from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.smmradar_common import NotificationChannel, Role, Settings, Severity, has_permission

settings = Settings(service_name="notification-service", service_port=8507)
app = FastAPI(title="SMM Radar Notification Service", version="1.0.0")

messages: list[dict[str, Any]] = []


class NotificationRequest(BaseModel):
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    severity: Severity = Severity.INFO
    actor_role: Role = Role.MANAGER


class CrisisNotificationRequest(BaseModel):
    recipient: str
    alert_id: str
    details: str
    actor_role: Role = Role.MANAGER


NotificationRequest.model_rebuild()
CrisisNotificationRequest.model_rebuild()


def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot {action}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/notify/send")
async def send_notification(request: NotificationRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "notification:send")
    payload = {
        **request.model_dump(mode="json"),
        "status": "queued",
        "created_at": datetime.now(UTC).isoformat(),
    }
    messages.append(payload)
    return payload


@app.post("/notify/crisis")
async def crisis_notification(request: CrisisNotificationRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "notification:send")
    payload = {
        "channel": NotificationChannel.TELEGRAM.value,
        "recipient": request.recipient,
        "subject": "Crisis monitoring signal",
        "body": f"Alert {request.alert_id}: {request.details}",
        "severity": Severity.CRITICAL.value,
        "status": "queued",
        "created_at": datetime.now(UTC).isoformat(),
    }
    messages.append(payload)
    return payload


@app.get("/notify/history")
async def history(limit: int = 100) -> dict[str, Any]:
    items = messages[-max(1, min(limit, 2000)) :]
    return {"count": len(items), "items": items}
