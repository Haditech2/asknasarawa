from __future__ import annotations

from dataclasses import dataclass

try:
    from rapidfuzz import fuzz
except ImportError:
    from difflib import SequenceMatcher

    class _FuzzFallback:
        @staticmethod
        def WRatio(s1: str, s2: str) -> float:
            return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100.0

        @staticmethod
        def token_set_ratio(s1: str, s2: str) -> float:
            tokens1 = set(s1.lower().split())
            tokens2 = set(s2.lower().split())
            if not tokens1 or not tokens2:
                return 0.0
            intersection = tokens1 & tokens2
            return (2.0 * len(intersection) / (len(tokens1) + len(tokens2))) * 100.0

    fuzz = _FuzzFallback()

from apps.core.text import normalize_text, token_overlap

from .models import FAQ


@dataclass(frozen=True)
class FAQSearchResult:
    faq: FAQ
    score: float
    matched_on: str


def _faq_values(faq: FAQ, language: str) -> list[tuple[str, str]]:
    if language == "ha":
        primary = [
            ("question", faq.question_ha),
            *(("alternative", value) for value in faq.alternative_questions_ha),
            *(("keyword", value) for value in faq.keywords_ha),
            ("answer", faq.answer_ha[:1000]),
        ]
        secondary = [("translated_question", faq.question_en)]
    else:
        primary = [
            ("question", faq.question_en),
            *(("alternative", value) for value in faq.alternative_questions_en),
            *(("keyword", value) for value in faq.keywords_en),
            ("answer", faq.answer_en[:1000]),
        ]
        secondary = [("translated_question", faq.question_ha)]
    return [(label, value) for label, value in primary + secondary if value]


def score_faq(query: str, faq: FAQ, language: str) -> tuple[float, str]:
    normalized_query = normalize_text(query)
    if not normalized_query:
        return 0.0, "none"

    best_score = 0.0
    matched_on = "none"
    for label, value in _faq_values(faq, language):
        normalized_value = normalize_text(value)
        if not normalized_value:
            continue
        if normalized_query == normalized_value:
            score = 100.0
        elif len(normalized_query) >= 3 and normalized_query in normalized_value:
            score = 95.0 if label in {"question", "alternative"} else 88.0
        elif normalized_value in normalized_query and label in {"question", "alternative", "keyword"}:
            score = 91.0
        else:
            ratio = fuzz.WRatio(normalized_query, normalized_value)
            token_score = fuzz.token_set_ratio(normalized_query, normalized_value)
            overlap_score = token_overlap(normalized_query, normalized_value) * 100
            score = max(ratio * 0.78 + overlap_score * 0.22, token_score * 0.9)
            if label == "answer":
                score *= 0.72
            elif label == "translated_question":
                score *= 0.95
            elif label == "keyword":
                score = min(98.0, score + 5)
        if score > best_score:
            best_score, matched_on = score, label

    category_values = (faq.category.name_en, faq.category.name_ha)
    category_score = max(fuzz.WRatio(normalized_query, normalize_text(value)) for value in category_values)
    if category_score > best_score and category_score >= 75:
        best_score, matched_on = category_score * 0.82, "category"
    return round(min(best_score, 100.0), 2), matched_on


def search_faqs(
    query: str,
    *,
    language: str = "en",
    category: str | int | None = None,
    limit: int = 20,
    minimum_score: float = 22,
) -> list[FAQSearchResult]:
    queryset = FAQ.objects.visible()
    if category:
        if str(category).isdigit():
            queryset = queryset.filter(category_id=int(category))
        else:
            queryset = queryset.filter(category__slug=str(category))

    results = []
    for faq in queryset:
        score, matched_on = score_faq(query, faq, language)
        if score >= minimum_score:
            results.append(FAQSearchResult(faq=faq, score=score, matched_on=matched_on))
    return sorted(results, key=lambda result: (-result.score, -result.faq.view_count))[:limit]


def related_faqs(faq: FAQ, language: str, limit: int = 4):
    return (
        FAQ.objects.visible()
        .filter(category=faq.category)
        .exclude(pk=faq.pk)
        .order_by("-is_featured", "-view_count", "question_en")[:limit]
    )
