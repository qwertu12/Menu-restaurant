from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_filter import FilterDepends
from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from config import settings
from models import (
    Allergen,
    Cuisine,
    Ingredient,
    MeasurementEnum,
    Recipe,
    RecipeIngredient,
    db_helper,
)


router = APIRouter(tags=["Recipes"], prefix=settings.url.recipes)


class CuisineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AllergenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class RecipeIngredientRead(BaseModel):
    id: int
    quantity: float
    measurement: int
    name: str


class RecipeRead(BaseModel):
    id: int
    title: str
    description: str
    cooking_time: int
    difficulty: int
    cuisine: CuisineRead
    allergens: list[AllergenRead]
    ingredients: list[RecipeIngredientRead]


class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    measurement: MeasurementEnum


class RecipeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=5000)
    cooking_time: int = Field(gt=0)
    difficulty: int = Field(ge=1, le=5)
    cuisine_id: int
    allergen_ids: list[int] = Field(default_factory=list)
    ingredients: list[RecipeIngredientCreate] = Field(default_factory=list)


class RecipeUpdate(RecipeCreate):
    pass


class RecipeFilter(Filter):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    title__like: str | None = Field(
        default=None,
        alias="name__like",
    )

    ingredient_id__in: list[int] | None = Field(
        default=None,
        alias="ingredient_id",
    )

    recipe_sort: list[str] = Field(
        default_factory=lambda: ["-id"],
        alias="sort",
    )

    class Constants(Filter.Constants):
        model = Recipe
        ordering_field_name = "recipe_sort"

    @field_validator("recipe_sort")
    @classmethod
    def validate_recipe_sort(cls, value):
        allowed = {
            "id",
            "difficulty",
        }

        for field_name in value or []:
            normalized = (
                field_name
                .removeprefix("-")
                .removeprefix("+")
            )

            if normalized not in allowed:
                raise ValueError(
                    "sort supports only id and difficulty"
                )

        return value

    def filter(self, query):
        base_filter = RecipeFilter(
            title__like=self.title__like,
            ingredient_id__in=None,
            recipe_sort=self.recipe_sort,
        )

        query = Filter.filter(
            base_filter,
            query,
        )

        if self.ingredient_id__in:
            recipe_ids = (
                select(RecipeIngredient.recipe_id)
                .where(
                    RecipeIngredient.ingredient_id.in_(
                        self.ingredient_id__in
                    )
                )
            )

            query = query.where(
                Recipe.id.in_(recipe_ids)
            )

        return query


def recipe_options():
    return (
        joinedload(Recipe.cuisine),
        selectinload(Recipe.allergens),
        selectinload(
            Recipe.recipe_ingredients
        ).joinedload(
            RecipeIngredient.ingredient
        ),
    )


def serialize_recipe(
    recipe: Recipe,
) -> RecipeRead:
    return RecipeRead(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        cooking_time=recipe.cooking_time,
        difficulty=recipe.difficulty,
        cuisine=CuisineRead.model_validate(
            recipe.cuisine
        ),
        allergens=[
            AllergenRead.model_validate(
                allergen
            )
            for allergen in recipe.allergens
        ],
        ingredients=[
            RecipeIngredientRead(
                id=item.ingredient.id,
                quantity=item.quantity,
                measurement=int(
                    item.measurement
                ),
                name=item.ingredient.name,
            )
            for item in recipe.recipe_ingredients
        ],
    )


def serialize_recipes(
    recipes: Sequence[Recipe],
) -> list[RecipeRead]:
    return [
        serialize_recipe(recipe)
        for recipe in recipes
    ]


async def get_recipe(
    session: AsyncSession,
    recipe_id: int,
) -> Recipe | None:
    stmt = (
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(*recipe_options())
    )

    return await session.scalar(stmt)


async def get_allergens(
    session: AsyncSession,
    ids: list[int],
) -> list[Allergen]:
    if not ids:
        return []

    unique_ids = set(ids)

    result = await session.scalars(
        select(Allergen).where(
            Allergen.id.in_(unique_ids)
        )
    )

    allergens = list(
        result.all()
    )

    found_ids = {
        item.id
        for item in allergens
    }

    missing_ids = (
        unique_ids - found_ids
    )

    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=(
                "Allergens not found: "
                f"{sorted(missing_ids)}"
            ),
        )

    return allergens


