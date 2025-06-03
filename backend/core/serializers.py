from rest_framework import serializers
from .models import (
    CustomUser, Country, VisaApplication, VisaFee, Document, Notification, FAQ, 
    SystemSetting, CurrencyRate, Payment, UserFeedback, VisaTypeCountry, 
    CountryGroup, UserSavedVisa, TravelItinerary, Embassy, VisaDocumentRule, 
    VisaProgress, Service, ChatMessage, Conversation, Language, UserProfile, 
    Translation, UserActivity, UserLoginHistory, Subscription, UserSubscription, UserAnalytics
)
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'region', 'visa_requirements', 'processing_time', 'image']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number', 'region', 'passport_number']

class VisaApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        source='country',
        write_only=True
    )

    class Meta:
        model = VisaApplication
        fields = [
            'id',
            'user',
            'country',
            'country_id',
            'visa_type',
            'purpose_of_travel',
            'travel_start_date',
            'travel_end_date',
            'number_of_applicants',
            'status',
            'documents',
            'submission_date',
            'decision_date',
            'admin_comments'
        ]
        read_only_fields = ['user', 'submission_date', 'decision_date', 'admin_comments']

class VisaFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaFee
        fields = ['id', 'country', 'visa_type', 'consular_fee', 'service_fee']

class VisaTypeCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaTypeCountry
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'name', 'description', 'price', 'duration_days', 'is_active')

class UserSubscriptionSerializer(serializers.ModelSerializer):
    subscription_plan = SubscriptionSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    is_currently_active = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_is_currently_active(self, obj):
        return obj.is_currently_active()

    class Meta:
        model = UserSubscription
        fields = (
            'id', 'user', 'subscription_plan', 'status', 'status_display',
            'start_date', 'end_date', 'is_active', 'payment_status', 
            'auto_renew', 'is_currently_active', 'admin_notes',
            'applied_at', 'processed_at', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'user', 'start_date', 'end_date', 'is_active', 'payment_status', 
            'applied_at', 'processed_at', 'created_at', 'updated_at', 'admin_notes'
        )

class UserSubscriptionCreateSerializer(serializers.ModelSerializer):
    subscription_plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(is_active=True),
        source='subscription_plan',
        write_only=True
    )

    class Meta:
        model = UserSubscription
        fields = ('subscription_plan_id', 'auto_renew')

class UserAnalyticsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserAnalytics
        fields = ('id', 'user', 'input_data', 'predicted_probability', 'prediction_model_version', 'feedback_score', 'created_at')
        read_only_fields = ('user', 'predicted_probability', 'prediction_model_version', 'created_at')

class ProbabilityRequestSerializer(serializers.Serializer):
    # Define fields based on the input_data structure you expect for UserAnalytics
    # For example:
    country_id = serializers.IntegerField()
    visa_type = serializers.CharField(max_length=100)
    # ... other relevant fields like income, travel_history_count, etc.
    # This serializer will validate the input for the probability prediction endpoint.
    # Ensure these fields match what your ML model or rules engine expects.

    def validate_country_id(self, value):
        if not Country.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid country ID.")
        return value

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'

class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = '__all__'

class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class UserFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = '__all__'

class CountryGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryGroup
        fields = '__all__'

class UserSavedVisaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSavedVisa
        fields = '__all__'

class TravelItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelItinerary
        fields = '__all__'

class EmbassySerializer(serializers.ModelSerializer):
    class Meta:
        model = Embassy
        fields = '__all__'

class VisaDocumentRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaDocumentRule
        fields = '__all__'

class VisaProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaProgress
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = '__all__'

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = '__all__'

class UserLoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLoginHistory
        fields = '__all__'

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code']