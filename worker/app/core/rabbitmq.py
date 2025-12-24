import json
import logging
from typing import Optional

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from app.core.config import settings

logger = logging.getLogger(__name__)

ACCESS_REQUEST_QUEUE = "access_request_created"


class RabbitMQPublisher:
    """Если понадобится публиковать события из worker (пока не используется)."""

    def __init__(self):
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

    def _ensure_connection(self):
        if self._connection is None or self._connection.is_closed:
            try:
                parameters = pika.URLParameters(settings.rabbitmq_url)
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                self._channel.queue_declare(queue=ACCESS_REQUEST_QUEUE, durable=True)
                logger.info("Подключение к RabbitMQ установлено")
            except (AMQPConnectionError, AMQPChannelError) as e:
                logger.error(f"Ошибка подключения к RabbitMQ: {e}")
                raise

    def publish(self, routing_key: str, message: dict):
        try:
            self._ensure_connection()
            self._channel.basic_publish(
                exchange="",
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except Exception as e:
            logger.error(f"Ошибка при публикации сообщения: {e}")
            raise

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()


