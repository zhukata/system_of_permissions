import json
import logging
import signal
import sys
import uuid
from typing import Optional, Any

import pika
from pika.adapters.blocking_connection import BlockingChannel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.rabbitmq import ACCESS_REQUEST_QUEUE
from app.models.access_request import AccessRequestStatus
from app.services.registry_client import RegistryClient
from app.services.requests import get_access_request, update_request_status


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class AccessRequestWorker:
    def __init__(self):
        self.registry = RegistryClient()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self._stop_requested = False

    def _connect(self) -> None:
        """Установка соединения с RabbitMQ."""
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

    def _process_business_logic(self, db: Session, request: Any) -> tuple[bool, Optional[str]]:
        """
        Ядро логики: проверка конфликтов и выполнение GRANT/REVOKE.
        Возвращает (успех, причина_отказа).
        """
        # 1. Проверка конфликтов (только для выдачи прав)
        if request.action.value == "GRANT":
            current_groups = self.registry.get_user_permission_groups(request.user_id)
            group_ids = [g.get("id") for g in current_groups]
            
            has_conflict, reason = self.registry.check_conflicts(group_ids, request.permission_group_id)
            if has_conflict:
                return False, reason or "Конфликт прав доступа"

        # 2. Выполнение действия
        if request.action.value == "GRANT":
            success = self.registry.grant_permission_group(request.user_id, request.permission_group_id)
        else:
            success = self.registry.revoke_permission_group(request.user_id, request.permission_group_id)
            
        return success, None if success else "Ошибка внешней системы (Registry API)"

    def _on_message_callback(self, ch: BlockingChannel, method: Any, properties: Any, body: bytes):
        """Обработка входящего сообщения из очереди."""
        request_id_str = "unknown"
        try:
            payload = json.loads(body.decode("utf-8"))
            request_id = uuid.UUID(payload["request_id"])
            request_id_str = str(request_id)
            
            logger.info(f"Начало обработки заявки: {request_id_str}")

            with SessionLocal() as db:
                request = get_access_request(db, request_id_str)
                if not request:
                    logger.warning(f"Заявка {request_id_str} не найдена в БД. Пропуск.")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                # Переводим в процесс
                self._update_status(db, request_id, AccessRequestStatus.PROCESSING)

                # Бизнес-логика
                success, error_reason = self._process_business_logic(db, request)

                if success:
                    self._update_status(db, request_id, AccessRequestStatus.APPROVED)
                    logger.info(f"Заявка {request_id_str} успешно одобрена")
                else:
                    self._update_status(db, request_id, AccessRequestStatus.REJECTED, error_reason)
                    logger.info(f"Заявка {request_id_str} отклонена: {error_reason}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError:
            logger.error("Некорректный формат JSON. Сообщение отброшено.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.exception(f"Критическая ошибка при обработке {request_id_str}: {e}")
            # Возвращаем в очередь для повторной попытки (requeue=True)
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
