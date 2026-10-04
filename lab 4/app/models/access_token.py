from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTable
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from .base import Base


class AccessToken(SQLAlchemyBaseAccessTokenTable[int], Base):
    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        )
