from __future__ import annotations

import json
import urllib.request

BASE = "http://localhost:8580"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    result = request(
        "POST",
        "/workflow/monitor-run",
        {
            "brand": "SMM Radar",
            "collect": {
                "platforms": ["vk", "telegram", "youtube", "twitter"],
                "keywords": ["SMM Radar", "brand mention", "customer support"],
                "hashtags": ["#smm", "#brand", "#analytics"],
                "limit_per_platform": 8,
            },
            "competitors": ["BrandPulse", "InsightFlow"],
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
