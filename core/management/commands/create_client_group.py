from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Creates or updates the "Client" user group with restricted model permissions.'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name='Client')

        # Target permissions:
        # QuoteRequest: view, change
        # Service: view, add, change, delete
        # GalleryImage: view, add, change, delete
        target_perms = [
            ('core', 'quoterequest', 'view_quoterequest'),
            ('core', 'quoterequest', 'change_quoterequest'),
            ('core', 'service', 'view_service'),
            ('core', 'service', 'add_service'),
            ('core', 'service', 'change_service'),
            ('core', 'service', 'delete_service'),
            ('core', 'galleryimage', 'view_galleryimage'),
            ('core', 'galleryimage', 'add_galleryimage'),
            ('core', 'galleryimage', 'change_galleryimage'),
            ('core', 'galleryimage', 'delete_galleryimage'),
        ]

        perms = []
        for app_label, model, codename in target_perms:
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model)
                perm = Permission.objects.get(content_type=ct, codename=codename)
                perms.append(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                perm = Permission.objects.filter(codename=codename, content_type__app_label=app_label).first()
                if perm:
                    perms.append(perm)

        group.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS(
            f'Successfully configured "Client" group with {len(perms)} permissions.'
        ))

