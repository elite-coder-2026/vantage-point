from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings as app_settings
from app.db import create_pool
from app.routers import auth, users, follows, groups, posts, hashtags, notify, pages, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount(
    app_settings.media_base_url,
    StaticFiles(directory=app_settings.media_storage_path, check_dir=False),
    name="media",
)
app.mount(
    app_settings.avatar_base_url,
    StaticFiles(directory=app_settings.avatar_storage_path, check_dir=False),
    name="avatars",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(follows.router)
app.include_router(groups.router)
app.include_router(posts.router)
app.include_router(hashtags.router)
app.include_router(notify.router)
app.include_router(pages.router)
app.include_router(settings.router)
