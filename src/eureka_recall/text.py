from __future__ import annotations

import re


STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "하는",
    "하고",
    "있는",
    "없는",
    "그럼",
    "이거",
    "저거",
}


def extract_terms(text: str) -> list[str]:
    terms = []
    for match in re.finditer(r"[A-Za-z0-9_\-./가-힣]{2,}", text.lower()):
        term = match.group(0).strip("./")
        if term and term not in STOPWORDS:
            terms.append(term)
    return list(dict.fromkeys(terms))


def score_text(text: str, terms: list[str]) -> float:
    lowered = text.lower()
    score = 0.0
    for term in terms:
        count = lowered.count(term.lower())
        if count:
            score += min(count, 5)
    return score


def snippet_for(text: str, terms: list[str], max_chars: int = 700) -> str:
    if not text:
        return ""
    lowered = text.lower()
    best_index = -1
    for term in terms:
        best_index = lowered.find(term.lower())
        if best_index >= 0:
            break
    if best_index < 0:
        return text[:max_chars].strip()
    start = max(best_index - max_chars // 3, 0)
    end = min(start + max_chars, len(text))
    return text[start:end].strip()

