# Demo Script

1. Start stack:

```bash
docker compose up --build -d
```

2. Run one monitoring cycle:

```bash
python scripts/demo_pipeline.py
```

3. Open dashboard:

- `http://localhost:5183`

4. Validate quality endpoints:

- `GET /analytics/performance`
- `GET /nlp/sentiment/benchmark`
- `GET /alerts/active`
