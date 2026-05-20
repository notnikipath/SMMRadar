from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI

from shared.smmradar_common import (
    AnalyticsIngestRequest,
    Settings,
    TTLCache,
    crisis_probability,
    geo_distribution,
    mention_dynamics,
    top_authors,
    word_cloud,
)

settings = Settings(service_name="analytics-service", service_port=8503)
app = FastAPI(title="SMM Radar Analytics Service", version="1.0.0")

records: list[AnalyticsIngestRequest] = []
cache = TTLCache(ttl_seconds=120)


def _posts() -> list[Any]:
    return [record.post for record in records]


def _sentiment_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        counts[record.nlp.sentiment.label.value] += 1
    return counts


def _summary() -> dict[str, Any]:
    posts = _posts()
    sentiments = _sentiment_counts()
    negative_mentions = sentiments.get("negative", 0)
    total_mentions = len(posts)
    severe_alerts = sum(1 for record in records if record.nlp.sentiment.score < -0.5)
    by_platform: Counter[str] = Counter(post.platform.value for post in posts)
    return {
        "total_mentions": total_mentions,
        "platforms": dict(by_platform),
        "sentiments": dict(sentiments),
        "negative_ratio": round(negative_mentions / max(total_mentions, 1), 3),
        "crisis_probability": crisis_probability(negative_mentions, total_mentions, severe_alerts),
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/analytics/ingest")
async def ingest(request: AnalyticsIngestRequest) -> dict[str, object]:
    records.append(request)
    cache.set("overview", _summary())
    return {
        "status": "accepted",
        "post_id": request.post.post_id,
        "ingested_at": datetime.now(UTC).isoformat(),
    }


@app.get("/analytics/overview")
async def overview() -> dict[str, object]:
    cached = cache.get("overview")
    if cached is not None:
        return {"cached": True, "summary": cached}
    summary = _summary()
    cache.set("overview", summary)
    return {"cached": False, "summary": summary}


@app.get("/analytics/mentions/dynamics")
async def dynamics(hours: int = 24) -> dict[str, object]:
    points = mention_dynamics(_posts(), hours=max(1, min(hours, 168)))
    return {"hours": hours, "count": len(points), "items": points}


@app.get("/analytics/authors/top")
async def authors_top(limit: int = 10) -> dict[str, object]:
    items = top_authors(_posts(), limit=max(1, min(limit, 100)))
    return {"count": len(items), "items": items}


@app.get("/analytics/geo")
async def geo() -> dict[str, object]:
    items = geo_distribution(_posts())
    return {"count": len(items), "items": items}


@app.get("/analytics/wordcloud")
async def cloud(limit: int = 60) -> dict[str, object]:
    key = f"wordcloud:{limit}"
    cached = cache.get(key)
    if cached is not None:
        return {"cached": True, "items": cached}
    items = word_cloud(_posts(), limit=max(10, min(limit, 250)))
    cache.set(key, items)
    return {"cached": False, "items": items}


@app.get("/analytics/sentiment")
async def sentiment() -> dict[str, object]:
    counts = _sentiment_counts()
    total = max(sum(counts.values()), 1)
    return {
        "total": sum(counts.values()),
        "distribution": dict(counts),
        "positive_pct": round(counts.get("positive", 0) / total * 100, 2),
        "negative_pct": round(counts.get("negative", 0) / total * 100, 2),
        "neutral_pct": round(counts.get("neutral", 0) / total * 100, 2),
    }


@app.get("/analytics/performance")
async def performance() -> dict[str, object]:
    total = len(records)
    return {
        "refresh_target_minutes": settings.refresh_target_minutes,
        "sentiment_accuracy_target_pct": settings.sentiment_accuracy_target_pct,
        "throughput_target_posts_per_day": settings.throughput_target_posts_per_day,
        "current_records": total,
        "estimated_capacity_posts_per_day": min(settings.throughput_target_posts_per_day, total * 720),
    }


@app.post("/analytics/reset")
async def reset() -> dict[str, str]:
    records.clear()
    cache._store.clear()
    return {"status": "cleared"}
