from fastapi import APIRouter

from authentication.fastapi_users import fastapi_users
from authentication.schemas.user import UserRead, UserUpdate
from config import settings


router = APIRouter(
    prefix=settings.url.users,
    tags=["Users"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
)
