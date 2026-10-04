from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Recipe, db_helper



router = APIRouter(
    tags=["Recipes"],
    prefix=settings.url.recipes,
)


class RecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    cooking_time: int
    difficulty: int


class RecipeCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        min_length=1,
        max_length=5000,
    )

    cooking_time: int = Field(
        gt=0,
    )

    difficulty: int = Field(
        ge=1,
        le=5,
    )


class RecipeUpdate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        min_length=1,
        max_length=5000,
    )

    cooking_time: int = Field(
        gt=0,
    )

    difficulty: int = Field(
        ge=1,
        le=5,
    )


@router.get("", response_model=list[RecipeRead])
async def recipe_index(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = select(Recipe).order_by(Recipe.id)

    recipes = await session.scalars(stmt)

    return recipes.all()


@router.post(
    "",
    response_model=RecipeRead,
    status_code=status.HTTP_201_CREATED,
)
async def recipe_store(
    recipe_create: RecipeCreate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    recipe = Recipe(
        **recipe_create.model_dump()
    )

    session.add(recipe)

    await session.commit()
    await session.refresh(recipe)

    return recipe


@router.get(
    "/{id}",
    response_model=RecipeRead,
)
async def recipe_show(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    recipe = await session.get(
        Recipe,
        id,
    )

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found",
        )

    return recipe


@router.put(
    "/{id}",
    response_model=RecipeRead,
)
async def recipe_update(
    id: int,
    recipe_update: RecipeUpdate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    recipe = await session.get(
        Recipe,
        id,
    )

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found",
        )

    for field, value in recipe_update.model_dump().items():
        setattr(recipe, field, value)

    await session.commit()
    await session.refresh(recipe)

    return recipe


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def recipe_destroy(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    recipe = await session.get(
        Recipe,
        id,
    )

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found",
        )

    await session.delete(recipe)
    await session.commit()