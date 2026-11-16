"""Role and permission provisioning for government administrators."""
from __future__ import annotations

from collections.abc import Iterable

from django.contrib.auth.models import Group, Permission, User
from django.db import transaction

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "FAQ Manager": {
        "faq.add_faqcategory",
        "faq.change_faqcategory",
        "faq.delete_faqcategory",
        "faq.view_faqcategory",
        "faq.add_faq",
        "faq.change_faq",
        "faq.delete_faq",
        "faq.view_faq",
        "faq.publish_faq",
        "chatbot.view_unansweredquestion",
        "chatbot.change_unansweredquestion",
        "chatbot.review_unansweredquestion",
        "chatbot.view_conversation",
        "chatbot.view_chatmessage",
        "chatbot.view_conversation_details",
        "analytics.view_chatbotanalytics",
        "analytics.view_analytics_dashboard",
    },
    "Content Editor": {
        "faq.add_faqcategory",
        "faq.change_faqcategory",
        "faq.view_faqcategory",
        "faq.add_faq",
        "faq.change_faq",
        "faq.view_faq",
    },
    "Analytics Viewer": {
        "analytics.view_chatbotanalytics",
        "analytics.view_analytics_dashboard",
        "chatbot.view_conversation",
        "chatbot.view_chatmessage",
        "chatbot.view_unansweredquestion",
        "chatbot.view_conversation_details",
    },
}

PROJECT_APP_LABELS = {"accounts", "faq", "chatbot", "analytics", "core", "auth"}


def _permissions_from_labels(labels: Iterable[str]) -> list[Permission]:
    permissions: list[Permission] = []
    for label in labels:
        try:
            app_label, codename = label.split(".", 1)
        except ValueError:
            continue
        permission = Permission.objects.filter(
            content_type__app_label=app_label,
            codename=codename,
        ).first()
        if permission:
            permissions.append(permission)
    return permissions


@transaction.atomic
def ensure_default_roles() -> dict[str, Group]:
    """Create/update the four supported administrator roles idempotently."""
    groups: dict[str, Group] = {}

    for role_name, labels in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        group.permissions.set(_permissions_from_labels(labels))
        groups[role_name] = group

    super_group, _ = Group.objects.get_or_create(name="Super Administrator")
    super_group.permissions.set(
        Permission.objects.filter(content_type__app_label__in=PROJECT_APP_LABELS)
    )
    groups["Super Administrator"] = super_group
    return groups


@transaction.atomic
def assign_role(user: User, role_name: str) -> None:
    groups = ensure_default_roles()
    if role_name not in groups:
        raise ValueError(f"Unknown role: {role_name}")
    user.groups.remove(*groups.values())
    user.groups.add(groups[role_name])
    if role_name == "Super Administrator":
        user.is_staff = True
        user.save(update_fields=["is_staff"])
