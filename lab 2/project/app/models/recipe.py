from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .recipe_allergen import recipe_allergens


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cooking_time: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cuisine_id: Mapped[int] = mapped_column(
        ForeignKey("cuisines.id"),
        nullable=False,
    )

    cuisine: Mapped["Cuisine"] = relationship(back_populates="recipes")
    allergens: Mapped[list["Allergen"]] = relationship(
        secondary=recipe_allergens,
        back_populates="recipes",
    )
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
    )
