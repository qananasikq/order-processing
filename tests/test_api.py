import pytest


@pytest.mark.asyncio
async def test_create_order(client):
    response = await client.post(
        '/orders',
        json={
            'customer': 'user@example.com',
            'items': [{'name': 'book', 'price': 100, 'qty': 2}],
            'total': 200,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body['total'] == 200
    assert body['status'] == 'queued'
    assert body['tries'] == 0
    assert body['created_at']
    assert body['updated_at']


@pytest.mark.asyncio
async def test_create_order_rejects_empty_items(client):
    response = await client.post(
        '/orders',
        json={
            'customer': 'user@example.com',
            'items': [],
            'total': 200,
        },
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'order must contain at least one line'


@pytest.mark.asyncio
async def test_create_order_rejects_total_mismatch(client):
    response = await client.post(
        '/orders',
        json={
            'customer': 'user@example.com',
            'items': [{'name': 'book', 'price': 100, 'qty': 2}],
            'total': 199,
        },
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'declared total does not match line totals'


@pytest.mark.asyncio
async def test_get_missing_order(client):
    response = await client.get('/orders/999')
    assert response.status_code == 404
