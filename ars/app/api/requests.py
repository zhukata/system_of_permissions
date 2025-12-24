"""
API endpoints для работы с заявками на доступ.

ARS - тонкий HTTP-слой:
- Принимает заявки (create/revoke)
- Отдает статусы заявок
- Отдает read-модели (права пользователя, заявки пользователя)
- Кладет задачи в очередь (через сервисы)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.schemas.access_request import (
    AccessRequestCreate,
    AccessRequestResponse,
    UserPermissionsResponse,
)
from app.services.access_request import (
    create_access_request,
    get_access_request,
    get_user_requests,
)

router = APIRouter(prefix="/access-requests", tags=["access-requests"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=AccessRequestResponse, status_code=201)
def create_request(
    data: AccessRequestCreate,
    db: Session = Depends(get_db),
):
    """
    Создает заявку на выдачу или отзыв прав.
    
    Заявка сохраняется со статусом PENDING и отправляется в очередь.
    Worker обработает её асинхронно.
    """
    return create_access_request(db, data)


@router.get("/{request_id}", response_model=AccessRequestResponse)
def get_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Получает статус заявки по ID."""
    req = get_access_request(db, str(request_id))
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return req


@router.get("/user/{user_id}", response_model=list[AccessRequestResponse])
def get_user_requests_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Получает все заявки пользователя."""
    requests = get_user_requests(db, str(user_id))
    return requests


@router.get("/user/{user_id}/permissions", response_model=UserPermissionsResponse)
def get_user_permissions(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Получает текущие права пользователя (read-модель).
    
    TODO: Интеграция с Identity+Catalog Service для получения актуальных прав.
    Пока возвращает заглушку.
    """
    # TODO: HTTP запрос к Registry Service
    # GET {registry_service_url}/users/{user_id}/permissions
    return UserPermissionsResponse(
        user_id=user_id,
        permission_groups=[],
    )

