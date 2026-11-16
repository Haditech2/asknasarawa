from django.db import connections, models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from apps.faq.models import FAQ, FAQCategory


@require_GET
def home(request):
    categories = FAQCategory.objects.active().annotate(
        published_count=models.Count(
            "faqs",
            filter=models.Q(faqs__status=FAQ.Status.PUBLISHED),
        )
    )
    featured_faqs = FAQ.objects.visible().filter(is_featured=True)[:6]
    if not featured_faqs:
        featured_faqs = FAQ.objects.visible()[:6]
    return render(
        request,
        "home.html",
        {"categories": categories, "featured_faqs": featured_faqs},
    )


@require_GET
@cache_page(30)
def health(request):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unhealthy", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


@require_GET
def robots(request):
    return HttpResponse("User-agent: *\nAllow: /\n", content_type="text/plain")
