from __future__ import annotations

from collections import Counter

from .schemas import SocialPlatform


def detect_bot_account(
    posts_per_day: int,
    followers: int,
    following: int,
    duplicate_ratio: float,
) -> dict[str, object]:
    follower_ratio = followers / max(following, 1)
    score = 0.0
    if posts_per_day > 60:
        score += 0.45
    if follower_ratio < 0.08:
        score += 0.25
    if duplicate_ratio > 0.35:
        score += 0.3
    score = round(min(1.0, score), 3)
    return {"bot_score": score, "is_bot": score >= 0.6}


def predict_post_virality(
    engagement_rate: float,
    author_reach: int,
    hashtag_count: int,
    sentiment_score: float,
) -> dict[str, float]:
    reach_factor = min(author_reach / 200_000, 1)
    hashtag_factor = min(hashtag_count / 8, 1)
    sentiment_factor = (sentiment_score + 1) / 2
    probability = engagement_rate * 0.5 + reach_factor * 0.25 + hashtag_factor * 0.15 + sentiment_factor * 0.1
    probability = round(min(max(probability, 0), 1), 3)
    return {
        "virality_probability": probability,
        "predicted_reach_multiplier": round(1 + probability * 4.5, 2),
    }


def stream_parallel_plan(events_per_minute: int, social_networks: int) -> dict[str, int]:
    workers = min(64, max(2, social_networks * 3, events_per_minute // 300))
    batch_size = min(2_000, max(120, events_per_minute // max(workers, 1)))
    return {"workers": workers, "batch_size": batch_size, "events_per_minute": events_per_minute}


def shard_by_platform(posts: list[dict[str, object]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for post in posts:
        platform = str(post.get("platform", "unknown"))
        counts[platform] += 1
    return dict(counts)


def recommended_cache_ttl(platform: SocialPlatform, volatility_index: float) -> int:
    base = {
        SocialPlatform.TWITTER: 60,
        SocialPlatform.TELEGRAM: 90,
        SocialPlatform.VK: 120,
        SocialPlatform.YOUTUBE: 300,
        SocialPlatform.INSTAGRAM: 180,
        SocialPlatform.FACEBOOK: 240,
        SocialPlatform.RUTUBE: 320,
    }[platform]
    modifier = max(0.4, min(1.8, 1.2 - volatility_index))
    return int(base * modifier)
