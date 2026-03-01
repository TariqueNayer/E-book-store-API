from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Creates a superuser if one does not exist.'

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = os.environ.get('DJANGO_SU_USERNAME', 'Great_admin')
        email = os.environ.get('DJANGO_SU_EMAIL', 'Great_admin@123.org')
        password = os.environ.get('DJANGO_SU_PASSWORD', 'compassword123')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists. Skipping.'))