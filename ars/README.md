# Access Request Service (ARS)

**ARS - тонкий HTTP-слой (фасад)** для обработки заявок на доступ.

## Архитектура

### ARS (Access Request Service)
- ✅ Принимает заявки (create/revoke)
- ✅ Хранит заявки и их статусы
- ✅ Отдает статусы заявок
- ✅ Отдает read-модели (права пользователя, заявки пользователя)
- ✅ Кладет задачи в очередь
- ❌ НЕ считает конфликты
- ❌ НЕ делает тяжелую бизнес-логику

### ARS Workers (CPU-bound слой)
- Забирает заявки из очереди RabbitMQ
- Синхронно ходит в Identity+Catalog Service
- Проверяет конфликты
- Принимает решение
- Обновляет статус заявки в ARS
- Триггерит выдачу/отзыв прав

### Identity+Catalog Service (source of truth)
- Хранит пользователей, группы прав, доступы, ресурсы, конфликты
- Отвечает на вопросы (какие группы у пользователя, какие доступы в группе, с чем конфликтует группа)
- Применяет изменения (выдать/отозвать)

## Запуск через Docker Compose

```bash
# Из корневой директории проекта
docker-compose up -d

# Или с логами
docker-compose up
```

Сервисы будут доступны:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management UI**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432

### Остановка

```bash
docker-compose down
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только API
docker-compose logs -f ars-api

# Только Worker
docker-compose logs -f ars-worker
```

### Масштабирование Worker'ов

Для увеличения количества worker'ов (для параллельной обработки заявок):

1. Уберите строку `container_name: ars_worker` у сервиса `ars-worker` в `docker-compose.yml`
2. Запустите с масштабированием:
   ```bash
   docker-compose up -d --scale ars-worker=3
   ```

## Локальная разработка

1. Убедитесь, что PostgreSQL и RabbitMQ запущены в Docker:
   ```bash
   docker-compose up -d postgres rabbitmq
   ```

2. Создайте `.env` файл из `env.example`:
   ```bash
   cp env.example .env
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Примените миграции:
   ```bash
   alembic upgrade head
   ```

5. Запустите API (в одном терминале):
   ```bash
   uvicorn app.main:app --reload
   ```

6. Запустите Worker (в другом терминале):
   ```bash
   python run_worker.py
   ```

## API Endpoints

- `POST /access-requests` - Создание заявки на доступ
- `GET /access-requests/{request_id}` - Получение статуса заявки
- `GET /access-requests/user/{user_id}` - Получение всех заявок пользователя
- `GET /access-requests/user/{user_id}/permissions` - Получение текущих прав пользователя (read-модель)

## Миграции

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```

## Структура проекта

```
ars/
├── app/
│   ├── api/              # API endpoints (тонкий HTTP-слой)
│   ├── core/             # Конфигурация, БД, RabbitMQ
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Сервисы (только сохранение и чтение)
│   ├── workers/          # Workers для обработки заявок (CPU-bound)
│   └── main.py           # FastAPI приложение
├── migrations/           # Alembic миграции
├── Dockerfile            # Docker образ
├── requirements.txt      # Python зависимости
└── run_worker.py         # Скрипт запуска worker
```

## Взаимодействие сервисов

### Синхронно (HTTP)
- User → ARS: создание заявки, получение статуса
- Worker → Identity+Catalog: получение прав, проверка конфликтов, выдача/отзыв прав

### Асинхронно (RabbitMQ)
- ARS → очередь: отправка заявки на обработку
- Очередь → Worker: получение заявки для обработки

