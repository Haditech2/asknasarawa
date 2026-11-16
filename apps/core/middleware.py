from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    """Add a conservative CSP and browser privacy headers.

    Bootstrap, Bootstrap Icons and Chart.js are loaded from jsDelivr. Deployments
    that self-host those assets can remove the CDN origin from this policy.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        script_policy = (
            "script-src 'self' 'unsafe-inline'"
            if request.path.startswith("/admin/")
            else "script-src 'self' https://cdn.jsdelivr.net"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "; ".join(
                [
                    "default-src 'self'",
                    script_policy,
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                    "font-src 'self' https://cdn.jsdelivr.net data:",
                    "img-src 'self' data:",
                    "connect-src 'self'",
                    "frame-ancestors 'none'",
                    "base-uri 'self'",
                    "form-action 'self'",
                ]
            ),
        )
        response.headers.setdefault("Permissions-Policy", "camera=(), geolocation=(), microphone=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        return response
