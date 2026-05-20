# API Overview

## Gateway

- `GET /health`
- `GET /services/health`
- `POST /auth/token`
- `POST /auth/verify`
- `POST /workflow/process-post`
- `POST /workflow/monitor-run`
- `GET /dashboard/overview`

## Collector service

- `GET /collector/sources`
- `POST /collector/raw`
- `POST /collector/collect`
- `GET /collector/raw`
- `GET /collector/raw/{post_id}`
- `GET /collector/stats`

## NLP service

- `POST /nlp/analyze`
- `POST /nlp/analyze/post`
- `POST /nlp/batch`
- `GET /nlp/sentiment/benchmark`
- `POST /nlp/bot-detection`
- `POST /nlp/virality`

## Analytics service

- `POST /analytics/ingest`
- `GET /analytics/overview`
- `GET /analytics/mentions/dynamics`
- `GET /analytics/authors/top`
- `GET /analytics/geo`
- `GET /analytics/wordcloud`
- `GET /analytics/sentiment`
- `GET /analytics/performance`

## Alert service

- `POST /alerts/check-spike`
- `POST /alerts/check-crisis`
- `POST /alerts/check-window`
- `GET /alerts/history`
- `GET /alerts/active`

## Competitor service

- `GET /competitors`
- `POST /competitors/update`
- `POST /competitors/sov`
- `GET /competitors/compare`

## Report service

- `POST /reports/dashboard/build`
- `GET /reports/history`
- `POST /reports/export`

## Notification service

- `POST /notify/send`
- `POST /notify/crisis`
- `GET /notify/history`
