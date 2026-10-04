from fastapi_users.authentication import JWTStrategy

from config import settings


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.access_token.jwt_secret,
        lifetime_seconds=settings.access_token.lifetime_seconds,
    )
