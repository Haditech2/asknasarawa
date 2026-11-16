from django.db.models import Count, Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.analytics.services import record_event
from apps.core.text import detect_language

from .models import FAQ, FAQCategory
from .serializers import FAQCategorySerializer, FAQDetailSerializer, FAQSearchResultSerializer
from .services import search_faqs


class FAQListAPIView(generics.ListAPIView):
    serializer_class = FAQDetailSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "faq_search"

    def get_queryset(self):
        queryset = FAQ.objects.visible()
        category = self.request.query_params.get("category")
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=int(category))
            else:
                queryset = queryset.filter(category__slug=category)
        if self.request.query_params.get("featured") in {"1", "true", "True"}:
            queryset = queryset.filter(is_featured=True)
        return queryset.order_by("category__display_order", "question_en")


class FAQCategoryListAPIView(generics.ListAPIView):
    serializer_class = FAQCategorySerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    def get_queryset(self):
        return FAQCategory.objects.active().annotate(
            faq_count=Count("faqs", filter=Q(faqs__status=FAQ.Status.PUBLISHED))
        )


class FAQSearchAPIView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "faq_search"

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"query": "", "count": 0, "results": []})
        if len(query) > 500:
            return Response({"error": "Search text must be 500 characters or fewer."}, status=400)
        requested = request.query_params.get("language", "auto")
        language = requested if requested in {"en", "ha"} else detect_language(query)[0]
        category = request.query_params.get("category") or None
        results = search_faqs(query, language=language, category=category, limit=20)
        record_event(
            "faq_search",
            language=language,
            metadata={"query_length": len(query), "result_count": len(results)},
        )
        serializer = FAQSearchResultSerializer(
            [{"faq": result.faq, "score": result.score, "matched_on": result.matched_on} for result in results],
            many=True,
            context={"request": request},
        )
        return Response(
            {"query": query, "language": language, "count": len(results), "results": serializer.data}
        )
