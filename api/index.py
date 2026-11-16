import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

if os.getenv("VERCEL"):
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

from config.wsgi import application

app = application
