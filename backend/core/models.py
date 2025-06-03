from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUser(AbstractUser):
    passport_number = models.CharField(max_length=20, unique=True, verbose_name=_("Passport Number"))
    phone_number = models.CharField(max_length=15, verbose_name=_("Phone Number"))
    region = models.CharField(max_length=100, verbose_name=_("Region"))

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    def __str__(self):
        return self.username

class Country(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Country Name"))
    region = models.CharField(max_length=50, verbose_name=_("Region"))
    visa_requirements = models.TextField(verbose_name=_("Visa Requirements"))
    processing_time = models.IntegerField(verbose_name=_("Processing Time (days)"))
    image = models.ImageField(upload_to='country_flags/', null=True, blank=True, verbose_name=_('Flag/Image'))

    def __str__(self):
        return self.name

class VisaApplication(models.Model):
    VISA_TYPES = [
        ("tourist", _("Tourist")),
        ("work", _("Work")),
        ("study", _("Study")),
        ("business", _("Business")),
    ]

    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name=_("User"), related_name='visa_applications')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name=_("Country"))
    visa_type = models.CharField(max_length=20, choices=VISA_TYPES, default="tourist", verbose_name=_("Visa Type"))
    purpose_of_travel = models.TextField(default="Not specified", verbose_name=_("Purpose of Travel"))
    travel_start_date = models.DateField(default="2025-01-01", verbose_name=_("Travel Start Date"))
    travel_end_date = models.DateField(default="2025-01-01", verbose_name=_("Travel End Date"))
    number_of_applicants = models.IntegerField(default=1, verbose_name=_("Number of Applicants"))
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", _("Pending")),
            ("in_review", _("In Review")),
            ("approved", _("Approved")),
            ("rejected", _("Rejected"))
        ],
        default="pending",
        verbose_name=_("Status")
    )
    documents = models.JSONField(verbose_name=_("Uploaded Documents"))
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Submission Date"))
    decision_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Decision Date"))
    admin_comments = models.TextField(blank=True, null=True, verbose_name=_("Admin Comments"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Visa Application for {self.user.username} to {self.country.name}"

class VisaFee(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name=_("Country"))
    visa_type = models.CharField(max_length=20, choices=VisaApplication.VISA_TYPES, verbose_name=_("Visa Type"))
    consular_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Consular Fee"))
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Service Fee"))

    def __str__(self):
        return f"{self.visa_type} - {self.country.name} (${self.consular_fee + self.service_fee})"

    def total_fee(self):
        return self.consular_fee + self.service_fee

class Subscription(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(help_text="Duration in days") # e.g., 30 for monthly, 365 for yearly
    is_active = models.BooleanField(default=True) # To easily deactivate a plan

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    SUBSCRIPTION_STATUS_CHOICES = [
        ('pending', 'В ожидании одобрения'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('expired', 'Истекла'),
        ('cancelled', 'Отменена'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default='pending')
    auto_renew = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.subscription_plan.name if self.subscription_plan else 'No Plan'} ({self.status})"

    def is_currently_active(self):
        """Проверяет активна ли подписка (одобрена и не истекла)"""
        if self.status != 'approved' or not self.is_active:
            return False
        if self.start_date and self.end_date:
            now = timezone.now()
            return self.start_date <= now <= self.end_date
        return False

    def approve_subscription(self, admin_notes=""):
        """Одобряет подписку и активирует её"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.status = 'approved'
        self.is_active = True
        self.admin_notes = admin_notes
        self.processed_at = timezone.now()
        
        # Устанавливаем даты действия подписки
        if not self.start_date:
            self.start_date = timezone.now()
        if not self.end_date and self.subscription_plan:
            self.end_date = self.start_date + timedelta(days=self.subscription_plan.duration_days)
            
        self.save()

    def reject_subscription(self, admin_notes=""):
        """Отклоняет подписку"""
        from django.utils import timezone
        
        self.status = 'rejected'
        self.is_active = False
        self.admin_notes = admin_notes
        self.processed_at = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status__in=['pending', 'approved'], is_active=True),
                name='unique_active_subscription'
            )
        ]

class UserAnalytics(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='analytics_data')
    # Store raw input data as JSON or specific fields based on what you collect
    input_data = models.JSONField(help_text="Data used for probability prediction, e.g., country, visa type, history")
    predicted_probability = models.FloatField(null=True, blank=True, help_text="Predicted visa success probability (0.0 to 1.0)")
    # You might want to store the model version or ruleset used for prediction
    prediction_model_version = models.CharField(max_length=50, blank=True)
    feedback_score = models.IntegerField(null=True, blank=True, help_text="User feedback on prediction accuracy (e.g., 1-5 stars)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.user.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "User Analytics"
        verbose_name_plural = "User Analytics"
        ordering = ['-created_at']

# Placeholder models to resolve import errors
# These should be properly defined based on application requirements.

class Document(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='user_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} for {self.user.username}"

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.question

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.key

class CurrencyRate(models.Model):
    currency_code = models.CharField(max_length=3, unique=True) # e.g., USD, EUR
    rate_to_base = models.DecimalField(max_digits=10, decimal_places=4) # Rate relative to a base currency (e.g., USD)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.currency_code

class Payment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    user_subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD') # Should match CurrencyRate codes
    status = models.CharField(max_length=50, default='pending') # e.g., pending, completed, failed, refunded
    payment_gateway_charge_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} - {self.status}"

class UserFeedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    rating = models.IntegerField(null=True, blank=True) # e.g., 1-5 stars
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

class VisaTypeCountry(models.Model): # Already present in serializers, ensure consistency
    visa_type_name = models.CharField(max_length=100) # e.g., "Schengen Type C", "UK Tourist Visa"
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    # Add other relevant fields like specific requirements, processing times for this type/country combo
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.visa_type_name} for {self.country.name}"

class CountryGroup(models.Model):
    name = models.CharField(max_length=100, unique=True) # e.g., "Schengen Area", "CANZUK"
    countries = models.ManyToManyField(Country, related_name='country_groups')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class UserSavedVisa(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_visas')
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    visa_type_name = models.CharField(max_length=100, blank=True) # Optional, if they save a specific type
    notes = models.TextField(blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Saved visa for {self.country.name} by {self.user.username}"

class TravelItinerary(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='itineraries')
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    details_json = models.JSONField(blank=True, null=True) # Could store flights, hotels, etc.

    def __str__(self):
        return self.name

class Embassy(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='embassies_in_country') # Embassy of X country
    located_in_country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='embassies_located_here') # Located in Y country
    city = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return f"Embassy of {self.country.name} in {self.located_in_country.name}, {self.city}"

class VisaDocumentRule(models.Model):
    visa_type_country = models.ForeignKey(VisaTypeCountry, on_delete=models.CASCADE, related_name='document_rules')
    document_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    condition = models.CharField(max_length=255, blank=True, help_text="e.g., 'if_unemployed', 'if_minor'")

    def __str__(self):
        return f"{self.document_name} for {self.visa_type_country}"

class VisaProgress(models.Model):
    application = models.OneToOneField(VisaApplication, on_delete=models.CASCADE, related_name='progress_status')
    current_step = models.CharField(max_length=100) # e.g., "Documents Submitted", "Under Review", "Interview Scheduled"
    estimated_completion_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress for {self.application.id}: {self.current_step}"

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Conversation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations')
    admin_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_conversations', limit_choices_to={'is_staff': True})
    subject = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} with {self.user.username}"

class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class Language(models.Model):
    code = models.CharField(max_length=5, unique=True) # e.g., en, ru, fr
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    nationality = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    language_preference = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Translation(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    original_text_key = models.CharField(max_length=255) # Key to identify the string, e.g., 'welcome_message'
    translated_text = models.TextField()

    class Meta:
        unique_together = ('language', 'original_text_key')

    def __str__(self):
        return f"{self.original_text_key} ({self.language.code})"

class UserActivity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_log')
    activity_type = models.CharField(max_length=100) # e.g., 'login', 'profile_update', 'application_submitted'
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(blank=True, null=True) # e.g., IP address, browser info

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"

class UserLoginHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"

# Add to existing User model if you prefer direct relations, though OneToOneField in UserSubscription is often cleaner
# User.add_to_class('has_premium_access', property(lambda u: u.subscription_details.is_currently_active() if hasattr(u, 'subscription_details') else False))