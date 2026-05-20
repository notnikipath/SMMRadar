from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.smmradar_common import AlertEvent, Settings, Severity, crisis_probability, spike_ratio

settings = Settings(service_name="alert-service", service_port=8504)
app = FastAPI(title="SMM Radar Alert Service", version="1.0.0")

alert_history: list[AlertEvent] = []


class SpikeCheckRequest(BaseModel):
    current_mentions: int = Field(ge=0)
    baseline_mentions: int = Field(ge=0)
    spike_threshold: float = Field(default=2.0, ge=1.0)


class CrisisCheckRequest(BaseModel):
    post_id: str
    sentiment_score: float = Field(ge=-1, le=1)
    platform: str


class WindowCheckRequest(BaseModel):
    total_mentions: int = Field(ge=0)
    negative_mentions: int = Field(ge=0)
    baseline_mentions: int = Field(ge=0)
    severe_signals: int = Field(default=0, ge=0)


SpikeCheckRequest.model_rebuild()
CrisisCheckRequest.model_rebuild()
WindowCheckRequest.model_rebuild()


def _push_alert(severity: Severity, title: str, details: str, metadata: dict | None = None) -> AlertEvent:
    event = AlertEvent(
        alert_id=f"alt-{uuid4().hex[:10]}",
        severity=severity,
        title=title,
        details=details,
        created_at=datetime.now(UTC),
        metadata=metadata or {},
    )
    alert_history.append(event)
    return event


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/alerts/check-spike")
async def check_spike(request: SpikeCheckRequest) -> dict[str, object]:
    ratio = spike_ratio(request.current_mentions, request.baseline_mentions)
    if ratio >= request.spike_threshold:
        event = _push_alert(
            severity=Severity.WARNING,
            title="Mentions spike detected",
            details=f"Spike ratio reached {ratio}x against baseline.",
            metadata={"ratio": ratio, "baseline": request.baseline_mentions, "current": request.current_mentions},
        )
        return {"triggered": True, "ratio": ratio, "alert": event.model_dump(mode="json")}
    return {"triggered": False, "ratio": ratio}


@app.post("/alerts/check-crisis")
async def check_crisis(request: CrisisCheckRequest) -> dict[str, object]:
    if request.sentiment_score < -0.5:
        event = _push_alert(
            severity=Severity.CRITICAL,
            title="Crisis sentiment signal",
            details=f"Negative sentiment score {request.sentiment_score} detected.",
            metadata={"post_id": request.post_id, "platform": request.platform},
        )
        return {"triggered": True, "alert": event.model_dump(mode="json")}
    return {"triggered": False}


@app.post("/alerts/check-window")
async def check_window(request: WindowCheckRequest) -> dict[str, object]:
    pressure = crisis_probability(request.negative_mentions, request.total_mentions, request.severe_signals)
    ratio = spike_ratio(request.total_mentions, request.baseline_mentions)
    triggered = pressure >= 0.42 or ratio >= 2.5
    alert = None
    if triggered:
        severity = Severity.CRITICAL if pressure >= 0.58 else Severity.WARNING
        alert = _push_alert(
            severity=severity,
            title="Window monitoring alert",
            details=f"Pressure={pressure}, spike={ratio}.",
            metadata={
                "pressure": pressure,
                "spike": ratio,
                "negative_mentions": request.negative_mentions,
                "total_mentions": request.total_mentions,
            },
        )
    return {
        "triggered": triggered,
        "pressure": pressure,
        "spike_ratio": ratio,
        "alert": alert.model_dump(mode="json") if alert else None,
    }


@app.get("/alerts/history")
async def history(limit: int = 100) -> dict[str, object]:
    items = [item.model_dump(mode="json") for item in alert_history[-max(1, min(limit, 2000)) :]]
    return {"count": len(items), "items": items}


@app.get("/alerts/active")
async def active(hours: int = 12) -> dict[str, object]:
    threshold = datetime.now(UTC) - timedelta(hours=max(1, min(hours, 72)))
    active_items = [
        item.model_dump(mode="json")
        for item in alert_history
        if item.created_at >= threshold and item.severity in {Severity.WARNING, Severity.CRITICAL}
    ]
    return {"count": len(active_items), "items": active_items}
