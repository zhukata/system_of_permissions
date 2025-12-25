from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.db import engine
from app.models import Base
from app.api import admin, internal


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield



app = FastAPI(
    title="Registry service",
    lifespan=lifespan,
)

app.include_router(admin.router)
app.include_router(internal.router)
