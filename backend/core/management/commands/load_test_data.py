from django.core.management.base import BaseCommand
from core.models import Country, VisaFee

class Command(BaseCommand):
    help = 'Loads test data for visa fees'

    def handle(self, *args, **kwargs):
        # Создаем тестовую страну
        country, created = Country.objects.get_or_create(
            name="USA",
            defaults={
                'region': 'North America',
                'visa_requirements': 'Valid passport, application form, photo',
                'processing_time': 15
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created country: {country.name}'))
        
        # Создаем тестовые данные о стоимости визы
        visa_fee, created = VisaFee.objects.get_or_create(
            country=country,
            visa_type='tourist',
            defaults={
                'consular_fee': 160.00,
                'service_fee': 30.00
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created visa fee for {country.name} - {visa_fee.visa_type}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Visa fee already exists for {country.name} - {visa_fee.visa_type}')) 