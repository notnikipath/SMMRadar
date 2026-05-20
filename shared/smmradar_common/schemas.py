from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SocialPlatform(str, Enum):
    VK = "vk"
    TELEGRAM = "telegram"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    RUTUBE = "rutube"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EntityType(str, Enum):
    PERSON = "person"
    ORG = "org"
    LOCATION = "location"
    HASHTAG = "hashtag"
    PRODUCT = "product"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    PUSH = "push"


class Role(str, Enum):
    ANALYST = "analyst"
    MANAGER = "manager"
    ADMIN = "admin"


class ReportFormat(str, Enum):
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"


class GeoPoint(BaseModel):
    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class CollectRequest(BaseModel):
    platforms: list[SocialPlatform] = Field(default_factory=lambda: list(SocialPlatform))
    keywords: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    geo: GeoPoint | None = None
    limit_per_platform: int = Field(default=25, ge=1, le=1000)


class RawPostInput(BaseModel):
    platform: SocialPlatform
    text: str = Field(min_length=3)
    author_id: str
    author_name: str
    url: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    geo: GeoPoint | None = None
    metrics: dict[str, int] = Field(default_factory=dict)


class SocialPost(BaseModel):
    post_id: str
    platform: SocialPlatform
    text: str
    author_id: str
    author_name: str
    url: str
    published_at: datetime
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    geo: GeoPoint | None = None
    metrics: dict[str, int] = Field(default_factory=dict)
    language: str = "ru"


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=3)
    platform: SocialPlatform | None = None


class NamedEntity(BaseModel):
    value: str
    entity_type: EntityType
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class SentimentResult(BaseModel):
    label: SentimentLabel
    score: float = Field(ge=-1, le=1)


class NLPResult(BaseModel):
    tokens: list[str] = Field(default_factory=list)
    lemmas: list[str] = Field(default_factory=list)
    sentiment: SentimentResult
    entities: list[NamedEntity] = Field(default_factory=list)


class AnalyticsIngestRequest(BaseModel):
    post: SocialPost
    nlp: NLPResult


class MentionPoint(BaseModel):
    ts_hour: datetime
    mentions: int


class AuthorStat(BaseModel):
    author_id: str
    author_name: str
    mentions: int
    engagement: int


class GeoStat(BaseModel):
    location: str
    mentions: int


class WordCloudEntry(BaseModel):
    token: str
    weight: int = Field(ge=1)


class AlertEvent(BaseModel):
    alert_id: str
    severity: Severity
    title: str
    details: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    event_id: str
    actor_id: str
    actor_role: Role | str
    action: str
    object_type: str
    object_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CompetitorSnapshot(BaseModel):
    brand: str
    mentions: int = Field(default=0, ge=0)
    positive: int = Field(default=0, ge=0)
    negative: int = Field(default=0, ge=0)
    engagement: int = Field(default=0, ge=0)


class ShareOfVoiceEntry(BaseModel):
    brand: str
    mentions: int = Field(ge=0)
    share_pct: float = Field(ge=0, le=100)


class ReportRequest(BaseModel):
    brand: str
    competitors: list[str] = Field(default_factory=list)
    from_dt: datetime | None = None
    to_dt: datetime | None = None
    report_format: ReportFormat = ReportFormat.JSON


class ProcessPostRequest(BaseModel):
    post_data: RawPostInput


class MonitorBatchRequest(BaseModel):
    brand: str
    collect: CollectRequest
    competitors: list[str] = Field(default_factory=list)


class ProcessPostResult(BaseModel):
    raw_post: SocialPost
    nlp: NLPResult
    analytics_status: str
    alert: AlertEvent | None = None


class DashboardSnapshot(BaseModel):
    summary: dict[str, Any]
    mention_dynamics: list[MentionPoint]
    top_authors: list[AuthorStat]
    geo_distribution: list[GeoStat]
    word_cloud: list[WordCloudEntry]
    alerts: list[AlertEvent]
    competitors: list[ShareOfVoiceEntry]
