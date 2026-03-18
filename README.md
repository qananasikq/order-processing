# Intake Orders Service

[![FastAPI](https://img.shields.io/badge/FastAPI-green?style=flat-square)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)

Микросервис для приёма и обработки заказов. Валидирует входные данные, объединяет дубли позиций, кладёт в очередь Redis. Воркер обрабатывает асинхронно в зависимости от типа заказа.

## Как это работает

1. API проверяет заказ - сумма, позиции, дубли
2. Объединяет одинаковые позиции
3. Кладёт заказ в очередь
4. Воркер достаёт и обрабатывает


## Проверки при приёме

- Заказ не должен быть пустой
- Одинаковые позиции объединяются в одну (qty суммируется)
- У одной позиции не может быть разных цен
- Сумма должна совпадать с указанной total

## Обработка воркером

Некоторые правила сделаны упрощённо:

- если в названии есть `preorder-*` — заказ откладывается и пробуется позже
- `blocked-*` — сразу уходит в failed
- большие заказы или расхождения по сумме — manual_review

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
├── api        # ручки
├── logic      # бизнес логика
├── worker     # обработка
├── tests
├── alembic
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

* две позиции `book` объединятся в одну (qty 3)
* сумма: 300 + 40 = 340 ✓
* заказ попадёт в очередь
* воркер увидит `preorder-marker` и отложит обработку


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



