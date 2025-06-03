from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CountryViewSet, VisaApplicationViewSet, CurrentUserView, RegisterView, 
    LoginView, LogoutView, VisaFeeViewSet, DocumentViewSet, NotificationViewSet, 
    FAQViewSet, SystemSettingViewSet, CurrencyRateViewSet, PaymentViewSet, 
    UserFeedbackViewSet, VisaTypeCountryViewSet, CountryGroupViewSet, 
    UserSavedVisaViewSet, TravelItineraryViewSet, EmbassyViewSet, 
    VisaDocumentRuleViewSet, VisaProgressViewSet, ServiceViewSet, ChatMessageViewSet, 
    ConversationViewSet, LanguageViewSet, UserProfileViewSet, TranslationViewSet, 
    UserActivityViewSet, UserLoginHistoryViewSet, TestAuthenticatedView, 
    upload_document_for_application, SubscriptionViewSet, UserSubscriptionViewSet, 
    VisaProbabilityView, UserViewSet, application_stats, calculate_visa_cost,
    VisaCostCalculatorView
)

router = DefaultRouter()
router.register(r'countries', CountryViewSet)
router.register(r'users', UserViewSet, basename='user')
router.register(r'visa-applications', VisaApplicationViewSet)
router.register(r'visa-fees', VisaFeeViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'faqs', FAQViewSet)
router.register(r'system-settings', SystemSettingViewSet)
router.register(r'currency-rates', CurrencyRateViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'user-feedback', UserFeedbackViewSet)
router.register(r'visa-type-countries', VisaTypeCountryViewSet)
router.register(r'country-groups', CountryGroupViewSet)
router.register(r'user-saved-visas', UserSavedVisaViewSet)
router.register(r'travel-itineraries', TravelItineraryViewSet)
router.register(r'embassies', EmbassyViewSet)
router.register(r'visa-document-rules', VisaDocumentRuleViewSet)
router.register(r'visa-progress', VisaProgressViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'chat-messages', ChatMessageViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'languages', LanguageViewSet)
router.register(r'user-profiles', UserProfileViewSet)
router.register(r'translations', TranslationViewSet)
router.register(r'user-activities', UserActivityViewSet)
router.register(r'user-login-history', UserLoginHistoryViewSet)

# New routers for subscription related views
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'user-subscriptions', UserSubscriptionViewSet, basename='usersubscription')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/user/', CurrentUserView.as_view(), name='current-user'),
    path('auth/test-auth/', TestAuthenticatedView.as_view(), name='test-auth'), # Added for testing
    path('visa-applications/<int:application_id>/upload-document/', upload_document_for_application, name='upload-document-for-application'),
    # New path for visa probability prediction
    path('subscription/probability/', VisaProbabilityView.as_view(), name='visa-probability'),
    path('application-stats/', application_stats, name='application-stats'),
    path('calculate-visa-cost/', VisaCostCalculatorView.as_view(), name='calculate-visa-cost'),
]