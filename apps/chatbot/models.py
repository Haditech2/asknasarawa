from __future__ import annotations

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class LanguageChoices(models.TextChoices):
    ENGLISH = "en", "English"
    HAUSA = "ha", "Hausa"


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=64, db_index=True)
    preferred_language = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_conversations",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        permissions = [("view_conversation_details", "Can view conversation details")]
        indexes = [
            models.Index(fields=("session_id", "is_active"), name="chat_session_active_idx"),
            models.Index(fields=("-created_at",), name="chat_conversation_created_idx"),
        ]

    def __str__(self) -> str:
        return f"Conversation {str(self.id)[:8]} ({self.preferred_language})"


class ChatMessage(models.Model):
    class Sender(models.TextChoices):
        USER = "user", "User"
        BOT = "bot", "Chatbot"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=4, choices=Sender.choices)
    message = models.TextField(max_length=4000)
    language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    matched_faq = models.ForeignKey(
        "faq.FAQ",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_messages",
    )
    confidence_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(fields=("conversation", "created_at"), name="chatmsg_conversation_idx"),
            models.Index(fields=("sender", "language", "-created_at"), name="chatmsg_sender_lang_idx"),
            models.Index(fields=("matched_faq",), name="chatmsg_matched_faq_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_sender_display()}: {self.message[:60]}"


class UnansweredQuestion(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        REVIEWED = "reviewed", "Reviewed"
        RESOLVED = "resolved", "Resolved"

    question = models.TextField(max_length=1000)
    detected_language = models.CharField(max_length=2, choices=LanguageChoices.choices)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="unanswered_questions",
    )
    matching_attempts = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    review_notes = models.TextField(blank=True)
    resolved_faq = models.ForeignKey(
        "faq.FAQ",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_questions",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="unanswered_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        permissions = [("review_unansweredquestion", "Can review unanswered questions")]
        indexes = [
            models.Index(fields=("status", "-created_at"), name="unanswered_status_idx"),
            models.Index(fields=("detected_language",), name="unanswered_language_idx"),
        ]

    def __str__(self) -> str:
        return self.question[:80]


class ChatFeedback(models.Model):
    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="feedback",
        limit_choices_to={"sender": ChatMessage.Sender.BOT},
    )
    helpful = models.BooleanField()
    comment = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Feedback for message {self.message_id}: {'Helpful' if self.helpful else 'Not helpful'}"
