from shared.smmradar_common import crisis_probability, score_sentiment, share_of_voice, tokenize_text


def test_tokenize_text() -> None:
    tokens = tokenize_text("SMM Radar is great #analytics")
    assert "smm" in tokens
    assert "#analytics" in tokens



def test_sentiment_scoring_positive() -> None:
    result = score_sentiment(["great", "super", "brand"])
    assert result.label.value == "positive"
    assert result.score > 0



def test_share_of_voice() -> None:
    items = share_of_voice({"A": 50, "B": 30, "C": 20})
    assert items[0]["brand"] == "A"
    assert round(sum(item["share_pct"] for item in items), 2) == 100.0



def test_crisis_probability() -> None:
    value = crisis_probability(negative_mentions=45, total_mentions=100, severe_alerts=2)
    assert 0 < value <= 1
