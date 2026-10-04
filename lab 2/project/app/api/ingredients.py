from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from config import settings
from models import Ingredient, Recipe, RecipeIngredient, db_helper
from .recipes import RecipeRead, serialize_recipe


router = APIRouter(tags=["Ingredients"], prefix=settings.url.ingredients)


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class IngredientUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


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


@router.get("/{id}/recipes", response_model=list[RecipeRead])
async def ingredient_recipes(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient with id {id} not found")

    stmt = (
        select(Recipe)
        .join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
        .where(RecipeIngredient.ingredient_id == id)
        .options(
            joinedload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient),
        )
        .order_by(Recipe.id)
    )
    result = await session.scalars(stmt)
    return [serialize_recipe(recipe) for recipe in result.unique().all()]
