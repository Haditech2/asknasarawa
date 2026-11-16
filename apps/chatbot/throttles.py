from rest_framework.throttling import SimpleRateThrottle


class ChatMessageThrottle(SimpleRateThrottle):
    scope = "chat"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return self.cache_format % {"scope": self.scope, "ident": f"user-{request.user.pk}"}
        session_key = request.session.session_key
        ident = session_key or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
