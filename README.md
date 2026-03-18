# Intake Orders Service

[![FastAPI](https://img.shields.io/badge/FastAPI-green?style=flat-square)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)

Сервис стоит между приёмом заказа и складом.  
API принимает заказ, проверяет входные данные и кладёт его в очередь.  
Дальше worker забирает задачу и решает, что с ней делать.

## Как это работает

- заказ принимается и проверяется на входе
- позиции нормализуются и объединяются
- сумма пересчитывается
- заказ кладётся в очередь
- worker обрабатывает его отдельно

## Что происходит с заказом

### На входе

- пустой заказ не принимается
- одинаковые позиции объединяются
- у одной позиции не может быть разных цен
- total должен совпадать с расчётом

### В обработке

- `preorder-*` → отложенный retry
- `blocked-*` → сразу failed
- крупные или хрупкие → manual_review



## Статусы

- `queued`
- `processing`
- `done`
- `failed`
- `manual_review`

## Стек

- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy (async)
- Alembic

## Структура

```text
orders-service/
├── api/
│   ├── config.py
│   ├── db.py
│   ├── dto.py
│   ├── log.py
│   ├── main.py
│   ├── models.py
│   └── queue.py
├── logic/
│   ├── orders.py
│   └── worker.py
├── worker/
│   └── main.py
├── tests/
├── alembic/
└── docker-compose.yml
```

## Переменные окружения

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/orders
POSTGRES_USER=orders
POSTGRES_PASSWORD=changeme
POSTGRES_DB=orders

# Redis
REDIS_URL=redis://localhost:6379/0

# App
APP_ENV=dev
LOG_LEVEL=INFO
WORKER_CONCURRENCY=4
```

Подробнее в `.env.example`.

## Запуск

```powershell
docker-compose up --build
```

API доступен: http://localhost:8000  
Docs: http://localhost:8000/docs

### Health Check

```
GET /health → 200 OK
```

Сервис готов к работе, когда база и Redis подключены.

## Примеры

### Запрос

```json
{
  "customer": "ops@northwind.example",
  "items": [
    {"name": "book", "price": 100, "qty": 1},
    {"name": " book ", "price": 100, "qty": 2},
    {"name": "preorder-marker", "price": 40, "qty": 1}
  ],
  "total": 340
}
```

### Что произойдёт

1. API нормализует названия, схлопнет `book` в одну позицию (qty 3)
2. Пересчитает сумму до 300 + 40 = 340 → совпадает ✓
3. Положит заказ в очередь со статусом `queued`
4. Worker обнаружит `preorder-marker` и отложит заказ

### Ответ

```json
{
  "id": 12,
  "customer": "ops@northwind.example",
  "items": [
    {"name": "book", "price": 100.0, "qty": 3},
    {"name": "preorder-marker", "price": 40.0, "qty": 1}
  ],
  "total": 340.0,
  "status": "queued",
  "tries": 0,
  "created_at": "2026-03-18T09:15:00Z",
  "updated_at": "2026-03-18T09:15:00Z"
}
```

## Тесты

```powershell
pytest tests/
```

## Лицензия

MIT


