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

GENERIC_MEMORY_TERMS = {
    "agent",
    "agents",
    "activation",
    "card",
    "cards",
    "connector",
    "connectors",
    "context",
    "design",
    "llm",
    "localwiki",
    "memory",
    "rag",
}


def extract_terms(text: str) -> list[str]:
    terms = []
    for match in re.finditer(r"[A-Za-z0-9_\-./가-힣]{2,}", text):
        raw = match.group(0).strip("./")
        for part in _term_variants(raw):
            term = part.lower()
            if term and term not in STOPWORDS:
                terms.append(term)
    return list(dict.fromkeys(terms))


def _term_variants(term: str) -> list[str]:
    variants = [term]
    camel_parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", term).split()
    if len(camel_parts) > 1:
        variants.extend(camel_parts)
    return variants


def score_text(text: str, terms: list[str]) -> float:
    lowered = text.lower()
    score = 0.0
    for term in terms:
        count = lowered.count(term.lower())
        if count:
            weight = 0.5 if term in GENERIC_MEMORY_TERMS else 1.0
            score += min(count, 5) * weight
    return score


def has_specific_match(text: str, terms: list[str]) -> bool:
    specific_terms = [term for term in terms if term not in GENERIC_MEMORY_TERMS]
    if not specific_terms:
        return True
    lowered = text.lower()
    return any(term.lower() in lowered for term in specific_terms)


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
