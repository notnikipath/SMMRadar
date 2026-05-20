# Algorithms

## Sentiment baseline

- Tokenize text by alphanumeric fragments and social markers (`#`, `@`)
- Apply lightweight lemmatization by common suffix stripping
- Calculate sentiment score: `(positive_tokens - negative_tokens) / token_count`
- Map score to labels:
  - `score > 0.12` -> positive
  - `score < -0.12` -> negative
  - otherwise neutral

## Mention spike

- Spike ratio = `current_mentions / max(baseline_mentions, 1)`
- Alert if spike ratio exceeds threshold (default `2.0x`)

## Crisis probability

- `negativity = negative_mentions / total_mentions`
- `pressure = min(1.0, negativity * 0.85 + severe_alerts * 0.08)`
- Trigger warning/critical alerts at configured levels

## Share of Voice

- `SOV(brand) = mentions_brand / mentions_all_brands * 100`
- Output sorted table for dashboard ranking

## Optional predictive models

- Bot score based on posting rate, follower ratio, and duplicate content ratio
- Virality score based on engagement rate, reach, hashtags, and sentiment
