import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.chatbot.models import ChatFeedback, ChatMessage, Conversation, UnansweredQuestion
from apps.core.text import detect_language, normalize_text
from apps.faq.models import FAQ, FAQCategory


class ChatbotTestCase(TestCase):
    def setUp(self):
        self.category = FAQCategory.objects.create(
            name_en="Education Services",
            name_ha="Ayyukan Ilimi",
            slug="education",
        )
        self.faq = FAQ.objects.create(
            category=self.category,
            question_en="How can I apply for a scholarship?",
            answer_en="Apply through the current official scholarship notice.",
            question_ha="Ta yaya zan nemi tallafin karatu?",
            answer_ha="Ka nema ta sanarwar tallafin karatu ta hukuma.",
            keywords_en=["scholarship", "bursary", "student grant"],
            keywords_ha=["tallafin karatu", "bursary", "dalibi"],
            alternative_questions_en=["Where is the bursary application?"],
            alternative_questions_ha=["A ina zan nemi bursary?"],
            status=FAQ.Status.PUBLISHED,
            verification_status=FAQ.VerificationStatus.VERIFIED,
            source_name="Official portal",
            source_url="https://example.gov.test/scholarship",
        )

    def post_message(self, message, language="auto", client=None):
        return (client or self.client).post(
            reverse("api-chat-message"),
            data=json.dumps({"message": message, "preferred_language": language}),
            content_type="application/json",
        )

    def test_normalizes_hausa_characters(self):
        self.assertEqual(normalize_text("Kuɗin tallafi"), "kudi tallafi")

    def test_detects_hausa(self):
        self.assertEqual(detect_language("Yaya zan nemi tallafin karatu?")[0], "ha")

    def test_matches_english_question(self):
        response = self.post_message("Where is the scholarship application?", "en")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["matched"])
        self.assertEqual(data["faq_id"], self.faq.pk)
        self.assertEqual(data["answer"], self.faq.answer_en)

    def test_matches_hausa_question_and_returns_hausa(self):
        response = self.post_message("Yaya zan samu tallafin karatu?", "ha")
        data = response.json()
        self.assertTrue(data["matched"])
        self.assertEqual(data["language"], "ha")
        self.assertEqual(data["answer"], self.faq.answer_ha)
        self.assertEqual(data["answer_en"], self.faq.answer_en)
        self.assertEqual(data["answer_ha"], self.faq.answer_ha)

    def test_hausa_question_with_english_preference_returns_english(self):
        response = self.post_message("Yaya zan samu tallafin karatu?", "en")
        data = response.json()
        self.assertTrue(data["matched"])
        self.assertEqual(data["language"], "en")
        self.assertEqual(data["answer"], self.faq.answer_en)

    def test_hausa_question_requesting_english_in_query_returns_english(self):
        response = self.post_message("Yaya zan samu tallafin karatu da turanci?", "auto")
        data = response.json()
        self.assertTrue(data["matched"])
        self.assertEqual(data["language"], "en")
        self.assertEqual(data["answer"], self.faq.answer_en)

    def test_selected_language_is_preserved(self):
        response = self.post_message("How can I apply for a scholarship?", "ha")
        self.assertEqual(response.json()["answer"], self.faq.answer_ha)

    def test_unanswered_question_is_recorded_without_fabrication(self):
        response = self.post_message("What is the orbital ferry timetable?", "en")
        data = response.json()
        self.assertFalse(data["matched"])
        self.assertIsNone(data["faq_id"])
        self.assertEqual(UnansweredQuestion.objects.count(), 1)
        self.assertIn("will not guess", data["answer"])

    def test_language_switch_updates_same_conversation(self):
        first = self.post_message("How can I apply for a scholarship?", "en").json()
        second = self.post_message("Yaya zan nemi tallafin karatu?", "ha").json()
        self.assertEqual(first["conversation_id"], second["conversation_id"])
        conversation = Conversation.objects.get(pk=first["conversation_id"])
        self.assertEqual(conversation.preferred_language, "ha")

    def test_history_is_limited_to_current_session(self):
        self.post_message("How can I apply for a scholarship?", "en")
        response = self.client.get(reverse("api-chat-history"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["messages"]), 2)

        other_client = Client()
        other_response = other_client.get(reverse("api-chat-history"))
        self.assertEqual(other_response.json()["messages"], [])

    def test_invalid_input_is_rejected(self):
        response = self.post_message(" ", "en")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_sensitive_credentials_are_redacted_before_storage(self):
        response = self.post_message("My BVN is 12345678901 and I need a scholarship", "en")
        self.assertTrue(response.json()["sensitive_data_redacted"])
        stored = ChatMessage.objects.filter(sender=ChatMessage.Sender.USER).get()
        self.assertNotIn("12345678901", stored.message)
        self.assertIn("[REDACTED]", stored.message)

    def test_feedback_is_saved_for_current_session_message(self):
        message_data = self.post_message("How can I apply for a scholarship?", "en").json()
        response = self.client.post(
            reverse("api-chat-feedback"),
            data=json.dumps({"message_id": message_data["message_id"], "helpful": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ChatFeedback.objects.get().helpful)

    def test_clear_conversation_starts_new_session_conversation(self):
        first_id = self.post_message("How can I apply for a scholarship?", "en").json()["conversation_id"]
        response = self.client.post(reverse("api-chat-clear"))
        self.assertEqual(response.status_code, 200)
        second_id = self.post_message("How can I apply for a scholarship?", "en").json()["conversation_id"]
        self.assertNotEqual(first_id, second_id)
        self.assertFalse(Conversation.objects.get(pk=first_id).is_active)

    def test_public_post_endpoint_enforces_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.get(reverse("chatbot:chat"))
        denied = self.post_message("How do I apply for a scholarship?", "en", csrf_client)
        self.assertEqual(denied.status_code, 403)
        token = csrf_client.cookies["csrftoken"].value
        allowed = csrf_client.post(
            reverse("api-chat-message"),
            data=json.dumps({"message": "How do I apply for a scholarship?", "preferred_language": "en"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(allowed.status_code, 200)
