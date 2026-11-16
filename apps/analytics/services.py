from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from apps.chatbot.models import ChatMessage, Conversation, UnansweredQuestion
from apps.faq.models import FAQ

from .models import ChatbotAnalytics


def record_event(event_type: str, *, category=None, language: str = "", metadata=None):
    valid_types = {choice for choice, _ in ChatbotAnalytics.EventType.choices}
    if event_type not in valid_types:
        raise ValueError(f"Unsupported analytics event: {event_type}")
    safe_metadata = metadata if isinstance(metadata, dict) else {}
    return ChatbotAnalytics.objects.create(
        event_type=event_type,
        category=category,
        language=language if language in {"en", "ha"} else "",
        metadata=safe_metadata,
    )


def analytics_snapshot(days: int = 30) -> dict:
    days = max(1, min(days, 366))
    start = timezone.now() - timedelta(days=days - 1)
    messages = ChatMessage.objects.filter(created_at__gte=start)
    user_messages = messages.filter(sender=ChatMessage.Sender.USER)
    conversations = Conversation.objects.filter(created_at__gte=start)
    unanswered = UnansweredQuestion.objects.filter(created_at__gte=start)

    language_rows = list(
        user_messages.values("language").annotate(count=Count("id")).order_by("language")
    )
    daily_rows = {
        row["day"]: row["count"]
        for row in user_messages.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    }
    daily = []
    today = timezone.localdate()
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        daily.append({"date": day.isoformat(), "count": daily_rows.get(day, 0)})

    monthly = list(
        user_messages.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    for row in monthly:
        row["month"] = row["month"].date().isoformat()

    top_faqs = list(
        messages.filter(sender=ChatMessage.Sender.BOT, matched_faq__isnull=False)
        .values("matched_faq_id", "matched_faq__question_en", "matched_faq__question_ha")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    top_categories = list(
        messages.filter(sender=ChatMessage.Sender.BOT, matched_faq__isnull=False)
        .values(
            "matched_faq__category_id",
            "matched_faq__category__name_en",
            "matched_faq__category__name_ha",
        )
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    return {
        "period_days": days,
        "totals": {
            "conversations": conversations.count(),
            "questions": user_messages.count(),
            "unanswered": unanswered.count(),
            "published_faqs": FAQ.objects.published().count(),
            "searches": ChatbotAnalytics.objects.filter(
                event_type=ChatbotAnalytics.EventType.FAQ_SEARCH,
                created_at__gte=start,
            ).count(),
        },
        "language_usage": language_rows,
        "daily_usage": daily,
        "monthly_usage": monthly,
        "top_faqs": top_faqs,
        "top_categories": top_categories,
        "unanswered_by_status": list(
            unanswered.values("status").annotate(count=Count("id")).order_by("status")
        ),
    }
