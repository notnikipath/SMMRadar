from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from .schemas import EntityType, NamedEntity, SentimentLabel, SentimentResult, SocialPost

TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-я0-9_#@]{2,}", re.UNICODE)
STOPWORDS = {
    "the",
    "and",
    "for",
    "это",
    "как",
    "что",
    "или",
    "при",
    "без",
    "from",
    "with",
    "brand",
    "https",
}
POSITIVE_WORDS = {
    "good",
    "great",
    "best",
    "love",
    "amazing",
    "супер",
    "отлично",
    "класс",
    "рекомендую",
    "нравится",
}
NEGATIVE_WORDS = {
    "bad",
    "awful",
    "hate",
    "poor",
    "worst",
    "ужас",
    "плохо",
    "кошмар",
    "проблема",
    "скандал",
}


def tokenize_text(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text or "")]


def lemmatize_token(token: str) -> str:
    suffixes = (
        "иями",
        "ями",
        "ами",
        "ого",
        "ему",
        "ому",
        "ее",
        "ие",
        "ый",
        "ий",
        "ой",
        "ая",
        "ое",
        "ые",
        "ий",
        "ым",
        "ом",
        "ах",
        "ях",
        "ов",
        "ев",
        "а",
        "я",
        "ы",
        "и",
        "е",
        "о",
        "у",
    )
    for suffix in suffixes:
        if len(token) > len(suffix) + 2 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def lemmatize_tokens(tokens: Iterable[str]) -> list[str]:
    return [lemmatize_token(token) for token in tokens]


def score_sentiment(tokens: Iterable[str]) -> SentimentResult:
    token_list = list(tokens)
    if not token_list:
        return SentimentResult(label=SentimentLabel.NEUTRAL, score=0)
    pos = sum(1 for token in token_list if token in POSITIVE_WORDS)
    neg = sum(1 for token in token_list if token in NEGATIVE_WORDS)
    raw = (pos - neg) / max(len(token_list), 1)
    score = round(max(-1.0, min(1.0, raw * 4)), 3)
    if score > 0.12:
        label = SentimentLabel.POSITIVE
    elif score < -0.12:
        label = SentimentLabel.NEGATIVE
    else:
        label = SentimentLabel.NEUTRAL
    return SentimentResult(label=label, score=score)


def extract_entities(text: str) -> list[NamedEntity]:
    entities: list[NamedEntity] = []
    for match in re.finditer(r"#([A-Za-zА-Яа-я0-9_]+)", text):
        entities.append(
            NamedEntity(
                value=match.group(0),
                entity_type=EntityType.HASHTAG,
                start=match.start(),
                end=match.end(),
            )
        )
    for match in re.finditer(r"@([A-Za-zА-Яа-я0-9_.]+)", text):
        entities.append(
            NamedEntity(
                value=match.group(0),
                entity_type=EntityType.PERSON,
                start=match.start(),
                end=match.end(),
            )
        )
    for match in re.finditer(r"\b(Москва|Санкт-Петербург|Казань|Новосибирск|Екатеринбург)\b", text):
        entities.append(
            NamedEntity(
                value=match.group(0),
                entity_type=EntityType.LOCATION,
                start=match.start(),
                end=match.end(),
            )
        )
    return entities


def mention_dynamics(posts: list[SocialPost], hours: int = 24) -> list[dict[str, object]]:
    now = datetime.now(UTC)
    since = now - timedelta(hours=hours)
    buckets: dict[datetime, int] = defaultdict(int)
    for post in posts:
        if post.published_at < since:
            continue
        ts_hour = post.published_at.replace(minute=0, second=0, microsecond=0)
        buckets[ts_hour] += 1
    return [{"ts_hour": ts, "mentions": buckets[ts]} for ts in sorted(buckets)]


def top_authors(posts: list[SocialPost], limit: int = 10) -> list[dict[str, object]]:
    counters: dict[tuple[str, str], dict[str, int]] = {}
    for post in posts:
        key = (post.author_id, post.author_name)
        engagement = int(post.metrics.get("likes", 0)) + int(post.metrics.get("comments", 0))
        state = counters.setdefault(key, {"mentions": 0, "engagement": 0})
        state["mentions"] += 1
        state["engagement"] += engagement
    ranked = sorted(
        counters.items(),
        key=lambda entry: (entry[1]["mentions"], entry[1]["engagement"]),
        reverse=True,
    )
    return [
        {
            "author_id": author_id,
            "author_name": author_name,
            "mentions": stats["mentions"],
            "engagement": stats["engagement"],
        }
        for (author_id, author_name), stats in ranked[:limit]
    ]


def geo_distribution(posts: list[SocialPost]) -> list[dict[str, object]]:
    counter: Counter[str] = Counter()
    for post in posts:
        if post.geo and post.geo.city:
            counter[post.geo.city] += 1
        elif post.geo and post.geo.region:
            counter[post.geo.region] += 1
        else:
            counter["unknown"] += 1
    return [{"location": location, "mentions": count} for location, count in counter.most_common()]


def word_cloud(posts: list[SocialPost], limit: int = 80) -> list[dict[str, object]]:
    freq: Counter[str] = Counter()
    for post in posts:
        tokens = lemmatize_tokens(tokenize_text(post.text))
        for token in tokens:
            if token in STOPWORDS or len(token) < 3:
                continue
            freq[token] += 1
    return [{"token": token, "weight": count} for token, count in freq.most_common(limit)]


def share_of_voice(mentions: dict[str, int]) -> list[dict[str, object]]:
    total = sum(max(value, 0) for value in mentions.values())
    if total == 0:
        return [{"brand": brand, "mentions": value, "share_pct": 0.0} for brand, value in mentions.items()]
    return [
        {
            "brand": brand,
            "mentions": value,
            "share_pct": round(value / total * 100, 2),
        }
        for brand, value in sorted(mentions.items(), key=lambda entry: entry[1], reverse=True)
    ]


def spike_ratio(current_mentions: int, baseline_mentions: int) -> float:
    return round(current_mentions / max(baseline_mentions, 1), 2)


def crisis_probability(negative_mentions: int, total_mentions: int, severe_alerts: int = 0) -> float:
    if total_mentions <= 0:
        return 0.0
    negativity = negative_mentions / total_mentions
    pressure = min(1.0, negativity * 0.85 + severe_alerts * 0.08)
    return round(pressure, 3)
