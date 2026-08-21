import sys
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Skip during build/management commands
        skip_commands = {'collectstatic', 'migrate', 'makemigrations', 'test', 'help', 'check'}
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        try:
            from .models import Destination
            from properties.models import Property
            if Destination.objects.count() == 0 or Property.objects.count() == 0:
                print("Auto-seeding LocalNest production database on application startup...")
                import seed_data
                seed_data.seed()
                print("Auto-seeding completed successfully!")
        except Exception as e:
            # Ignore errors if tables do not exist yet before migration
            pass
