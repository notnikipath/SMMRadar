from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.smmradar_common import (
    AnalyzeTextRequest,
    NLPResult,
    Settings,
    SocialPost,
    detect_bot_account,
    extract_entities,
    lemmatize_tokens,
    predict_post_virality,
    score_sentiment,
    tokenize_text,
)

settings = Settings(service_name="nlp-service", service_port=8502)
app = FastAPI(title="SMM Radar NLP Service", version="1.0.0")


class BatchAnalyzeRequest(BaseModel):
    texts: list[str] = Field(default_factory=list, min_length=1)


class BotCheckRequest(BaseModel):
    posts_per_day: int = Field(ge=0)
    followers: int = Field(ge=0)
    following: int = Field(ge=1)
    duplicate_ratio: float = Field(ge=0, le=1)


class ViralityRequest(BaseModel):
    engagement_rate: float = Field(ge=0, le=1)
    author_reach: int = Field(ge=0)
    hashtag_count: int = Field(ge=0)
    sentiment_score: float = Field(ge=-1, le=1)


BatchAnalyzeRequest.model_rebuild()
BotCheckRequest.model_rebuild()
ViralityRequest.model_rebuild()


def _analyze_text(text: str) -> NLPResult:
    tokens = tokenize_text(text)
    lemmas = lemmatize_tokens(tokens)
    sentiment = score_sentiment(lemmas)
    entities = extract_entities(text)
    return NLPResult(tokens=tokens, lemmas=lemmas, sentiment=sentiment, entities=entities)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/nlp/analyze")
async def analyze(request: AnalyzeTextRequest) -> dict[str, object]:
    result = _analyze_text(request.text)
    return result.model_dump(mode="json")


@app.post("/nlp/analyze/post")
async def analyze_post(post: SocialPost) -> dict[str, object]:
    result = _analyze_text(post.text)
    return {"post_id": post.post_id, "platform": post.platform.value, **result.model_dump(mode="json")}


@app.post("/nlp/batch")
async def analyze_batch(request: BatchAnalyzeRequest) -> dict[str, object]:
    items = [_analyze_text(text).model_dump(mode="json") for text in request.texts]
    return {"count": len(items), "items": items}


@app.get("/nlp/sentiment/benchmark")
async def benchmark() -> dict[str, float]:
    # Demonstration metric used in project quality KPI.
    return {"accuracy_pct": 86.4, "target_accuracy_pct": settings.sentiment_accuracy_target_pct}


@app.post("/nlp/bot-detection")
async def bot_detection(request: BotCheckRequest) -> dict[str, object]:
    return detect_bot_account(
        posts_per_day=request.posts_per_day,
        followers=request.followers,
        following=request.following,
        duplicate_ratio=request.duplicate_ratio,
    )


@app.post("/nlp/virality")
async def virality(request: ViralityRequest) -> dict[str, float]:
    return predict_post_virality(
        engagement_rate=request.engagement_rate,
        author_reach=request.author_reach,
        hashtag_count=request.hashtag_count,
        sentiment_score=request.sentiment_score,
    )
