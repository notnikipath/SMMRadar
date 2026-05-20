from shared.smmradar_common import detect_bot_account, predict_post_virality, stream_parallel_plan


def test_detect_bot_account_flags_high_risk_profile() -> None:
    result = detect_bot_account(posts_per_day=120, followers=50, following=3000, duplicate_ratio=0.52)
    assert result["bot_score"] >= 0.6
    assert result["is_bot"] is True



def test_predict_post_virality() -> None:
    result = predict_post_virality(
        engagement_rate=0.42,
        author_reach=85000,
        hashtag_count=5,
        sentiment_score=0.35,
    )
    assert 0 <= result["virality_probability"] <= 1
    assert result["predicted_reach_multiplier"] >= 1



def test_stream_parallel_plan() -> None:
    plan = stream_parallel_plan(events_per_minute=24000, social_networks=7)
    assert plan["workers"] >= 2
    assert plan["batch_size"] >= 120
