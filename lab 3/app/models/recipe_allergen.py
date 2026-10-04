from sqlalchemy import Column, ForeignKey, Table

from .base import Base


recipe_allergens = Table(
    "recipe_allergens",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True),
)
