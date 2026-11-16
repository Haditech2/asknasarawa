from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import F

from apps.analytics.services import record_event
from apps.core.text import detect_language, redact_sensitive_data
from apps.faq.models import FAQ
from apps.faq.services import FAQSearchResult, search_faqs

from .models import ChatMessage, Conversation, UnansweredQuestion


@dataclass(frozen=True)
class MatchOutcome:
    faq: FAQ | None
    confidence: float
    suggestions: list[FAQ]
    attempts: list[dict[str, Any]]


class FAQMatcher:
    def __init__(self, threshold: float | None = None, suggestion_threshold: float | None = None):
        self.threshold = threshold if threshold is not None else settings.CHAT_MATCH_THRESHOLD
        self.suggestion_threshold = (
            suggestion_threshold
            if suggestion_threshold is not None
            else settings.CHAT_SUGGESTION_THRESHOLD
        )

    def match(self, query: str, language: str, category=None) -> MatchOutcome:
        ranked: list[FAQSearchResult] = search_faqs(
            query,
            language=language,
            category=category,
            limit=8,
            minimum_score=0,
        )
        # Search alternate language as well to guarantee cross-lingual matches (e.g. Hausa query answered in English)
        alt_language = "en" if language == "ha" else "ha"
        alt_ranked: list[FAQSearchResult] = search_faqs(
            query,
            language=alt_language,
            category=category,
            limit=8,
            minimum_score=0,
        )
        seen: dict[int, FAQSearchResult] = {}
        for result in ranked + alt_ranked:
            if result.faq.pk not in seen or result.score > seen[result.faq.pk].score:
                seen[result.faq.pk] = result
        merged = sorted(seen.values(), key=lambda r: r.score, reverse=True)

        attempts = [
            {
                "faq_id": result.faq.pk,
                "score": result.score,
                "matched_on": result.matched_on,
            }
            for result in merged[:5]
        ]
        best = merged[0] if merged else None
        matched_faq = best.faq if best and best.score >= self.threshold else None
        suggestions = [
            result.faq
            for result in merged
            if result.score >= self.suggestion_threshold and result.faq != matched_faq
        ][:3]
        return MatchOutcome(
            faq=matched_faq,
            confidence=best.score if best else 0.0,
            suggestions=suggestions,
            attempts=attempts,
        )


