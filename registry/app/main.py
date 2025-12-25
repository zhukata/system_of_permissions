from fastapi import FastAPI

from app.core.config import settings
from app.core.db import engine
from app.models import Base
from app.api import admin, internal

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(admin.router)
app.include_router(internal.router)
