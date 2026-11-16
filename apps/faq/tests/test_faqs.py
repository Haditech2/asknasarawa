from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.faq.models import FAQ, FAQCategory
from apps.faq.services import search_faqs


class FAQTestMixin:
    def setUp(self):
        self.category = FAQCategory.objects.create(
            name_en="Education Services",
            name_ha="Ayyukan Ilimi",
            slug="education",
            icon="bi-mortarboard",
        )
        self.faq = FAQ.objects.create(
            category=self.category,
            question_en="How can I apply for a scholarship?",
            answer_en="Use the current official Scholarship Board application notice.",
            question_ha="Ta yaya zan nemi tallafin karatu?",
            answer_ha="Bi sanarwar neman tallafin karatu ta Hukumar a yanzu.",
            keywords_en=["scholarship", "bursary"],
            keywords_ha=["tallafin karatu", "bursary"],
            alternative_questions_en=["Where is the bursary form?"],
            alternative_questions_ha=["A ina fom din bursary yake?"],
            status=FAQ.Status.PUBLISHED,
            verification_status=FAQ.VerificationStatus.VERIFIED,
            source_name="Official scholarship portal",
            source_url="https://example.gov.test/scholarship",
        )


class FAQModelTests(FAQTestMixin, TestCase):
    def test_draft_can_be_saved_incompletely(self):
        draft = FAQ(category=self.category, question_en="Draft", status=FAQ.Status.DRAFT)
        draft.full_clean()

    def test_published_faq_requires_both_languages(self):
        faq = FAQ(
            category=self.category,
            question_en="English only",
            answer_en="Answer",
            status=FAQ.Status.PUBLISHED,
        )
        with self.assertRaises(ValidationError):
            faq.full_clean()

    def test_verified_faq_requires_source(self):
        self.faq.source_url = ""
        with self.assertRaises(ValidationError):
            self.faq.full_clean()

    def test_category_slug_is_generated(self):
        category = FAQCategory.objects.create(name_en="Tax and Revenue", name_ha="Haraji")
        self.assertEqual(category.slug, "tax-and-revenue")


class FAQSearchTests(FAQTestMixin, TestCase):
    def test_english_fuzzy_search(self):
        results = search_faqs("Where do I get the bursary application", language="en")
        self.assertEqual(results[0].faq, self.faq)

    def test_hausa_search(self):
        results = search_faqs("Yaya zan samu tallafin dalibi", language="ha")
        self.assertEqual(results[0].faq, self.faq)

    def test_api_returns_only_published_faqs(self):
        FAQ.objects.create(
            category=self.category,
            question_en="Unpublished",
            question_ha="Ba a wallafa ba",
            status=FAQ.Status.DRAFT,
        )
        response = self.client.get(reverse("api-faq-list"), {"language": "en"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_search_api_returns_localized_result(self):
        response = self.client.get(
            reverse("api-faq-search"),
            {"q": "tallafin karatu", "language": "ha"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["faq"]["question"], self.faq.question_ha)

    def test_search_rejects_overlong_input(self):
        response = self.client.get(reverse("api-faq-search"), {"q": "a" * 501})
        self.assertEqual(response.status_code, 400)
