from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import create_pool
from app.routers import auth, users, follows, groups, posts, hashtags


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(follows.router)
app.include_router(groups.router)
app.include_router(posts.router)
app.include_router(hashtags.router)
