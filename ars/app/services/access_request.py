"""
Сервисы для работы с заявками на доступ.

ARS - тонкий слой: только сохранение, чтение и отправка в очередь.
Вся бизнес-логика (конфликты, проверки) - в Worker'ах.
"""
import logging
from sqlalchemy.orm import Session

from app.core.rabbitmq import get_publisher
from app.models.access_request import AccessRequest
from app.schemas.access_request import AccessRequestCreate

logger = logging.getLogger(__name__)


def create_access_request(db: Session, data: AccessRequestCreate) -> AccessRequest:
    """
    Создает заявку и отправляет её в очередь для обработки.
    
    ARS не проверяет конфликты - это делает Worker.
    """
    req = AccessRequest(
        user_id=data.user_id,
        permission_group_id=data.permission_group_id,
        action=data.action,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    
    # Отправляем заявку в очередь для обработки Worker'ом
    try:
        publisher = get_publisher()
        publisher.publish_access_request_created(
            request_id=str(req.id),
            user_id=str(req.user_id),
            permission_group_id=str(req.permission_group_id),
            action=req.action.value,
        )
        logger.info(f"Заявка {req.id} создана и отправлена в очередь")
    except Exception as e:
        logger.error(f"Не удалось отправить заявку {req.id} в очередь: {e}")
        # Не прерываем выполнение - заявка уже создана, Worker может обработать позже
    
    return req


def get_access_request(db: Session, request_id: str) -> AccessRequest | None:
    """Получает заявку по ID."""
    return db.query(AccessRequest).filter(AccessRequest.id == request_id).one_or_none()


def get_user_requests(db: Session, user_id: str) -> list[AccessRequest]:
    """Получает все заявки пользователя."""
    return db.query(AccessRequest).filter(AccessRequest.user_id == user_id).all()


def update_request_status(
    db: Session, request_id: str, status: str, rejection_reason: str | None = None
) -> AccessRequest:
    """
    Обновляет статус заявки.
    
    Используется Worker'ом для обновления статуса после обработки.
    """
    from app.models.access_request import AccessRequestStatus
    
    req = get_access_request(db, request_id)
    if not req:
        raise ValueError(f"Заявка {request_id} не найдена")
    
    req.status = AccessRequestStatus(status)
    if rejection_reason:
        req.rejection_reason = rejection_reason
    
    db.commit()
    db.refresh(req)
    
    logger.info(f"Статус заявки {request_id} обновлен на {status}")
    return req

