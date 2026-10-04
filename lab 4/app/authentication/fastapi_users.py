from fastapi_users import FastAPIUsers

from models import User

from .backend import authentication_backend
from .helper.user_manager import get_user_manager


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [authentication_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_active_superuser = fastapi_users.current_user(active=True, superuser=True)
