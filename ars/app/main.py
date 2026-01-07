from fastapi import FastAPI

from ars.app.api.requests import router as access_requests_router
from ars.app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(access_requests_router)
