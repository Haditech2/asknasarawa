from django.db.models import Count, Q
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from apps.faq.models import FAQ, FAQCategory


@require_GET
@ensure_csrf_cookie
def chat(request):
    categories = FAQCategory.objects.active().annotate(
        faq_count=Count("faqs", filter=Q(faqs__status=FAQ.Status.PUBLISHED))
    )
    suggestions = FAQ.objects.visible().filter(is_featured=True)[:6]
    if not suggestions:
        suggestions = FAQ.objects.visible()[:6]
    return render(
        request,
        "chatbot/chat.html",
        {"categories": categories, "suggestions": suggestions},
    )
