from __future__ import annotations

import random
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.smmradar_common import CollectRequest, GeoPoint, RawPostInput, Settings, SocialPlatform, SocialPost

settings = Settings(service_name="collector-service", service_port=8501)
app = FastAPI(title="SMM Radar Collector Service", version="1.0.0")

raw_posts: dict[str, SocialPost] = {}

CITIES = [
    ("Moscow", "Central", "RU", 55.7558, 37.6176),
    ("Saint Petersburg", "North-West", "RU", 59.9343, 30.3351),
    ("Kazan", "Volga", "RU", 55.7963, 49.1088),
    ("Novosibirsk", "Siberia", "RU", 55.0084, 82.9357),
    ("Yekaterinburg", "Ural", "RU", 56.8389, 60.6057),
]
TEXT_TEMPLATES = [
    "People discuss {kw} on {platform}. Product quality is {tone}. #{tag}",
    "{kw} trend is growing on {platform}. Users share feedback. #{tag}",
    "Breaking conversation about {kw} and brand reputation on {platform}. #{tag}",
]
TONE_WORDS = ["good", "great", "super", "bad", "awful", "neutral"]


def _make_geo(request_geo: GeoPoint | None) -> GeoPoint:
    if request_geo:
        return request_geo
    city, region, country, lat, lon = random.choice(CITIES)
    return GeoPoint(city=city, region=region, country=country, latitude=lat, longitude=lon)


def _build_mock_post(
    platform: SocialPlatform,
    keywords: list[str],
    hashtags: list[str],
    geo: GeoPoint | None,
) -> SocialPost:
    keyword = random.choice(keywords or ["brand"])
    tag = random.choice(hashtags or ["brandwatch"]).lstrip("#")
    tone = random.choice(TONE_WORDS)
    template = random.choice(TEXT_TEMPLATES)
    text = template.format(kw=keyword, platform=platform.value, tag=tag, tone=tone)
    post_id = f"{platform.value}-{uuid4().hex[:10]}"
    author_id = f"author-{random.randint(1000, 9999)}"
    return SocialPost(
        post_id=post_id,
        platform=platform,
        text=text,
        author_id=author_id,
        author_name=f"user_{author_id[-4:]}",
        url=f"https://social.example/{platform.value}/{post_id}",
        published_at=datetime.now(UTC),
        hashtags=[f"#{tag}"],
        mentions=["@brand"],
        geo=_make_geo(geo),
        metrics={
            "likes": random.randint(5, 1800),
            "comments": random.randint(0, 240),
            "shares": random.randint(0, 140),
            "views": random.randint(120, 15000),
        },
        language="ru",
    )


def _seed_posts() -> None:
    if raw_posts:
        return
    seed = CollectRequest(
        platforms=[SocialPlatform.VK, SocialPlatform.TELEGRAM, SocialPlatform.YOUTUBE],
        keywords=["SMM Radar", "brand quality"],
        hashtags=["#smm", "#analytics"],
        limit_per_platform=5,
    )
    for platform in seed.platforms:
        for _ in range(seed.limit_per_platform):
            post = _build_mock_post(platform, seed.keywords, seed.hashtags, seed.geo)
            raw_posts[post.post_id] = post


_seed_posts()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/collector/sources")
async def sources() -> dict[str, list[str]]:
    return {"sources": [source.value for source in SocialPlatform]}


@app.post("/collector/raw")
async def save_raw(payload: RawPostInput) -> dict[str, object]:
    post = SocialPost(post_id=f"{payload.platform.value}-{uuid4().hex[:10]}", **payload.model_dump(mode="python"))
    raw_posts[post.post_id] = post
    return post.model_dump(mode="json")


@app.post("/collector/collect")
async def collect(request: CollectRequest) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for platform in request.platforms:
        for _ in range(request.limit_per_platform):
            post = _build_mock_post(platform, request.keywords, request.hashtags, request.geo)
            raw_posts[post.post_id] = post
            items.append(post.model_dump(mode="json"))
    return {
        "batch_id": str(uuid4()),
        "generated": len(items),
        "platforms": [platform.value for platform in request.platforms],
        "items": items,
    }


@app.get("/collector/raw")
async def list_raw(
    platform: SocialPlatform | None = None,
    keyword: str | None = None,
    hashtag: str | None = None,
    city: str | None = None,
    limit: int = 100,
) -> dict[str, object]:
    items = list(raw_posts.values())
    if platform:
        items = [post for post in items if post.platform == platform]
    if keyword:
        lowered = keyword.lower()
        items = [post for post in items if lowered in post.text.lower()]
    if hashtag:
        normalized = hashtag if hashtag.startswith("#") else f"#{hashtag}"
        items = [post for post in items if normalized in post.hashtags]
    if city:
        city_lower = city.lower()
        items = [post for post in items if post.geo and (post.geo.city or "").lower() == city_lower]
    limited = items[: max(1, min(limit, 2000))]
    return {"count": len(limited), "items": [item.model_dump(mode="json") for item in limited]}


@app.get("/collector/raw/{post_id}")
async def get_raw(post_id: str) -> dict[str, object]:
    post = raw_posts.get(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post.model_dump(mode="json")


@app.get("/collector/stats")
async def collector_stats() -> dict[str, object]:
    by_source: dict[str, int] = {}
    for post in raw_posts.values():
        by_source[post.platform.value] = by_source.get(post.platform.value, 0) + 1
    return {"total_posts": len(raw_posts), "by_source": by_source}
