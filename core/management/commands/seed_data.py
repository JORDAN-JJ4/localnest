from django.core.management.base import BaseCommand
import seed_data

class Command(BaseCommand):
    help = 'Idempotently seeds the LocalNest database with initial content, hosts, properties, and media images.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting LocalNest data seeding process..."))
        seed_data.seed()
        self.stdout.write(self.style.SUCCESS("Successfully completed LocalNest data seeding!"))
