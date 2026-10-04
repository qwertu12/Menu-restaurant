from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Cuisine, db_helper


router = APIRouter(tags=["Cuisines"], prefix=settings.url.cuisines)


class CuisineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CuisineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CuisineUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


@router.get("", response_model=list[CuisineRead])
async def cuisine_index(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    result = await session.scalars(select(Cuisine).order_by(Cuisine.id))
    return result.all()


@router.get("/{id}", response_model=CuisineRead)
async def cuisine_show(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(status_code=404, detail=f"Cuisine with id {id} not found")
    return cuisine


@router.post("", response_model=CuisineRead, status_code=status.HTTP_201_CREATED)
async def cuisine_store(
    cuisine_create: CuisineCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    cuisine = Cuisine(name=cuisine_create.name)
    session.add(cuisine)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Cuisine name must be unique")
    await session.refresh(cuisine)
    return cuisine


@router.put("/{id}", response_model=CuisineRead)
async def cuisine_update(
    id: int,
    cuisine_update: CuisineUpdate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(status_code=404, detail=f"Cuisine with id {id} not found")
    cuisine.name = cuisine_update.name
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Cuisine name must be unique")
    await session.refresh(cuisine)
    return cuisine


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def cuisine_destroy(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(status_code=404, detail=f"Cuisine with id {id} not found")
    try:
        await session.delete(cuisine)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Cuisine is used by recipes")
