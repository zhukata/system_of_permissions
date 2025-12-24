from fastapi import FastAPI

from app.api.requests import router as access_requests_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(access_requests_router)

