from django.urls import path

from . import api_views

urlpatterns = [
    path("message/", api_views.ChatMessageAPIView.as_view(), name="api-chat-message"),
    path("history/", api_views.ChatHistoryAPIView.as_view(), name="api-chat-history"),
    path("feedback/", api_views.ChatFeedbackAPIView.as_view(), name="api-chat-feedback"),
    path("clear/", api_views.ChatClearAPIView.as_view(), name="api-chat-clear"),
]
