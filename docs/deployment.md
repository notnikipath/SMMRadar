# Deployment

## Local environment

1. Configure `.env` from `.env.example`
2. Build and run stack:

```bash
docker compose up --build -d
```

3. Check health:

```bash
curl http://localhost:8580/services/health
```

## Runtime ports

- Gateway: `8580`
- Frontend: `5183`
- PostgreSQL: `55440`
- MongoDB: `27028`
- Elasticsearch: `9208`
- RabbitMQ UI: `15678`
- Redis: `6388`

## CI checks

```bash
python -m ruff check .
python -m pytest -q
docker compose config
```
