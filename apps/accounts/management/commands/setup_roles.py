from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services import assign_role, ensure_default_roles


class Command(BaseCommand):
    help = "Create the default administrator groups and optionally assign a user."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--username", help="Existing username to receive a role.")
        parser.add_argument(
            "--role",
            choices=[
                "Super Administrator",
                "FAQ Manager",
                "Content Editor",
                "Analytics Viewer",
            ],
            default="FAQ Manager",
        )

    def handle(self, *args, **options) -> None:
        groups = ensure_default_roles()
        self.stdout.write(self.style.SUCCESS(f"Provisioned {len(groups)} administrator roles."))
        if options["username"]:
            User = get_user_model()
            try:
                user = User.objects.get(username=options["username"])
            except User.DoesNotExist as exc:
                raise CommandError("The specified user does not exist.") from exc
            assign_role(user, options["role"])
            self.stdout.write(
                self.style.SUCCESS(f"Assigned {options['role']} to {user.get_username()}.")
            )
