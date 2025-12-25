import logging

from sqlalchemy.orm import Session

from common.models.access_request import AccessRequest, AccessRequestStatus

logger = logging.getLogger(__name__)


def get_access_request(db: Session, request_id: str) -> AccessRequest | None:
    return db.query(AccessRequest).filter(AccessRequest.id == request_id).one_or_none()


def update_request_status(
    db: Session,
    request_id: str,
    status: AccessRequestStatus,
    rejection_reason: str | None = None,
) -> AccessRequest:
    req = get_access_request(db, request_id)
    if not req:
        raise ValueError(f"Заявка {request_id} не найдена")

    req.status = status
    if rejection_reason:
        req.rejection_reason = rejection_reason

    logger.info(f"Статус заявки {request_id} обновлен на {status}")
    return req
