from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import FAQ, FAQCategory


class FAQAdminForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = "__all__"
        widgets = {
            "answer_en": forms.Textarea(attrs={"rows": 8}),
            "answer_ha": forms.Textarea(attrs={"rows": 8}),
            "keywords_en": forms.Textarea(attrs={"rows": 3}),
            "keywords_ha": forms.Textarea(attrs={"rows": 3}),
            "alternative_questions_en": forms.Textarea(attrs={"rows": 4}),
            "alternative_questions_ha": forms.Textarea(attrs={"rows": 4}),
        }


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_ha", "display_order", "is_active", "created_at")
    list_editable = ("display_order", "is_active")
    search_fields = ("name_en", "name_ha", "description_en", "description_ha")
    prepopulated_fields = {"slug": ("name_en",)}
    ordering = ("display_order", "name_en")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    form = FAQAdminForm
    list_display = (
        "question_en_short",
        "category",
        "status",
        "verification_status",
        "is_featured",
        "view_count",
        "updated_at",
    )
    list_filter = ("status", "verification_status", "category", "is_featured", "updated_at")
    search_fields = (
        "question_en",
        "question_ha",
        "answer_en",
        "answer_ha",
        "source_name",
    )
    autocomplete_fields = ("category", "created_by", "updated_by")
    readonly_fields = ("view_count", "created_at", "updated_at", "created_by", "updated_by")
    list_select_related = ("category", "created_by")
    actions = ("publish_selected", "unpublish_selected")
    fieldsets = (
        ("Classification", {"fields": ("category", "status", "is_featured")}),
        ("English content", {"fields": ("question_en", "answer_en", "keywords_en", "alternative_questions_en")}),
        ("Hausa content", {"fields": ("question_ha", "answer_ha", "keywords_ha", "alternative_questions_ha")}),
        ("Accuracy and source", {"fields": ("verification_status", "source_name", "source_url", "last_verified_at")}),
        ("Audit", {"fields": ("created_by", "updated_by", "created_at", "updated_at", "view_count"), "classes": ("collapse",)}),
    )

    @admin.display(description="English question", ordering="question_en")
    def question_en_short(self, obj):
        return obj.question_en[:90] or "—"

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if not request.user.has_perm("faq.publish_faq"):
            fields.append("status")
        return fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        if not request.user.has_perm("faq.publish_faq"):
            if change:
                obj.status = FAQ.objects.only("status").get(pk=obj.pk).status
            else:
                obj.status = FAQ.Status.DRAFT
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm("faq.publish_faq"):
            actions.pop("publish_selected", None)
            actions.pop("unpublish_selected", None)
        return actions

    @admin.action(description="Publish selected FAQs")
    def publish_selected(self, request, queryset):
        if not request.user.has_perm("faq.publish_faq"):
            self.message_user(request, "You do not have publishing permission.", messages.ERROR)
            return
        published = 0
        for faq in queryset:
            faq.status = FAQ.Status.PUBLISHED
            try:
                faq.full_clean()
            except ValidationError as exc:
                self.message_user(request, f"Skipped “{faq}”: {exc}", messages.WARNING)
                continue
            faq.updated_by = request.user
            faq.save(update_fields=("status", "updated_by", "updated_at"))
            published += 1
        self.message_user(request, f"Published {published} FAQ(s).", messages.SUCCESS)

    @admin.action(description="Return selected FAQs to draft")
    def unpublish_selected(self, request, queryset):
        if request.user.has_perm("faq.publish_faq"):
            count = queryset.update(status=FAQ.Status.DRAFT, updated_by=request.user)
            self.message_user(request, f"Unpublished {count} FAQ(s).", messages.SUCCESS)
