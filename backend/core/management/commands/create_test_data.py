from django.core.management.base import BaseCommand
from core.models import Country, VisaApplication, CustomUser
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Creates test data for visa applications'

    def handle(self, *args, **kwargs):
        # Create test countries if they don't exist
        countries = [
            {
                'name': 'United States',
                'region': 'North America',
                'visa_requirements': 'Valid passport, application form, photo',
                'processing_time': 30
            },
            {
                'name': 'United Kingdom',
                'region': 'Europe',
                'visa_requirements': 'Valid passport, application form, photo, bank statement',
                'processing_time': 15
            },
            {
                'name': 'Schengen Area',
                'region': 'Europe',
                'visa_requirements': 'Valid passport, application form, photo, travel insurance',
                'processing_time': 15
            }
        ]

        for country_data in countries:
            Country.objects.get_or_create(
                name=country_data['name'],
                defaults={
                    'region': country_data['region'],
                    'visa_requirements': country_data['visa_requirements'],
                    'processing_time': country_data['processing_time']
                }
            )

        # Get or create test user
        user, created = CustomUser.objects.get_or_create(
            id=5,
            defaults={
                'username': 'testuser',
                'email': 'test@example.com',
                'phone_number': '+1234567890',
                'region': 'Test Region',
                'passport_number': 'TEST123456'
            }
        )

        # Create test visa applications
        applications = [
            {
                'country': Country.objects.get(name='United States'),
                'visa_type': 'tourist',
                'purpose_of_travel': 'Vacation',
                'travel_start_date': timezone.now() + datetime.timedelta(days=30),
                'travel_end_date': timezone.now() + datetime.timedelta(days=45),
                'number_of_applicants': 2,
                'status': 'pending',
                'documents': ['passport.pdf', 'photo.jpg']
            },
            {
                'country': Country.objects.get(name='United Kingdom'),
                'visa_type': 'business',
                'purpose_of_travel': 'Business meeting',
                'travel_start_date': timezone.now() + datetime.timedelta(days=15),
                'travel_end_date': timezone.now() + datetime.timedelta(days=20),
                'number_of_applicants': 1,
                'status': 'in_review',
                'documents': ['passport.pdf', 'invitation.pdf']
            },
            {
                'country': Country.objects.get(name='Schengen Area'),
                'visa_type': 'tourist',
                'purpose_of_travel': 'Family visit',
                'travel_start_date': timezone.now() + datetime.timedelta(days=60),
                'travel_end_date': timezone.now() + datetime.timedelta(days=75),
                'number_of_applicants': 3,
                'status': 'approved',
                'documents': ['passport.pdf', 'family_invitation.pdf']
            }
        ]

        for app_data in applications:
            VisaApplication.objects.get_or_create(
                user=user,
                country=app_data['country'],
                defaults={
                    'visa_type': app_data['visa_type'],
                    'purpose_of_travel': app_data['purpose_of_travel'],
                    'travel_start_date': app_data['travel_start_date'],
                    'travel_end_date': app_data['travel_end_date'],
                    'number_of_applicants': app_data['number_of_applicants'],
                    'status': app_data['status'],
                    'documents': app_data['documents'],
                    'submission_date': timezone.now()
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully created test data')) 