from django.db import models

from apps.chatbot.models import LanguageChoices


class ChatbotAnalytics(models.Model):
    class EventType(models.TextChoices):
        CONVERSATION_STARTED = "conversation_started", "Conversation started"
        QUESTION_ASKED = "question_asked", "Question asked"
        FAQ_MATCHED = "faq_matched", "FAQ matched"
        UNANSWERED = "unanswered", "Question unanswered"
        FAQ_SEARCH = "faq_search", "FAQ searched"
        FAQ_VIEW = "faq_view", "FAQ viewed"
        FEEDBACK = "feedback", "Feedback submitted"
        LANGUAGE_SWITCH = "language_switch", "Language changed"
        CONVERSATION_CLEARED = "conversation_cleared", "Conversation cleared"

    event_type = models.CharField(max_length=32, choices=EventType.choices)
    category = models.ForeignKey(
        "faq.FAQCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_events",
    )
    language = models.CharField(max_length=2, choices=LanguageChoices.choices, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "chatbot analytics"
        ordering = ("-created_at",)
        permissions = [("view_analytics_dashboard", "Can view analytics dashboard")]
        indexes = [
            models.Index(fields=("event_type", "-created_at"), name="analytics_event_created_idx"),
            models.Index(fields=("language", "-created_at"), name="analytics_language_idx"),
            models.Index(fields=("category", "-created_at"), name="analytics_category_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} at {self.created_at:%Y-%m-%d %H:%M}"
