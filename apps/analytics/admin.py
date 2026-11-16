from django.contrib import admin

from .models import ChatbotAnalytics


@admin.register(ChatbotAnalytics)
class ChatbotAnalyticsAdmin(admin.ModelAdmin):
    list_display = ("event_type", "language", "category", "created_at")
    list_filter = ("event_type", "language", "category", "created_at")
    search_fields = ("metadata",)
    readonly_fields = ("event_type", "language", "category", "metadata", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
