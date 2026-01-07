import json
import logging
import signal
import uuid
from typing import Optional, Any

import pika
from pika.adapters.blocking_connection import BlockingChannel
from sqlalchemy.orm import Session

from worker.app.core.config import settings
from worker.app.core.db import SessionLocal
from worker.app.core.rabbitmq import ACCESS_REQUEST_QUEUE
from common.enums import AccessAction
from common.models.access_request import AccessRequestStatus
from common.clients.registry_client import RegistryClient
from worker.app.services.requests import get_access_request, update_request_status


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class AccessRequestWorker:
    def __init__(self):
        self.registry = RegistryClient(settings.registry_service_url)
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self._stop_requested = False

    def _connect(self) -> None:
        """Установка соединения с RabbitMQ."""
        self.registry.close()
        self.registry = RegistryClient(settings.registry_service_url)

        params = pika.URLParameters(settings.rabbitmq_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        
        # Durable=True гарантирует сохранность очереди при перезагрузке RabbitMQ
        self.channel.queue_declare(queue=ACCESS_REQUEST_QUEUE, durable=True)
        # Prefetch=1 для равномерного распределения задач
        self.channel.basic_qos(prefetch_count=1)
        
        logger.info("Успешное подключение к RabbitMQ")

    def _update_status(self, db: Session, request_id: uuid.UUID, status: AccessRequestStatus, reason: Optional[str] = None):
        """Вспомогательный метод для обновления статуса в БД."""
        try:
            update_request_status(db, str(request_id), status, rejection_reason=reason)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка обновления статуса {request_id} на {status}: {e}")

    def _process_access_request(
        self,
        request: Any,
    ) -> tuple[bool, Optional[str]]:
        """
        Обрабатывает заявку на доступ:
        - проверяет конфликты
        - выполняет GRANT / REVOKE через Registry
        """

        if request.action is AccessAction.GRANT:
            current_groups = self.registry.get_user_permission_groups(
                request.user_id
            )
            group_ids = [g["id"] for g in current_groups]

            has_conflict, reason = self.registry.check_conflicts(
                group_ids,
                request.permission_group_id,
            )
            if has_conflict:
                return False, reason or "Конфликт прав доступа"

        try:
            if request.action is AccessAction.GRANT:
                self.registry.grant_permission_group(
                    request.user_id,
                    request.permission_group_id,
                )
            else:
                self.registry.revoke_permission_group(
                    request.user_id,
                    request.permission_group_id,
                )
        except Exception as e:
            logger.error(f"Ошибка Registry API: {e}")
            return False, "Ошибка внешней системы (Registry API)"

        return True, None


    def _on_message_callback(
        self,
        ch: BlockingChannel,
        method: Any,
        properties: Any,
        body: bytes,
    ):
        request_id_str = "unknown"

        try:
            payload = json.loads(body.decode("utf-8"))
            request_id = uuid.UUID(payload["request_id"])
            request_id_str = str(request_id)

            logger.info(f"[request_id={request_id_str}] получено сообщение")

            with SessionLocal() as db:
                request = get_access_request(db, request_id_str)

                if not request:
                    logger.warning(
                        f"[request_id={request_id_str}] заявка не найдена, ACK"
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                if request.status in (
                    AccessRequestStatus.APPROVED,
                    AccessRequestStatus.REJECTED,
                ):
                    logger.info(
                        f"[request_id={request_id_str}] заявка уже финализирована ({request.status}), пропуск"
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                self._update_status(
                    db,
                    request_id,
                    AccessRequestStatus.PROCESSING,
                )

                success, error_reason = self._process_access_request(request)

                if success:
                    self._update_status(
                        db,
                        request_id,
                        AccessRequestStatus.APPROVED,
                    )
                    logger.info(
                        f"[request_id={request_id_str}] заявка одобрена"
                    )
                else:
                    self._update_status(
                        db,
                        request_id,
                        AccessRequestStatus.REJECTED,
                        error_reason,
                    )
                    logger.info(
                        f"[request_id={request_id_str}] заявка отклонена: {error_reason}"
                    )

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError:
            logger.error("Некорректный JSON, сообщение отброшено")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.exception(
                f"[request_id={request_id_str}] ошибка обработки: {e}"
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


    def stop(self, *args):
        """Безопасная остановка."""
        logger.info("Завершение работы воркера...")
        self._stop_requested = True
        if self.connection and self.connection.is_open:
            self.connection.close()
        self.registry.close()

    def run(self):
        """Запуск цикла прослушивания."""
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        while not self._stop_requested:
            try:
                self._connect()
                self.channel.basic_consume(
                    queue=ACCESS_REQUEST_QUEUE, 
                    on_message_callback=self._on_message_callback
                )
                logger.info("Воркер запущен и ожидает задач...")
                self.channel.start_consuming()
            except pika.exceptions.AMQPConnectionError:
                if self._stop_requested:
                    break
                logger.error("Соединение с RabbitMQ разорвано. Повтор через 5 секунд...")
                import time
                time.sleep(5)
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка: {e}")
                break

if __name__ == "__main__":
    worker = AccessRequestWorker()
    worker.run()
