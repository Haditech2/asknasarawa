from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

admin.site.site_header = "Tambayi Nasarawa Administration"
admin.site.site_title = "Tambayi Nasarawa Admin"
admin.site.index_title = "Government information management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/faq/", include("apps.faq.api_urls")),
    path("api/chat/", include("apps.chatbot.api_urls")),
    path("api/analytics/", include("apps.analytics.api_urls")),
    path("faqs/", include("apps.faq.urls")),
    path("chat/", include("apps.chatbot.urls")),
    path("dashboard/", include("apps.analytics.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
