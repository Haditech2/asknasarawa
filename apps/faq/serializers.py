from rest_framework import serializers

from .models import FAQ, FAQCategory


def requested_language(context) -> str:
    request = context.get("request")
    language = request.query_params.get("language", "en") if request else "en"
    return language if language in {"en", "ha"} else "en"


class FAQCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    faq_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = FAQCategory
        fields = (
            "id",
            "slug",
            "name",
            "description",
            "name_en",
            "name_ha",
            "description_en",
            "description_ha",
            "icon",
            "faq_count",
        )

    def get_name(self, obj):
        return obj.localized_name(requested_language(self.context))

    def get_description(self, obj):
        return obj.localized_description(requested_language(self.context))


class FAQSummarySerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    category = FAQCategorySerializer(read_only=True)

    class Meta:
        model = FAQ
        fields = (
            "id",
            "question",
            "answer",
            "category",
            "verification_status",
            "source_name",
            "source_url",
            "last_verified_at",
            "is_featured",
            "updated_at",
        )

    def get_question(self, obj):
        return obj.localized_question(requested_language(self.context))

    def get_answer(self, obj):
        return obj.localized_answer(requested_language(self.context))


class FAQDetailSerializer(FAQSummarySerializer):
    class Meta(FAQSummarySerializer.Meta):
        fields = FAQSummarySerializer.Meta.fields + (
            "question_en",
            "answer_en",
            "question_ha",
            "answer_ha",
            "keywords_en",
            "keywords_ha",
            "alternative_questions_en",
            "alternative_questions_ha",
        )


class FAQSearchResultSerializer(serializers.Serializer):
    score = serializers.FloatField()
    matched_on = serializers.CharField()
    faq = FAQSummarySerializer()
