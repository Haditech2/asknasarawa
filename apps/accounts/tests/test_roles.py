from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from apps.accounts.services import assign_role, ensure_default_roles


class RoleTests(TestCase):
    def setUp(self):
        self.groups = ensure_default_roles()
        self.user = get_user_model().objects.create_user("editor", password="strong-test-password")

    def test_all_required_roles_are_created(self):
        self.assertEqual(
            set(self.groups),
            {"Super Administrator", "FAQ Manager", "Content Editor", "Analytics Viewer"},
        )

    def test_content_editor_cannot_publish(self):
        assign_role(self.user, "Content Editor")
        self.assertTrue(self.user.has_perm("faq.change_faq"))
        self.assertFalse(self.user.has_perm("faq.publish_faq"))

    def test_faq_manager_can_publish_and_review(self):
        assign_role(self.user, "FAQ Manager")
        self.assertTrue(self.user.has_perm("faq.publish_faq"))
        self.assertTrue(self.user.has_perm("chatbot.review_unansweredquestion"))

    def test_assigning_role_replaces_previous_project_role(self):
        assign_role(self.user, "Content Editor")
        assign_role(self.user, "Analytics Viewer")
        self.assertEqual(list(self.user.groups.values_list("name", flat=True)), ["Analytics Viewer"])
