from django.urls import path

from . import api_views

urlpatterns = [
    path("", api_views.FAQListAPIView.as_view(), name="api-faq-list"),
    path("categories/", api_views.FAQCategoryListAPIView.as_view(), name="api-faq-categories"),
    path("search/", api_views.FAQSearchAPIView.as_view(), name="api-faq-search"),
]