async def get_ingredients(
    session: AsyncSession,
    ids: set[int],
) -> dict[int, Ingredient]:
    if not ids:
        return {}

    result = await session.scalars(
        select(Ingredient).where(
            Ingredient.id.in_(ids)
        )
    )

    ingredients = {
        item.id: item
        for item in result.all()
    }

    missing_ids = (
        ids - set(ingredients)
    )

    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=(
                "Ingredients not found: "
                f"{sorted(missing_ids)}"
            ),
        )

    return ingredients


@router.get(
    "",
    response_model=Page[RecipeRead],
)
async def recipe_index(
    recipe_filter: Annotated[
        RecipeFilter,
        FilterDepends(
            RecipeFilter,
            by_alias=True,
        ),
    ],
    session: Annotated[
        AsyncSession,
        Depends(
            db_helper.session_getter
        ),
    ],
):
    stmt = select(Recipe).options(*recipe_options())

    stmt = recipe_filter.filter(stmt)

    stmt = recipe_filter.sort(stmt)

    return await apaginate(
        session,
        stmt,
        transformer=serialize_recipes,
    )


@router.post(
    "",
    response_model=RecipeRead,
    status_code=status.HTTP_201_CREATED,
)
async def recipe_store(
    recipe_create: RecipeCreate,
    session: Annotated[
        AsyncSession,
        Depends(
            db_helper.session_getter
        ),
    ],
):
    cuisine = await session.get(
        Cuisine,
        recipe_create.cuisine_id,
    )

    if not cuisine:
        raise HTTPException(
            status_code=404,
            detail=(
                "Cuisine with id "
                f"{recipe_create.cuisine_id} "
                "not found"
            ),
        )

    allergens = await get_allergens(
        session,
        recipe_create.allergen_ids,
    )

    ingredient_ids = {
        item.ingredient_id
        for item in recipe_create.ingredients
    }

    ingredients = await get_ingredients(
        session,
        ingredient_ids,
    )

    recipe = Recipe(
        title=recipe_create.title,
        description=recipe_create.description,
        cooking_time=recipe_create.cooking_time,
        difficulty=recipe_create.difficulty,
        cuisine=cuisine,
        allergens=allergens,
    )

    session.add(recipe)

    for item in recipe_create.ingredients:
        session.add(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredients[
                    item.ingredient_id
                ],
                quantity=item.quantity,
                measurement=item.measurement,
            )
        )

    await session.commit()

    recipe = await get_recipe(
        session,
        recipe.id,
    )

    return serialize_recipe(recipe)


@router.get(
    "/{id}",
    response_model=RecipeRead,
)
async def recipe_show(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(
            db_helper.session_getter
        ),
    ],
):
    recipe = await get_recipe(
        session,
        id,
    )

    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Recipe with id {id} "
                "not found"
            ),
        )

    return serialize_recipe(recipe)


@router.put(
    "/{id}",
    response_model=RecipeRead,
)
async def recipe_update(
    id: int,
    recipe_update: RecipeUpdate,
    session: Annotated[
        AsyncSession,
        Depends(
            db_helper.session_getter
        ),
    ],
):
    recipe = await get_recipe(
        session,
        id,
    )

    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Recipe with id {id} "
                "not found"
            ),
        )

    cuisine = await session.get(
        Cuisine,
        recipe_update.cuisine_id,
    )

    if not cuisine:
        raise HTTPException(
            status_code=404,
            detail=(
                "Cuisine with id "
                f"{recipe_update.cuisine_id} "
                "not found"
            ),
        )

    allergens = await get_allergens(
        session,
        recipe_update.allergen_ids,
    )

    ingredient_ids = {
        item.ingredient_id
        for item in recipe_update.ingredients
    }

    ingredients = await get_ingredients(
        session,
        ingredient_ids,
    )

    recipe.title = (
        recipe_update.title
    )

    recipe.description = (
        recipe_update.description
    )

    recipe.cooking_time = (
        recipe_update.cooking_time
    )

    recipe.difficulty = (
        recipe_update.difficulty
    )

    recipe.cuisine = cuisine

    recipe.allergens = allergens

    recipe.recipe_ingredients = [
        RecipeIngredient(
            ingredient=ingredients[
                item.ingredient_id
            ],
            quantity=item.quantity,
            measurement=item.measurement,
        )
        for item in recipe_update.ingredients
    ]

    await session.commit()

    recipe = await get_recipe(
        session,
        id,
    )

    return serialize_recipe(recipe)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def recipe_destroy(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(
            db_helper.session_getter
        ),
    ],
):
    recipe = await session.get(
        Recipe,
        id,
    )

    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Recipe with id {id} "
                "not found"
            ),
        )

    await session.delete(recipe)

    await session.commit()