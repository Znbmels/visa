from django.core.management.base import BaseCommand
from core.models import Country

class Command(BaseCommand):
    help = 'Fixes country regions: заменяет America на North America'

    def handle(self, *args, **options):
        updated = 0
        for country in Country.objects.filter(region='America'):
            country.region = 'North America'
            country.save()
            updated += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} countries from America to North America')) 