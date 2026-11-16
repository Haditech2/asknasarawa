from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from .services import analytics_snapshot


@login_required
@permission_required("analytics.view_analytics_dashboard", raise_exception=True)
def dashboard(request):
    return render(request, "dashboard/index.html", {"snapshot": analytics_snapshot(30)})
