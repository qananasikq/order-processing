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

```

orders-service/
├── api/
├── logic/
├── worker/
├── tests/
├── alembic/
└── docker-compose.yml

```

## Запуск

```

docker-compose up --build

```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Пример запроса

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

## Что произойдёт

* book объединится в одну позицию с qty 3
* сумма пересчитается
* заказ попадёт в очередь
* worker отправит его в delayed retry

## Пример ответа

```json
{
  "id": 12,
  "customer": "ops@northwind.example",
  "items": [
    {"name": "book", "price": 100.0, "qty": 3}
  ],
  "total": 300.0,
  "status": "queued",
  "tries": 0
}
```



