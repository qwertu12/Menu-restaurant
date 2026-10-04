from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Allergen, db_helper


router = APIRouter(tags=["Allergens"], prefix=settings.url.allergens)


class AllergenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AllergenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class AllergenUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


@router.get("", response_model=list[AllergenRead])
async def allergen_index(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    result = await session.scalars(select(Allergen).order_by(Allergen.id))
    return result.all()


@router.get("/{id}", response_model=AllergenRead)
async def allergen_show(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(status_code=404, detail=f"Allergen with id {id} not found")
    return allergen


@router.post("", response_model=AllergenRead, status_code=status.HTTP_201_CREATED)
async def allergen_store(
    allergen_create: AllergenCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    allergen = Allergen(name=allergen_create.name)
    session.add(allergen)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Allergen name must be unique")
    await session.refresh(allergen)
    return allergen


@router.put("/{id}", response_model=AllergenRead)
async def allergen_update(
    id: int,
    allergen_update: AllergenUpdate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(status_code=404, detail=f"Allergen with id {id} not found")
    allergen.name = allergen_update.name
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Allergen name must be unique")
    await session.refresh(allergen)
    return allergen


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def allergen_destroy(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(status_code=404, detail=f"Allergen with id {id} not found")
    await session.delete(allergen)
    await session.commit()
