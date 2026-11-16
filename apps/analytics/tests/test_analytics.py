from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.services import assign_role, ensure_default_roles
from apps.analytics.services import analytics_snapshot, record_event
from apps.chatbot.models import ChatMessage, Conversation


class AnalyticsTests(TestCase):
    def setUp(self):
        ensure_default_roles()
        self.user = get_user_model().objects.create_user("analyst", password="strong-test-password")

    def test_analytics_api_requires_permission(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("api-analytics"))
        self.assertEqual(response.status_code, 403)

    def test_analytics_viewer_can_access_aggregates(self):
        assign_role(self.user, "Analytics Viewer")
        self.client.force_login(self.user)
        response = self.client.get(reverse("api-analytics"), {"days": 30})
        self.assertEqual(response.status_code, 200)
        self.assertIn("totals", response.json())

    def test_snapshot_counts_questions_and_languages(self):
        conversation = Conversation.objects.create(session_id="test-session", preferred_language="ha")
        ChatMessage.objects.create(
            conversation=conversation,
            sender=ChatMessage.Sender.USER,
            message="Tambaya",
            language="ha",
        )
        snapshot = analytics_snapshot(30)
        self.assertEqual(snapshot["totals"]["questions"], 1)
        self.assertEqual(snapshot["language_usage"][0]["language"], "ha")

    def test_raw_search_text_is_not_needed_for_search_analytics(self):
        record_event("faq_search", language="en", metadata={"query_length": 12, "result_count": 2})
        self.assertEqual(analytics_snapshot(30)["totals"]["searches"], 1)
