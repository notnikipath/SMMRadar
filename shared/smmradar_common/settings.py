from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "smmradar-service"
    service_port: int = 8500
    environment: str = "dev"

    postgres_dsn: str = "postgresql+psycopg://smmradar:smmradar@postgres:5432/smmradar"
    mongodb_dsn: str = "mongodb://mongodb:27017"
    elasticsearch_url: str = "http://elasticsearch:9200"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = "smmradar-dev-secret"
    encryption_key: str = "smmradar-dev-encryption-key"

    refresh_target_minutes: int = 15
    sentiment_accuracy_target_pct: float = 85.0
    throughput_target_posts_per_day: int = 1_000_000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
