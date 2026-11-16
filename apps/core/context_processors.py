from django.conf import settings


def site_context(request):
    requested_language = request.GET.get("language")
    if requested_language in {"en", "ha"}:
        request.session["ui_language"] = requested_language
    ui_language = request.session.get("ui_language", "en")
    return {
        "SITE_NAME": settings.SITE_NAME,
        "OFFICIAL_ENQUIRY_EMAIL": settings.OFFICIAL_ENQUIRY_EMAIL,
        "OFFICIAL_ENQUIRY_URL": settings.OFFICIAL_ENQUIRY_URL,
        "UI_LANGUAGE": ui_language if ui_language in {"en", "ha"} else "en",
    }
