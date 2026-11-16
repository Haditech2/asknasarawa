from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from apps.analytics.services import record_event
from apps.core.text import detect_language

from .models import FAQ, FAQCategory
from .services import related_faqs, search_faqs


@require_GET
@ensure_csrf_cookie
def faq_list(request):
    query = request.GET.get("q", "").strip()[:500]
    language = request.GET.get("language", "en")
    if language not in {"en", "ha"}:
        language = detect_language(query, "en")[0] if query else "en"
    category = request.GET.get("category", "")
    if query:
        results = search_faqs(query, language=language, category=category or None)
        faqs = [result.faq for result in results]
        record_event(
            "faq_search",
            language=language,
            metadata={"query_length": len(query), "result_count": len(faqs)},
        )
    else:
        queryset = FAQ.objects.visible()
        if category:
            queryset = queryset.filter(category__slug=category)
        faqs = list(queryset[:50])
    return render(
        request,
        "faq/faq_list.html",
        {
            "faqs": faqs,
            "categories": FAQCategory.objects.active(),
            "query": query,
            "selected_category": category,
            "language": language,
        },
    )


@require_GET
def faq_detail(request, pk: int):
    faq = get_object_or_404(FAQ.objects.visible(), pk=pk)
    language = request.GET.get("language", "en")
    language = language if language in {"en", "ha"} else "en"
    FAQ.objects.filter(pk=faq.pk).update(view_count=F("view_count") + 1)
    record_event("faq_view", category=faq.category, language=language, metadata={"faq_id": faq.pk})
    return render(
        request,
        "faq/faq_detail.html",
        {"faq": faq, "related_faqs": related_faqs(faq, language), "language": language},
    )
