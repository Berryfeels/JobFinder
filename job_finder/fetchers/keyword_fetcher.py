from __future__ import annotations


def normalize_keywords(keywords: str) -> str:
    tokens = [token.strip() for token in keywords.split(",") if token.strip()]
    if tokens:
        return " ".join(tokens)
    return keywords.strip()


def keyword_tokens(keywords: str) -> list[str]:
    return [token.strip().lower() for token in keywords.split(",") if token.strip()]


def matches_keywords(text: str | None, tokens: list[str]) -> bool:
    if not tokens:
        return True
    if not text:
        return False
    lowered = text.lower()
    return all(token in lowered for token in tokens)
