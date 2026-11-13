from django.core.management.base import BaseCommand
from core.models import Service


class Command(BaseCommand):
    help = 'Idempotently seeds initial moving services into the database.'

    def handle(self, *args, **options):
        initial_services = [
            {
                'title': 'Household Shifting',
                'description': 'Moving household goods and furniture within Tiruppur and on trips to Chennai, Madurai and nearby towns.',
                'order': 1,
                'is_active': True,
            },
            {
                'title': 'Office Relocation',
                'description': 'Moving office desks, equipment, and documents within Tiruppur and to Chennai and Madurai.',
                'order': 2,
                'is_active': True,
            },
            {
                'title': 'Two-Wheeler & Vehicle Transport',
                'description': 'Transport for two-wheelers and personal vehicles within Tiruppur and to Chennai and Madurai.',
                'order': 3,
                'is_active': True,
            },
        ]

        created_count = 0
        for item in initial_services:
            _, created = Service.objects.get_or_create(
                title=item['title'],
                defaults=item
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Services seeding complete. {created_count} added, {len(initial_services) - created_count} already existed.'
        ))

