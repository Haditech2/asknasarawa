import logging

from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_migrate, dispatch_uid="accounts.ensure_default_roles")
def provision_roles(**kwargs) -> None:
    try:
        from .services import ensure_default_roles

        ensure_default_roles()
    except Exception:
        # Migrations must not become unrecoverable if permissions are still being
        # created. The setup_roles command can be run explicitly afterwards.
        logger.exception("Unable to provision administrator roles during migration")
