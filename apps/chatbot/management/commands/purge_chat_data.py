from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.analytics.models import ChatbotAnalytics
from apps.chatbot.models import Conversation, UnansweredQuestion


class Command(BaseCommand):
    help = "Delete expired conversation and unanswered-question data according to retention policy."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=settings.CHAT_DATA_RETENTION_DAYS,
            help="Conversation/unanswered retention in days.",
        )
        parser.add_argument(
            "--analytics-days",
            type=int,
            default=730,
            help="Analytics event retention in days.",
        )
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        days = options["days"]
        analytics_days = options["analytics_days"]
        if days < 1 or analytics_days < 1:
            raise CommandError("Retention periods must be at least one day.")
        chat_cutoff = timezone.now() - timedelta(days=days)
        analytics_cutoff = timezone.now() - timedelta(days=analytics_days)

        conversations = Conversation.objects.filter(updated_at__lt=chat_cutoff)
        unanswered = UnansweredQuestion.objects.filter(created_at__lt=chat_cutoff)
        analytics = ChatbotAnalytics.objects.filter(created_at__lt=analytics_cutoff)
        counts = {
            "conversations": conversations.count(),
            "unanswered_questions": unanswered.count(),
            "analytics_events": analytics.count(),
        }
        if options["dry_run"]:
            self.stdout.write(f"Dry run: {counts}")
            return
        # Unanswered questions are deleted explicitly because their conversation
        # foreign key is SET_NULL to support short-term editorial review.
        unanswered.delete()
        conversations.delete()
        analytics.delete()
        self.stdout.write(self.style.SUCCESS(f"Purged expired data: {counts}"))