def _session_key(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_current_conversation(request, preferred_language: str = "en") -> tuple[Conversation, bool]:
    session_key = _session_key(request)
    conversation_id = request.session.get("chat_conversation_id")
    conversation = None
    if conversation_id:
        conversation = Conversation.objects.filter(
            pk=conversation_id,
            session_id=session_key,
            is_active=True,
        ).first()
    created = False
    if conversation is None:
        conversation = Conversation.objects.create(
            session_id=session_key,
            preferred_language=preferred_language,
            user=request.user if request.user.is_authenticated else None,
        )
        request.session["chat_conversation_id"] = str(conversation.pk)
        created = True
        record_event("conversation_started", language=preferred_language)
    return conversation, created


def _fallback_message(language: str) -> str:
    if language == "ha":
        message = (
            "Ban sami amsa tabbatacciya ga wannan tambayar ba. Ban so in ba ka bayanin da ba a tabbatar ba. "
            "Ka zaɓi ɗaya daga tambayoyin da aka ba da shawara ko ka sake tambaya a taƙaice."
        )
        if settings.OFFICIAL_ENQUIRY_EMAIL:
            message += f" Don ƙarin bayani, tuntuɓi {settings.OFFICIAL_ENQUIRY_EMAIL}."
        return message
    message = (
        "I could not find a sufficiently reliable answer to that question, so I will not guess. "
        "Choose a related question or try asking again with fewer words."
    )
    if settings.OFFICIAL_ENQUIRY_EMAIL:
        message += f" For a case-specific enquiry, contact {settings.OFFICIAL_ENQUIRY_EMAIL}."
    return message


def _suggestion_payload(faqs: list[FAQ], language: str) -> list[dict]:
    return [
        {
            "id": faq.pk,
            "question": faq.localized_question(language),
            "category": faq.category.localized_name(language),
        }
        for faq in faqs
    ]


@transaction.atomic
def process_message(
    request,
    raw_message: str,
    *,
    preferred_language: str = "auto",
    category=None,
) -> dict:
    started = time.perf_counter()
    message, redacted = redact_sensitive_data(raw_message.strip())
    detected_language, detection_confidence = detect_language(message, "en")

    # Detect in-query language request (e.g. asking in Hausa but requesting English: "da turanci", "in english")
    norm_lower = message.lower()
    explicit_english = bool(
        re.search(r"\b(da\s+turanci|a\s+turanci|turanci|in\s+english|english|in\s+eng)\b", norm_lower)
    )
    explicit_hausa = bool(
        re.search(r"\b(da\s+hausa|a\s+hausa|in\s+hausa)\b", norm_lower)
    )

    if explicit_english:
        response_language = "en"
    elif explicit_hausa:
        response_language = "ha"
    elif preferred_language in {"en", "ha"}:
        response_language = preferred_language
    else:
        response_language = detected_language

    conversation, _ = get_current_conversation(request, response_language)
    if conversation.preferred_language != response_language:
        previous = conversation.preferred_language
        conversation.preferred_language = response_language
        conversation.save(update_fields=("preferred_language", "updated_at"))
        record_event(
            "language_switch",
            language=response_language,
            metadata={"from": previous, "to": response_language},
        )

    user_message = ChatMessage.objects.create(
        conversation=conversation,
        sender=ChatMessage.Sender.USER,
        message=message,
        language=detected_language,
    )
    record_event(
        "question_asked",
        language=detected_language,
        metadata={"message_id": user_message.pk, "redacted": redacted},
    )

    outcome = FAQMatcher().match(message, detected_language, category=category)
    if outcome.faq:
        faq = outcome.faq
        answer = faq.localized_answer(response_language)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        bot_message = ChatMessage.objects.create(
            conversation=conversation,
            sender=ChatMessage.Sender.BOT,
            message=answer,
            language=response_language,
            matched_faq=faq,
            confidence_score=outcome.confidence,
            response_time_ms=elapsed_ms,
        )
        FAQ.objects.filter(pk=faq.pk).update(view_count=F("view_count") + 1)
        record_event(
            "faq_matched",
            category=faq.category,
            language=response_language,
            metadata={"faq_id": faq.pk, "confidence": outcome.confidence},
        )
        matched = True
        source = {
            "name": faq.source_name,
            "url": faq.source_url,
            "verification_status": faq.verification_status,
            "last_verified_at": faq.last_verified_at,
        }
        category_payload = {
            "id": faq.category_id,
            "name": faq.category.localized_name(response_language),
        }
    else:
        answer = _fallback_message(response_language)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        bot_message = ChatMessage.objects.create(
            conversation=conversation,
            sender=ChatMessage.Sender.BOT,
            message=answer,
            language=response_language,
            confidence_score=outcome.confidence,
            response_time_ms=elapsed_ms,
        )
        UnansweredQuestion.objects.create(
            question=message,
            detected_language=detected_language,
            conversation=conversation,
            matching_attempts=outcome.attempts,
        )
        record_event(
            "unanswered",
            language=detected_language,
            metadata={"confidence": outcome.confidence},
        )
        matched = False
        source = None
        category_payload = None

    return {
        "conversation_id": conversation.pk,
        "user_message_id": user_message.pk,
        "message_id": bot_message.pk,
        "answer": answer,
        "answer_en": faq.answer_en if outcome.faq else None,
        "answer_ha": faq.answer_ha if outcome.faq else None,
        "question_en": faq.question_en if outcome.faq else None,
        "question_ha": faq.question_ha if outcome.faq else None,
        "language": response_language,
        "detected_language": detected_language,
        "language_confidence": detection_confidence,
        "matched": matched,
        "confidence": round(outcome.confidence, 2),
        "faq_id": outcome.faq.pk if outcome.faq else None,
        "category": category_payload,
        "source": source,
        "suggestions": _suggestion_payload(outcome.suggestions, response_language),
        "sensitive_data_redacted": redacted,
        "timestamp": bot_message.created_at,
    }


@transaction.atomic
def clear_conversation(request) -> None:
    session_key = _session_key(request)
    conversation_id = request.session.pop("chat_conversation_id", None)
    if conversation_id:
        Conversation.objects.filter(pk=conversation_id, session_id=session_key).update(is_active=False)
    record_event("conversation_cleared")
