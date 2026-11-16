from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.text import slugify


def validate_string_list(value: Any) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValidationError("Enter a JSON list containing only text values.")
    if any(len(item.strip()) > 300 for item in value):
        raise ValidationError("Each list item must be 300 characters or fewer.")


class FAQCategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class FAQCategory(models.Model):
    name_en = models.CharField(max_length=120, verbose_name="English name")
    name_ha = models.CharField(max_length=120, verbose_name="Hausa name")
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description_en = models.TextField(blank=True, verbose_name="English description")
    description_ha = models.TextField(blank=True, verbose_name="Hausa description")
    icon = models.CharField(
        max_length=60,
        default="bi-grid",
        validators=[RegexValidator(r"^bi-[a-z0-9-]+$", "Use a Bootstrap Icon class such as bi-book.")],
        help_text="Bootstrap Icon class, for example bi-book.",
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FAQCategoryQuerySet.as_manager()

    class Meta:
        ordering = ("display_order", "name_en")
        verbose_name = "FAQ category"
        verbose_name_plural = "FAQ categories"
        constraints = [
            models.UniqueConstraint(Lower("name_en"), name="unique_category_name_en_ci"),
            models.UniqueConstraint(Lower("name_ha"), name="unique_category_name_ha_ci"),
        ]
        indexes = [models.Index(fields=("is_active", "display_order"), name="faqcat_active_order_idx")]

    def __str__(self) -> str:
        return self.name_en

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.name_en) or "category"
            slug = base
            counter = 2
            while FAQCategory.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def localized_name(self, language: str) -> str:
        return self.name_ha if language == "ha" else self.name_en

    def localized_description(self, language: str) -> str:
        return self.description_ha if language == "ha" else self.description_en


class FAQQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=FAQ.Status.PUBLISHED, category__is_active=True)

    def visible(self):
        return self.published().select_related("category", "created_by")


class FAQ(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    class VerificationStatus(models.TextChoices):
        VERIFIED = "verified", "Verified from official source"
        AWAITING = "awaiting", "Awaiting official confirmation"

    category = models.ForeignKey(FAQCategory, on_delete=models.PROTECT, related_name="faqs")
    question_en = models.CharField(max_length=500, blank=True, verbose_name="English question")
    answer_en = models.TextField(blank=True, verbose_name="English answer")
    question_ha = models.CharField(max_length=500, blank=True, verbose_name="Hausa question")
    answer_ha = models.TextField(blank=True, verbose_name="Hausa answer")
    keywords_en = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_string_list],
        help_text='JSON list, for example ["tax", "invoice"].',
    )
    keywords_ha = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_string_list],
        help_text='JSON list, for example ["haraji", "biyan kuɗi"].',
    )
    alternative_questions_en = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_string_list],
        help_text="Common alternative English phrasings as a JSON list.",
    )
    alternative_questions_ha = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_string_list],
        help_text="Common alternative Hausa phrasings as a JSON list.",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    verification_status = models.CharField(
        max_length=12,
        choices=VerificationStatus.choices,
        default=VerificationStatus.AWAITING,
    )
    source_name = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    last_verified_at = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveBigIntegerField(default=0, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faqs_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faqs_updated",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FAQQuerySet.as_manager()

    class Meta:
        ordering = ("category__display_order", "question_en")
        permissions = [
            ("publish_faq", "Can publish and unpublish FAQs"),
        ]
        indexes = [
            models.Index(fields=("status", "category"), name="faq_status_category_idx"),
            models.Index(fields=("is_featured", "status"), name="faq_featured_status_idx"),
            models.Index(fields=("-updated_at",), name="faq_updated_idx"),
        ]

    def __str__(self) -> str:
        return self.question_en or self.question_ha or f"FAQ {self.pk or 'draft'}"

    def clean(self) -> None:
        super().clean()
        for field_name in (
            "keywords_en",
            "keywords_ha",
            "alternative_questions_en",
            "alternative_questions_ha",
        ):
            validate_string_list(getattr(self, field_name))

        if self.status == self.Status.PUBLISHED:
            missing = [
                label
                for field, label in (
                    (self.question_en, "English question"),
                    (self.answer_en, "English answer"),
                    (self.question_ha, "Hausa question"),
                    (self.answer_ha, "Hausa answer"),
                )
                if not field.strip()
            ]
            if missing:
                raise ValidationError(
                    {"status": f"Published FAQs require: {', '.join(missing)}."}
                )
        if self.verification_status == self.VerificationStatus.VERIFIED and not self.source_url:
            raise ValidationError(
                {"source_url": "A verified FAQ must link to the official source used."}
            )

    def get_absolute_url(self) -> str:
        return reverse("faq:detail", kwargs={"pk": self.pk})

    def localized_question(self, language: str) -> str:
        return self.question_ha if language == "ha" else self.question_en

    def localized_answer(self, language: str) -> str:
        return self.answer_ha if language == "ha" else self.answer_en

    def localized_keywords(self, language: str) -> list[str]:
        return self.keywords_ha if language == "ha" else self.keywords_en

    def localized_alternatives(self, language: str) -> list[str]:
        return self.alternative_questions_ha if language == "ha" else self.alternative_questions_en
