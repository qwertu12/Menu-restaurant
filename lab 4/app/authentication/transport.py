from fastapi_users.authentication import BearerTransport

from config import settings


bearer_transport = BearerTransport(
    tokenUrl=settings.url.bearer_token_url,
)
