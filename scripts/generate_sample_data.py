from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

PLATFORMS = ["vk", "telegram", "youtube", "twitter", "instagram", "facebook", "rutube"]
CITIES = ["Moscow", "Saint Petersburg", "Kazan", "Novosibirsk", "Yekaterinburg"]
KEYWORDS = ["SMM Radar", "brand support", "delivery speed", "customer service", "new campaign"]
TONES = ["great", "good", "neutral", "bad", "awful"]


def generate_record(index: int) -> dict:
    platform = random.choice(PLATFORMS)
    city = random.choice(CITIES)
    keyword = random.choice(KEYWORDS)
    tone = random.choice(TONES)
    hashtags = ["#smm", f"#{platform}", "#brand"]
    text = f"{keyword} feedback on {platform} is {tone}. {hashtags[0]} {hashtags[1]}"
    likes = random.randint(0, 5000)
    comments = random.randint(0, 800)
    shares = random.randint(0, 550)
    views = random.randint(100, 50000)
    return {
        "post_id": f"{platform}-{index:06d}",
        "platform": platform,
        "author_id": f"author-{random.randint(1000, 9999)}",
        "author_name": f"user_{random.randint(1000, 9999)}",
        "text": text,
        "hashtags": hashtags,
        "mentions": ["@brand"],
        "geo": {"country": "RU", "city": city},
        "metrics": {
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views,
        },
        "published_at": (datetime.now(UTC) - timedelta(minutes=index)).isoformat(),
    }


if __name__ == "__main__":
    random.seed(42)
    output = Path(__file__).resolve().parents[1] / "data" / "samples" / "social_events.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = [generate_record(index) for index in range(1, 12001)]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload)} records to {output}")
