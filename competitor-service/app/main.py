from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.smmradar_common import CompetitorSnapshot, Settings, share_of_voice

settings = Settings(service_name="competitor-service", service_port=8505)
app = FastAPI(title="SMM Radar Competitor Service", version="1.0.0")

snapshots: dict[str, CompetitorSnapshot] = {
    "SMM Radar": CompetitorSnapshot(brand="SMM Radar", mentions=4200, positive=2100, negative=520, engagement=102000),
    "BrandPulse": CompetitorSnapshot(brand="BrandPulse", mentions=3700, positive=1650, negative=640, engagement=81200),
    "InsightFlow": CompetitorSnapshot(
        brand="InsightFlow",
        mentions=2900,
        positive=1210,
        negative=510,
        engagement=66300,
    ),
}


class SnapshotBatchRequest(BaseModel):
    items: list[CompetitorSnapshot] = Field(default_factory=list)


class SOVRequest(BaseModel):
    brand: str
    competitors: list[str] = Field(default_factory=list)
    mentions: dict[str, int] = Field(default_factory=dict)


SnapshotBatchRequest.model_rebuild()
SOVRequest.model_rebuild()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/competitors")
async def list_competitors() -> dict[str, object]:
    return {"count": len(snapshots), "items": [item.model_dump(mode="json") for item in snapshots.values()]}


@app.post("/competitors/update")
async def update_competitors(request: SnapshotBatchRequest) -> dict[str, Any]:
    for item in request.items:
        snapshots[item.brand] = item
    return {"status": "updated", "count": len(request.items)}


@app.post("/competitors/sov")
async def sov(request: SOVRequest) -> dict[str, object]:
    mentions = dict(request.mentions)
    tracked_names = [request.brand, *request.competitors]
    if not mentions:
        for name in tracked_names:
            snapshot = snapshots.get(name)
            if snapshot:
                mentions[name] = snapshot.mentions
    if request.brand not in mentions:
        mentions[request.brand] = snapshots.get(request.brand, CompetitorSnapshot(brand=request.brand)).mentions

    table = share_of_voice(mentions)
    return {"brand": request.brand, "count": len(table), "items": table}


@app.get("/competitors/compare")
async def compare(brand_a: str, brand_b: str) -> dict[str, object]:
    left = snapshots.get(brand_a, CompetitorSnapshot(brand=brand_a))
    right = snapshots.get(brand_b, CompetitorSnapshot(brand=brand_b))

    left_positive_rate = left.positive / max(left.mentions, 1)
    right_positive_rate = right.positive / max(right.mentions, 1)
    left_negative_rate = left.negative / max(left.mentions, 1)
    right_negative_rate = right.negative / max(right.mentions, 1)

    return {
        "brand_a": left.model_dump(mode="json"),
        "brand_b": right.model_dump(mode="json"),
        "delta_mentions": left.mentions - right.mentions,
        "delta_engagement": left.engagement - right.engagement,
        "delta_positive_rate": round(left_positive_rate - right_positive_rate, 3),
        "delta_negative_rate": round(left_negative_rate - right_negative_rate, 3),
    }
