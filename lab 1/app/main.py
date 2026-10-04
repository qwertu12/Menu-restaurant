import uvicorn
from fastapi import FastAPI
from config import settings
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from models import db_helper, Base
from api import router as api_router

APP_DIR = Path(__file__).resolve().parent

STATIC_DIR = APP_DIR / "static"

STATIC_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # shutdown
    await db_helper.dispose()


main_app = FastAPI(
    lifespan=lifespan,
)
main_app.include_router(
    api_router,
)

main_app.mount(
    "/static",
    StaticFiles(
        directory=str(STATIC_DIR)
    ),
    name="static",
)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
