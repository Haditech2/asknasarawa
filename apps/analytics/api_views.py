from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import CanViewAnalytics
from .services import analytics_snapshot


class AnalyticsAPIView(APIView):
    permission_classes = (CanViewAnalytics,)

    def get(self, request):
        try:
            days = int(request.query_params.get("days", "30"))
        except (TypeError, ValueError):
            return Response({"error": "days must be a whole number."}, status=400)
        if not 1 <= days <= 366:
            return Response({"error": "days must be between 1 and 366."}, status=400)
        return Response(analytics_snapshot(days))
