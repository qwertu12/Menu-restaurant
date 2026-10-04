from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .recipe_allergen import recipe_allergens


class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(
        secondary=recipe_allergens,
        back_populates="allergens",
    )
