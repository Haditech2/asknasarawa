from django.utils.html import strip_tags
from rest_framework import serializers

from .models import ChatFeedback, ChatMessage


class ChatMessageInputSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, trim_whitespace=True)
    preferred_language = serializers.ChoiceField(
        choices=("auto", "en", "ha"),
        default="auto",
    )
    category = serializers.CharField(max_length=140, required=False, allow_blank=True)

    def validate_message(self, value):
        cleaned = " ".join(strip_tags(value).split())
        if not cleaned:
            raise serializers.ValidationError("Enter a question.")
        if len(cleaned) < 2:
            raise serializers.ValidationError("The question is too short.")
        return cleaned


class ChatMessageSerializer(serializers.ModelSerializer):
    faq_id = serializers.IntegerField(source="matched_faq_id", allow_null=True, read_only=True)
    answer_en = serializers.CharField(source="matched_faq.answer_en", allow_null=True, read_only=True)
    answer_ha = serializers.CharField(source="matched_faq.answer_ha", allow_null=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "sender",
            "message",
            "language",
            "faq_id",
            "answer_en",
            "answer_ha",
            "confidence_score",
            "created_at",
        )


class FeedbackInputSerializer(serializers.Serializer):
    message_id = serializers.IntegerField(min_value=1)
    helpful = serializers.BooleanField()
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True, trim_whitespace=True)

    def validate_comment(self, value):
        return " ".join(strip_tags(value).split())


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatFeedback
        fields = ("message_id", "helpful", "comment", "created_at", "updated_at")
