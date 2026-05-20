# SMM Radar

SMM Radar is a microservice platform for social media monitoring, sentiment analytics, trend detection, competitor analysis, and reporting.

## Mandatory coverage

- Supported sources: `VK`, `Telegram`, `YouTube`, `Twitter`, `Instagram`, `Facebook`, `Rutube`
- Data collection by keywords, hashtags, and geo filters
- Raw data storage (`collector-service`, MongoDB-ready architecture)
- Text processing: tokenization, lightweight lemmatization, sentiment, NER
- Analytics: mention dynamics, top authors, geo distribution, word cloud
- Alerts: mention spikes and crisis monitoring
- Reports: dashboard payloads + export (`JSON`, `PDF`, `Excel-compatible CSV`)
- Competitor module: comparison and share of voice (SOV)

## Services

- `api-gateway` - orchestration and unified API
- `collector-service` - social source connectors and raw post ingestion
- `nlp-service` - NLP analysis, bot detection, virality prediction
- `analytics-service` - aggregations and KPI metrics
- `alert-service` - spike and crisis detection
- `report-service` - dashboards and export
- `competitor-service` - competitor snapshots and SOV
- `notification-service` - delivery of operational notifications
- `frontend` - React + D3 analytics dashboard

## Optional improvements implemented

- Group A: fake account (bot) detection endpoint
- Group A: post virality prediction endpoint
- Group C: stream parallelization plan for high-volume processing
- Group C: cache layer for analytics responses
- Group D: interactive frontend widgets and visual charts

## Tech stack

- Backend: Python FastAPI
- Databases: PostgreSQL, MongoDB, Elasticsearch
- Queue: RabbitMQ
- Cache: Redis
- NLP: rule-based Russian/English tokenizer + sentiment baseline, extensible for Dostoevsky/RuBERT
- Frontend: React + D3.js

## Local run

```bash
cd 'your/project/folder'
docker compose up --build -d
```

## Useful URLs

- Frontend: `http://localhost:5183`
- Gateway health: `http://localhost:31051/health`
- Service health map: `http://localhost:31051/services/health`
- Gateway docs: `http://localhost:31051/docs`

## Demo workflow

```bash
python scripts/demo_pipeline.py
```

## Validation

```bash
python -m ruff check .
python -m pytest -q
docker compose config
```

## Sample data

Generate social media demo data:

```bash
python scripts/generate_sample_data.py
```

Output file: `data/samples/social_events.json`

## Quality targets

- Data refresh target: `< 15 min`
- Sentiment accuracy target: `> 85%`
- Throughput target architecture: `1,000,000 posts/day`
