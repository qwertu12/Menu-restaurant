from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from models import Ingredient, Recipe, RecipeIngredient, db_helper


router = APIRouter(tags=["Ingredients"], prefix=settings.url.ingredients)


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class IngredientUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


BASE_RECIPE_FIELDS = {"id", "name", "difficulty", "description", "cooking_time"}
INCLUDE_VALUES = {"cuisine", "ingredients", "allergens"}


def parse_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def validate_values(values: set[str], allowed: set[str], parameter: str) -> None:
    invalid = values - allowed
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported {parameter}: {', '.join(sorted(invalid))}",
        )


def shape_recipe(recipe: Recipe, selected: set[str], includes: set[str]) -> dict[str, Any]:
    values = {
        "id": recipe.id,
        "name": recipe.title,
        "difficulty": recipe.difficulty,
        "description": recipe.description,
        "cooking_time": recipe.cooking_time,
    }
    data = {field: values[field] for field in values if field in selected}

    if "cuisine" in includes:
        data["cuisine"] = {
            "id": recipe.cuisine.id,
            "name": recipe.cuisine.name,
        }

    if "allergens" in includes:
        data["allergens"] = [
            {
                "id": allergen.id,
                "name": allergen.name,
            }
            for allergen in recipe.allergens
        ]

    if "ingredients" in includes:
        data["ingredients"] = [
            {
                "id": item.ingredient.id,
                "name": item.ingredient.name,
                "quantity": item.quantity,
                "measurement": int(item.measurement),
            }
            for item in recipe.recipe_ingredients
        ]

    return data


@router.get("", response_model=list[IngredientRead])
async def ingredient_index(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    result = await session.scalars(select(Ingredient).order_by(Ingredient.id))
    return result.all()


@router.get("/{id}", response_model=IngredientRead)
async def ingredient_show(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient with id {id} not found")
    return ingredient


@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
async def ingredient_store(
    ingredient_create: IngredientCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    ingredient = Ingredient(name=ingredient_create.name)
    session.add(ingredient)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Ingredient name must be unique")
    await session.refresh(ingredient)
    return ingredient


@router.put("/{id}", response_model=IngredientRead)
async def ingredient_update(
    id: int,
    ingredient_update: IngredientUpdate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient with id {id} not found")
    ingredient.name = ingredient_update.name
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Ingredient name must be unique")
    await session.refresh(ingredient)
    return ingredient


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def ingredient_destroy(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient with id {id} not found")
    try:
        await session.delete(ingredient)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Ingredient is used by recipes")


@router.get("/{id}/recipes")
async def ingredient_recipes(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    include: Annotated[str | None, Query()] = None,
    select_fields: Annotated[str | None, Query(alias="select")] = None,
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient with id {id} not found")

    includes = parse_csv(include)
    selected = parse_csv(select_fields) or BASE_RECIPE_FIELDS
    validate_values(includes, INCLUDE_VALUES, "include")
    validate_values(selected, BASE_RECIPE_FIELDS, "select")

    options = []
    if "cuisine" in includes:
        options.append(selectinload(Recipe.cuisine))
    if "allergens" in includes:
        options.append(selectinload(Recipe.allergens))
    if "ingredients" in includes:
        options.append(
            selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient)
        )

    stmt = (
        select(Recipe)
        .join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
        .where(RecipeIngredient.ingredient_id == id)
        .order_by(Recipe.id)
    )
    if options:
        stmt = stmt.options(*options)

    result = await session.scalars(stmt)
    recipes = result.unique().all()
    return [shape_recipe(recipe, selected, includes) for recipe in recipes]
