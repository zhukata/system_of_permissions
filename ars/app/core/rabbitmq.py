"""
RabbitMQ Publisher для отправки задач в очередь.

ARS отправляет события в очередь, Worker'ы их обрабатывают.
"""
import json
import logging
from typing import Optional

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Название очереди для заявок на доступ
ACCESS_REQUEST_QUEUE = "access_request_created"


class RabbitMQPublisher:
    """Класс для публикации событий в RabbitMQ."""

    def __init__(self):
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

    def _ensure_connection(self):
        """Устанавливает соединение с RabbitMQ, если оно не установлено."""
        if self._connection is None or self._connection.is_closed:
            try:
                parameters = pika.URLParameters(settings.rabbitmq_url)
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                # Объявляем очередь (idempотентная операция)
                self._channel.queue_declare(queue=ACCESS_REQUEST_QUEUE, durable=True)
                logger.info("Подключение к RabbitMQ установлено")
            except (AMQPConnectionError, AMQPChannelError) as e:
                logger.error(f"Ошибка подключения к RabbitMQ: {e}")
                raise

    def publish_access_request_created(
        self, request_id: str, user_id: str, permission_group_id: str, action: str
    ):
        """
        Публикует событие о создании заявки на доступ.
        
        Worker'ы подхватят это событие и обработают заявку.
        
        Args:
            request_id: UUID заявки
            user_id: UUID пользователя
            permission_group_id: UUID группы прав
            action: Действие (GRANT/REVOKE)
        """
        try:
            self._ensure_connection()
            
            message = {
                "request_id": request_id,
                "user_id": user_id,
                "permission_group_id": permission_group_id,
                "action": action,
            }
            
            self._channel.basic_publish(
                exchange="",
                routing_key=ACCESS_REQUEST_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Сохранять сообщения на диск
                ),
            )
            logger.info(f"Событие access_request_created опубликовано: {request_id}")
        except Exception as e:
            logger.error(f"Ошибка при публикации события: {e}")
            raise

    def close(self):
        """Закрывает соединение с RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("Соединение с RabbitMQ закрыто")


# Глобальный экземпляр publisher (singleton)
_publisher: Optional[RabbitMQPublisher] = None


def get_publisher() -> RabbitMQPublisher:
    """Возвращает глобальный экземпляр RabbitMQ publisher."""
    global _publisher
    if _publisher is None:
        _publisher = RabbitMQPublisher()
    return _publisher

