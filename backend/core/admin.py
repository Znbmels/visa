from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CustomUser, Country, VisaApplication, VisaFee, Document, Notification, FAQ, 
    SystemSetting, CurrencyRate, Payment, UserFeedback, VisaTypeCountry, 
    CountryGroup, UserSavedVisa, TravelItinerary, Embassy, VisaDocumentRule, 
    VisaProgress, Service, ChatMessage, Conversation, Language, UserProfile, 
    Translation, UserActivity, UserLoginHistory, Subscription, UserSubscription, UserAnalytics
)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'passport_number', 'phone_number', 'region')
    search_fields = ('username', 'email', 'passport_number')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'profile__nationality', 'profile__language_preference')
    ordering = ('username',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'processing_time')
    search_fields = ('name', 'region')

@admin.register(VisaApplication)
class VisaApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'country', 'visa_type', 'status', 'submission_date')
    list_filter = ('status', 'country', 'visa_type')
    search_fields = ('user__username', 'country__name')

@admin.register(VisaFee)
class VisaFeeAdmin(admin.ModelAdmin):
    list_display = ('country', 'visa_type', 'consular_fee', 'service_fee', 'total_fee')
    list_filter = ('country', 'visa_type')
    search_fields = ('country__name', 'visa_type')

    def total_fee(self, obj):
        return obj.total_fee()
    total_fee.short_description = 'Total Fee'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_picture_thumbnail', 'email_verified', 'phone_verified')
    search_fields = ('user__username', 'user__email', 'bio')
    readonly_fields = ('profile_picture_thumbnail',)

    def profile_picture_thumbnail(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_picture.url)
        return "-"
    profile_picture_thumbnail.short_description = 'Profile Picture'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'status', 'applied_at', 'processed_at', 'is_active', 'start_date', 'end_date')
    list_filter = ('status', 'is_active', 'applied_at', 'processed_at', 'subscription_plan')
    search_fields = ('user__username', 'user__email', 'subscription_plan__name')
    readonly_fields = ('applied_at', 'created_at', 'updated_at')
    ordering = ('-applied_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'subscription_plan', 'status', 'is_active')
        }),
        ('Даты', {
            'fields': ('applied_at', 'processed_at', 'start_date', 'end_date')
        }),
        ('Управление', {
            'fields': ('admin_notes', 'payment_status', 'auto_renew')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_subscriptions', 'reject_subscriptions']
    
    def approve_subscriptions(self, request, queryset):
        """Одобрить выбранные заявки на подписку"""
        updated = 0
        for subscription in queryset.filter(status='pending'):
            subscription.approve_subscription(f"Одобрено администратором {request.user.username}")
            updated += 1
        
        self.message_user(request, f'Одобрено {updated} заявок на подписку.')
    approve_subscriptions.short_description = "Одобрить выбранные заявки"
    
    def reject_subscriptions(self, request, queryset):
        """Отклонить выбранные заявки на подписку"""
        updated = 0
        for subscription in queryset.filter(status='pending'):
            subscription.reject_subscription(f"Отклонено администратором {request.user.username}")
            updated += 1
            
        self.message_user(request, f'Отклонено {updated} заявок на подписку.')
    reject_subscriptions.short_description = "Отклонить выбранные заявки"

@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'predicted_probability', 'prediction_model_version', 'feedback_score', 'created_at')
    list_filter = ('prediction_model_version',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'input_data') # input_data can be large
    list_select_related = ('user',) # Optimize queries

# Example of how you might have registered other models, ensure new ones are added similarly
# admin.site.register(Country) # Removed this line as Country is already registered with @admin.register
# admin.site.register(VisaApplication) # Consider using a ModelAdmin for better control like above
# admin.site.register(VisaFee)
# admin.site.register(Document)
# ... and so on for all your models

# If you have many models and want a simple registration for all:
# from django.apps import apps
# models = apps.get_models()
# for model in models:
#     try:
#         admin.site.register(model)
#     except admin.sites.AlreadyRegistered:
#         pass