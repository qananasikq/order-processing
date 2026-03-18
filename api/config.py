import os


class Settings:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL') or 'postgresql+asyncpg://app:app@localhost:5432/orders'
        self.redis_url = os.getenv('REDIS_URL') or 'redis://localhost:6379/0'
        self.ready_queue_name = os.getenv('READY_QUEUE_NAME') or 'orders:ready'
        self.delayed_queue_name = os.getenv('DELAYED_QUEUE_NAME') or 'orders:delayed'
        self.lock_ttl_seconds = int(os.getenv('LOCK_TTL_SECONDS') or '30')
        self.retry_delay_seconds = int(os.getenv('RETRY_DELAY_SECONDS') or '20')
        self.max_retries = int(os.getenv('MAX_RETRIES') or '3')


settings = Settings()
