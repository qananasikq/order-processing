````markdown
# Intake Orders Service

Сервис работает между приёмом заказа и складом. API принимает заказ, чистит входные данные, проверяет базовые вещи и кладёт задачу в очередь.
Дальше worker забирает заказ и решает, что с ним делать.

- отправить сразу в обработку;
- отложить и попробовать позже, если данные ещё не готовы;
- отправить в manual_review, если заказ выбивается из нормального потока;
- завершить в failed, если повторять смысла нет.

## Что есть в логике

- дубли позиций объединяются ещё на входе;
- сумма пересчитывается и сверяется с запросом;
- крупные и хрупкие заказы не идут в автопоток;
- retry делается через отложенную очередь в Redis;
- обработка завязана на конкретный intake, а не просто фоновые задачи.

## Статусы заказа

- `queued` заказ принят и ждёт обработки  
- `processing` заказ взят в работу  
- `done` обработка прошла успешно  
- `failed` заказ не удалось обработать  
- `manual_review` требуется ручная проверка  

## Логика обработки

### API

- пустой заказ не принимается  
- одинаковые позиции объединяются  
- одна позиция не может иметь разные цены  
- слишком раздробленные заказы отсекаются  
- total должен совпадать с пересчитанной суммой  

### Worker

- `preorder-*` отправляется в отложенный retry  
- `blocked-*` сразу уходит в failed  
- крупные или хрупкие заказы идут в manual_review  

## Стек

- FastAPI  
- PostgreSQL  
- Redis (очередь, retry, блокировки)  
- SQLAlchemy async  
- Alembic  

RabbitMQ не используется, Redis закрывает задачу без лишней инфраструктуры.

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
````

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

1. позиции `book` объединятся в одну с qty 3
2. сумма пересчитается
3. заказ попадёт в очередь `orders:ready`
4. worker отправит заказ в delayed retry из-за `preorder-marker`

## Запуск

```bash
docker-compose up --build
```

* API: [http://localhost:8000](http://localhost:8000)
* Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

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
  "tries": 0,
  "error": null,
  "created_at": "2026-03-18T09:15:00Z",
  "updated_at": "2026-03-18T09:15:00Z"
}
```
