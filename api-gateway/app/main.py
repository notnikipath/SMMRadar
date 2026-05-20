from __future__ import annotations

from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.smmradar_common import MonitorBatchRequest, ProcessPostRequest, Role, Settings, sign_token, verify_token


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    service_port: int = 8500

    collector_service_url: str = "http://collector-service:8501"
    nlp_service_url: str = "http://nlp-service:8502"
    analytics_service_url: str = "http://analytics-service:8503"
    alert_service_url: str = "http://alert-service:8504"
    competitor_service_url: str = "http://competitor-service:8505"
    report_service_url: str = "http://report-service:8506"
    notification_service_url: str = "http://notification-service:8507"

    jwt_secret: str = Settings().jwt_secret
    token_exp_minutes: int = 240

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AuthRequest(BaseModel):
    user_id: str
    role: Role


settings = GatewaySettings()
app = FastAPI(title="SMM Radar API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


AuthRequest.model_rebuild()
MonitorBatchRequest.model_rebuild()
ProcessPostRequest.model_rebuild()


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def _service_urls() -> dict[str, str]:
    return {
        "collector": settings.collector_service_url,
        "nlp": settings.nlp_service_url,
        "analytics": settings.analytics_service_url,
        "alert": settings.alert_service_url,
        "competitor": settings.competitor_service_url,
        "report": settings.report_service_url,
        "notification": settings.notification_service_url,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/auth/token")
async def issue_token(request: AuthRequest) -> dict[str, str]:
    token = sign_token(
        {"sub": request.user_id, "role": request.role.value},
        settings.jwt_secret,
        exp_minutes=settings.token_exp_minutes,
    )
    return {"access_token": token, "token_type": "Bearer"}


@app.post("/auth/verify")
async def verify_auth(token: str) -> dict[str, Any]:
    payload = verify_token(token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.get("/services/health")
async def service_health() -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, base_url in _service_urls().items():
            try:
                statuses[name] = await _get_json(client, f"{base_url}/health")
            except HTTPException as exc:
                statuses[name] = {"status": "error", "detail": exc.detail}
            except httpx.HTTPError as exc:
                statuses[name] = {"status": "error", "detail": str(exc)}
    return statuses


@app.post("/workflow/process-post")
async def process_post(request: ProcessPostRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        post = await _post_json(
            client,
            f"{settings.collector_service_url}/collector/raw",
            request.post_data.model_dump(mode="json"),
        )
        nlp = await _post_json(
            client,
            f"{settings.nlp_service_url}/nlp/analyze",
            {"text": post["text"], "platform": post["platform"]},
        )
        analytics = await _post_json(
            client,
            f"{settings.analytics_service_url}/analytics/ingest",
            {"post": post, "nlp": nlp},
        )

        alert = None
        if nlp["sentiment"]["score"] < -0.5:
            alert_resp = await _post_json(
                client,
                f"{settings.alert_service_url}/alerts/check-crisis",
                {
                    "post_id": post["post_id"],
                    "sentiment_score": nlp["sentiment"]["score"],
                    "platform": post["platform"],
                },
            )
            alert = alert_resp.get("alert") if alert_resp.get("triggered") else None
            if alert:
                await _post_json(
                    client,
                    f"{settings.notification_service_url}/notify/crisis",
                    {
                        "recipient": "brand-security-room",
                        "alert_id": alert["alert_id"],
                        "details": alert["details"],
                        "actor_role": Role.MANAGER.value,
                    },
                )

    return {
        "raw_post": post,
        "nlp": nlp,
        "analytics_status": analytics.get("status", "accepted"),
        "alert": alert,
    }


@app.post("/workflow/monitor-run")
async def monitor_run(request: MonitorBatchRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        collected = await _post_json(
            client,
            f"{settings.collector_service_url}/collector/collect",
            request.collect.model_dump(mode="json"),
        )

        processed = 0
        negative_mentions = 0
        for post in collected["items"]:
            nlp = await _post_json(
                client,
                f"{settings.nlp_service_url}/nlp/analyze",
                {"text": post["text"], "platform": post["platform"]},
            )
            await _post_json(
                client,
                f"{settings.analytics_service_url}/analytics/ingest",
                {"post": post, "nlp": nlp},
            )
            processed += 1
            if nlp["sentiment"]["label"] == "negative":
                negative_mentions += 1

        overview = await _get_json(client, f"{settings.analytics_service_url}/analytics/overview")
        dynamics = await _get_json(
            client,
            f"{settings.analytics_service_url}/analytics/mentions/dynamics",
            {"hours": 24},
        )
        top_authors = await _get_json(
            client,
            f"{settings.analytics_service_url}/analytics/authors/top",
            {"limit": 10},
        )
        geo = await _get_json(client, f"{settings.analytics_service_url}/analytics/geo")
        cloud = await _get_json(client, f"{settings.analytics_service_url}/analytics/wordcloud", {"limit": 60})

        baseline = max(1, processed // 3)
        spike = await _post_json(
            client,
            f"{settings.alert_service_url}/alerts/check-spike",
            {"current_mentions": processed, "baseline_mentions": baseline, "spike_threshold": 2.0},
        )
        window = await _post_json(
            client,
            f"{settings.alert_service_url}/alerts/check-window",
            {
                "total_mentions": processed,
                "negative_mentions": negative_mentions,
                "baseline_mentions": baseline,
                "severe_signals": 1 if spike.get("triggered") else 0,
            },
        )
        alerts = await _get_json(client, f"{settings.alert_service_url}/alerts/history", {"limit": 25})

        mentions_map = {request.brand: processed}
        for competitor in request.competitors:
            mentions_map[competitor] = max(1, int(processed * 0.7))
        sov = await _post_json(
            client,
            f"{settings.competitor_service_url}/competitors/sov",
            {"brand": request.brand, "competitors": request.competitors, "mentions": mentions_map},
        )

        report = await _post_json(
            client,
            f"{settings.report_service_url}/reports/dashboard/build",
            {
                "brand": request.brand,
                "summary": overview["summary"],
                "mention_dynamics": dynamics["items"],
                "top_authors": top_authors["items"],
                "geo_distribution": geo["items"],
                "word_cloud": cloud["items"],
                "competitors": sov["items"],
                "alerts": alerts["items"],
            },
        )

    return {
        "brand": request.brand,
        "collected": collected["generated"],
        "processed": processed,
        "negative_mentions": negative_mentions,
        "spike": spike,
        "window": window,
        "report": report,
        "sov": sov,
    }


@app.get("/dashboard/overview")
async def dashboard_overview() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        summary = await _get_json(client, f"{settings.analytics_service_url}/analytics/overview")
        dynamics = await _get_json(
            client,
            f"{settings.analytics_service_url}/analytics/mentions/dynamics",
            {"hours": 24},
        )
        authors = await _get_json(
            client,
            f"{settings.analytics_service_url}/analytics/authors/top",
            {"limit": 8},
        )
        geo = await _get_json(client, f"{settings.analytics_service_url}/analytics/geo")
        cloud = await _get_json(client, f"{settings.analytics_service_url}/analytics/wordcloud", {"limit": 40})
        alerts = await _get_json(client, f"{settings.alert_service_url}/alerts/active", {"hours": 12})
        competitors = await _get_json(client, f"{settings.competitor_service_url}/competitors")
    return {
        "summary": summary.get("summary", {}),
        "mention_dynamics": dynamics.get("items", []),
        "top_authors": authors.get("items", []),
        "geo_distribution": geo.get("items", []),
        "word_cloud": cloud.get("items", []),
        "alerts": alerts.get("items", []),
        "competitors": competitors.get("items", []),
    }
