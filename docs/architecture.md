# Architecture

## Context

SMM Radar provides end-to-end social media monitoring for brand mentions and reputation control.

## Service map

- `api-gateway`: auth, workflow orchestration, and unified dashboard API
- `collector-service`: social API connectors (mock-ready), keyword/hashtag/geo collection, raw post storage
- `nlp-service`: tokenization, lemmatization, sentiment, NER, bot and virality scoring
- `analytics-service`: mention dynamics, top authors, geo distribution, word cloud, KPI aggregation
- `alert-service`: mention spike detection and crisis monitoring
- `report-service`: dashboard payload preparation and export formats
- `competitor-service`: competitor snapshots and share-of-voice calculations
- `notification-service`: operational notifications for incidents and trends
- `frontend`: React + D3 interface for analysts and managers

## Infrastructure

- PostgreSQL: analytical metadata and structured reporting state
- MongoDB: raw post storage target
- Elasticsearch: search index target for fast text queries
- RabbitMQ: event transport between collection and processing
- Redis: cache for hot analytical queries
- Docker Compose: local environment and dependency wiring

## Core workflow

1. Collect posts by source and filters (`collector-service`)
2. Analyze text (`nlp-service`)
3. Persist aggregate metrics (`analytics-service`)
4. Trigger alert checks (`alert-service`)
5. Notify teams (`notification-service`)
6. Build dashboard and exportable reports (`report-service`)
7. Compare brand with competitors (`competitor-service`)

## Scalability notes

- Stateless services are horizontally scalable
- Analytics responses are cached for low-latency reads
- Stream processing plan is exposed for high-volume ingestion
- Platform sharding strategy is supported in shared logic
