from typing import Annotated

from fastapi import Depends
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from models import AccessToken, db_helper


async def get_access_tokens_db(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
