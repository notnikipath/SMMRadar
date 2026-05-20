from pathlib import Path

from fastapi.testclient import TestClient

from tests.integration.helpers import load_module

ROOT = Path(__file__).resolve().parents[2]

collector_module = load_module("collector_module", ROOT / "collector-service" / "app" / "main.py")
nlp_module = load_module("nlp_module", ROOT / "nlp-service" / "app" / "main.py")
analytics_module = load_module("analytics_module", ROOT / "analytics-service" / "app" / "main.py")
alert_module = load_module("alert_module", ROOT / "alert-service" / "app" / "main.py")
competitor_module = load_module("competitor_module", ROOT / "competitor-service" / "app" / "main.py")
report_module = load_module("report_module", ROOT / "report-service" / "app" / "main.py")
notification_module = load_module("notification_module", ROOT / "notification-service" / "app" / "main.py")

collector_client = TestClient(collector_module.app)
nlp_client = TestClient(nlp_module.app)
analytics_client = TestClient(analytics_module.app)
alert_client = TestClient(alert_module.app)
competitor_client = TestClient(competitor_module.app)
report_client = TestClient(report_module.app)
notification_client = TestClient(notification_module.app)


def test_collect_nlp_analytics_flow() -> None:
    analytics_client.post("/analytics/reset")

    collected = collector_client.post(
        "/collector/collect",
        json={
            "platforms": ["vk", "telegram"],
            "keywords": ["SMM Radar", "support quality"],
            "hashtags": ["#smm", "#radar"],
            "limit_per_platform": 2,
        },
    )
    assert collected.status_code == 200
    payload = collected.json()
    assert payload["generated"] == 4

    post = payload["items"][0]
    nlp = nlp_client.post("/nlp/analyze", json={"text": post["text"], "platform": post["platform"]})
    assert nlp.status_code == 200
    nlp_payload = nlp.json()
    assert "sentiment" in nlp_payload

    ingest = analytics_client.post("/analytics/ingest", json={"post": post, "nlp": nlp_payload})
    assert ingest.status_code == 200

    overview = analytics_client.get("/analytics/overview")
    assert overview.status_code == 200
    assert overview.json()["summary"]["total_mentions"] >= 1


def test_alert_competitor_report_and_notification_flow() -> None:
    spike = alert_client.post(
        "/alerts/check-spike",
        json={"current_mentions": 120, "baseline_mentions": 40, "spike_threshold": 2.0},
    )
    assert spike.status_code == 200
    assert spike.json()["triggered"] is True

    sov = competitor_client.post(
        "/competitors/sov",
        json={
            "brand": "SMM Radar",
            "competitors": ["BrandPulse", "InsightFlow"],
            "mentions": {"SMM Radar": 180, "BrandPulse": 120, "InsightFlow": 60},
        },
    )
    assert sov.status_code == 200
    assert sov.json()["items"][0]["brand"] == "SMM Radar"

    report = report_client.post(
        "/reports/dashboard/build",
        json={
            "brand": "SMM Radar",
            "summary": {"total_mentions": 180, "crisis_probability": 0.24},
            "mention_dynamics": [{"ts_hour": "2026-01-01T12:00:00Z", "mentions": 33}],
            "top_authors": [{"author_id": "a-1", "author_name": "user_1", "mentions": 4, "engagement": 120}],
            "geo_distribution": [{"location": "Moscow", "mentions": 40}],
            "word_cloud": [{"token": "brand", "weight": 16}],
            "competitors": sov.json()["items"],
            "alerts": [],
        },
    )
    assert report.status_code == 200
    report_id = report.json()["report_id"]

    exported = report_client.post(
        "/reports/export",
        json={"report_id": report_id, "report_format": "excel"},
    )
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")

    notify = notification_client.post(
        "/notify/send",
        json={
            "channel": "telegram",
            "recipient": "@marketing-team",
            "subject": "Mentions spike",
            "body": "Mentions are above baseline",
            "severity": "warning",
            "actor_role": "manager",
        },
    )
    assert notify.status_code == 200
