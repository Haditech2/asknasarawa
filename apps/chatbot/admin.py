from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from apps.faq.models import FAQ, FAQCategory

from .models import ChatFeedback, ChatMessage, Conversation, UnansweredQuestion


class ConvertToFAQForm(forms.Form):
    category = forms.ModelChoiceField(queryset=FAQCategory.objects.none())
    question_en = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    answer_en = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 7}))
    question_ha = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    answer_ha = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 7}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = FAQCategory.objects.active()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("question_en") and not cleaned.get("question_ha"):
            raise forms.ValidationError("Enter the question in at least one language.")
        return cleaned


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    can_delete = False
    fields = ("sender", "language", "message", "matched_faq", "confidence_score", "created_at")
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("short_id", "preferred_language", "message_count", "is_active", "created_at", "updated_at")
    list_filter = ("preferred_language", "is_active", "created_at")
    search_fields = ("id", "session_id")
    readonly_fields = ("id", "session_id", "preferred_language", "user", "is_active", "created_at", "updated_at")
    inlines = (ChatMessageInline,)
    date_hierarchy = "created_at"

    @admin.display(description="Conversation")
    def short_id(self, obj):
        return str(obj.id)[:12]

    @admin.display(description="Messages")
    def message_count(self, obj):
        return obj.messages.count()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("chatbot.view_conversation_details")

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "language", "message_short", "matched_faq", "confidence_score", "created_at")
    list_filter = ("sender", "language", "created_at")
    search_fields = ("message", "conversation__id")
    readonly_fields = (
        "conversation",
        "sender",
        "message",
        "language",
        "matched_faq",
        "confidence_score",
        "response_time_ms",
        "created_at",
    )
    list_select_related = ("conversation", "matched_faq")

    @admin.display(description="Message")
    def message_short(self, obj):
        return obj.message[:100]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(UnansweredQuestion)
class UnansweredQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_short", "detected_language", "status", "convert_link", "created_at")
    list_filter = ("status", "detected_language", "created_at")
    search_fields = ("question", "review_notes")
    readonly_fields = ("question", "detected_language", "conversation", "matching_attempts", "created_at")
    autocomplete_fields = ("resolved_faq", "reviewed_by")
    actions = ("mark_reviewed",)
    date_hierarchy = "created_at"

    @admin.display(description="Question")
    def question_short(self, obj):
        return obj.question[:110]

    @admin.display(description="FAQ action")
    def convert_link(self, obj):
        if obj.status == UnansweredQuestion.Status.RESOLVED:
            return "Resolved"
        url = reverse("admin:chatbot_unansweredquestion_convert", args=(obj.pk,))
        return format_html('<a class="button" href="{}">Convert to FAQ</a>', url)

    @admin.action(description="Mark selected questions as reviewed")
    def mark_reviewed(self, request, queryset):
        if not request.user.has_perm("chatbot.review_unansweredquestion"):
            raise PermissionDenied
        count = queryset.exclude(status=UnansweredQuestion.Status.RESOLVED).update(
            status=UnansweredQuestion.Status.REVIEWED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"Marked {count} question(s) as reviewed.", messages.SUCCESS)

    def get_urls(self):
        return [
            path(
                "<path:object_id>/convert/",
                self.admin_site.admin_view(self.convert_to_faq),
                name="chatbot_unansweredquestion_convert",
            )
        ] + super().get_urls()

    def convert_to_faq(self, request, object_id):
        if not (
            request.user.has_perm("chatbot.review_unansweredquestion")
            and request.user.has_perm("faq.add_faq")
        ):
            raise PermissionDenied
        unanswered = get_object_or_404(UnansweredQuestion, pk=object_id)
        initial = {
            "question_ha" if unanswered.detected_language == "ha" else "question_en": unanswered.question
        }
        form = ConvertToFAQForm(request.POST or None, initial=initial)
        if request.method == "POST" and form.is_valid():
            faq = FAQ.objects.create(
                category=form.cleaned_data["category"],
                question_en=form.cleaned_data["question_en"],
                answer_en=form.cleaned_data["answer_en"],
                question_ha=form.cleaned_data["question_ha"],
                answer_ha=form.cleaned_data["answer_ha"],
                status=FAQ.Status.DRAFT,
                verification_status=FAQ.VerificationStatus.AWAITING,
                created_by=request.user,
                updated_by=request.user,
            )
            unanswered.status = UnansweredQuestion.Status.RESOLVED
            unanswered.resolved_faq = faq
            unanswered.reviewed_by = request.user
            unanswered.reviewed_at = timezone.now()
            unanswered.save(
                update_fields=("status", "resolved_faq", "reviewed_by", "reviewed_at")
            )
            self.message_user(
                request,
                "A draft FAQ was created. Complete both translations and verify its source before publishing.",
                messages.SUCCESS,
            )
            return redirect("admin:faq_faq_change", faq.pk)

        context = {
            **self.admin_site.each_context(request),
            "title": "Convert unanswered question to FAQ",
            "form": form,
            "unanswered": unanswered,
            "opts": self.model._meta,
        }
        return render(request, "admin/chatbot/unansweredquestion/convert.html", context)


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ("message", "helpful", "created_at")
    list_filter = ("helpful", "created_at")
    search_fields = ("comment", "message__message")
    readonly_fields = ("message", "helpful", "comment", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
