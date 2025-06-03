from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import VisaApplication, CustomUser, Country, VisaFee, Document, Notification, FAQ, SystemSetting, CurrencyRate, Payment, UserFeedback, VisaTypeCountry, CountryGroup, UserSavedVisa, TravelItinerary, Embassy, VisaDocumentRule, VisaProgress, Service, ChatMessage, Conversation, Language, UserProfile, Translation, UserActivity, UserLoginHistory, Subscription, UserSubscription, UserAnalytics
from .serializers import VisaApplicationSerializer, UserSerializer, CountrySerializer, VisaFeeSerializer, DocumentSerializer, NotificationSerializer, FAQSerializer, SystemSettingSerializer, CurrencyRateSerializer, PaymentSerializer, UserFeedbackSerializer, VisaTypeCountrySerializer, CountryGroupSerializer, UserSavedVisaSerializer, TravelItinerarySerializer, EmbassySerializer, VisaDocumentRuleSerializer, VisaProgressSerializer, ServiceSerializer, ChatMessageSerializer, ConversationSerializer, LanguageSerializer, UserProfileSerializer, TranslationSerializer, UserActivitySerializer, UserLoginHistorySerializer, SubscriptionSerializer, UserSubscriptionSerializer, UserAnalyticsSerializer, ProbabilityRequestSerializer, UserSubscriptionCreateSerializer
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.urls import get_resolver
import logging
from django.utils.translation import activate
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action, api_view, permission_classes
from django.utils import timezone
from datetime import timedelta

# Настройка логирования
logger = logging.getLogger(__name__)

class VisaApplicationViewSet(viewsets.ModelViewSet):
    queryset = VisaApplication.objects.all()
    serializer_class = VisaApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = VisaApplication.objects.filter(user=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        logger.info(f"Received update request for application {kwargs.get('pk')}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"User: {request.user}")
        instance = self.get_object()
        logger.info(f"Found instance: {instance}")
        previous_status = instance.status
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Status changed from {previous_status} to {instance.status}")
            if instance.status != previous_status:
                logger.info(f"Attempting to send email to {instance.user.email}")
                try:
                    send_mail(
                        'Visa Application Status Update',
                        f'Your application status has changed to {instance.status}. Comments: {instance.admin_comments or "None"}',
                        'znbmels@gmail.com',
                        [instance.user.email],
                        fail_silently=False,  # Changed to False to see errors
                    )
                    logger.info(f"Email sent successfully to {instance.user.email}")
                except Exception as e:
                    logger.error(f"Failed to send email: {str(e)}")
                    logger.error(f"Email settings: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USER={settings.EMAIL_HOST_USER}")
                
                try:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'user_{instance.user.id}',
                        {
                            'type': 'status_update',
                            'application_id': instance.id,
                            'status': instance.status,
                            'admin_comments': instance.admin_comments,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {str(e)}")
                    
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"VisaApplicationViewSet: Error in list: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]

class ApplicationStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            applications = VisaApplication.objects.filter(user=request.user)
            stats = {
                "total": applications.count(),
                "pending": applications.filter(status="pending").count(),
                "in_review": applications.filter(status="in_review").count(),
                "approved": applications.filter(status="approved").count(),
                "rejected": applications.filter(status="rejected").count(),
            }
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"ApplicationStatsView: Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VisaCostCalculatorView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Received POST request to /api/calculate-visa-cost/ with data: {request.data}")
        
        # Валидация входных данных
        country_id = request.data.get('country')
        visa_type = request.data.get('visa_type')
        number_of_applicants = request.data.get('number_of_applicants', 1)

        if not country_id or not visa_type:
            return Response(
                {"error": "Both country and visa_type are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            number_of_applicants = int(number_of_applicants)
            if number_of_applicants < 1:
                raise ValueError("Number of applicants must be positive")
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid number of applicants"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка существования страны
        try:
            country = Country.objects.get(id=country_id)
        except Country.DoesNotExist:
            return Response(
                {"error": f"Country with id {country_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверка валидности типа визы
        valid_visa_types = dict(VisaApplication.VISA_TYPES).keys()
        if visa_type not in valid_visa_types:
            return Response(
                {"error": f"Invalid visa type. Must be one of: {', '.join(valid_visa_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            visa_fee = VisaFee.objects.get(country=country, visa_type=visa_type)
            total_cost = visa_fee.total_fee() * number_of_applicants
            breakdown = {
                "country": country.name,
                "visa_type": visa_type,
                "number_of_applicants": number_of_applicants,
                "consular_fee": float(visa_fee.consular_fee) * number_of_applicants,
                "service_fee": float(visa_fee.service_fee) * number_of_applicants,
                "total_cost": float(total_cost)
            }
            logger.info(f"Returning breakdown: {breakdown}")
            return Response(breakdown, status=status.HTTP_200_OK)
        except VisaFee.DoesNotExist:
            # Добавляем подробный лог
            available_fees = VisaFee.objects.filter(country=country)
            available_types = list(available_fees.values_list('visa_type', flat=True))
            logger.error(
                f"No VisaFee found for country_id={country.id}, country_name={country.name}, visa_type={visa_type}. "
                f"Available types for this country: {available_types}"
            )
            return Response(
                {
                    "error": f"No fee data available for {country.name} and {visa_type} visa type",
                    "available_types": available_types
                },
                status=status.HTTP_404_NOT_FOUND
            )

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data['password'])
            user.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class DebugUrlsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        def get_all_urls(resolver, prefix=''):
            urls = []
            for pattern in resolver.url_patterns:
                if hasattr(pattern, 'url_patterns'):  # Это URLResolver (вложенный маршрут)
                    urls.extend(get_all_urls(pattern, prefix + str(pattern.pattern)))
                else:  # Это URLPattern (конечный маршрут)
                    urls.append(prefix + str(pattern.pattern))
            return urls

        urls = get_all_urls(get_resolver())
        return Response(urls)

class SetLanguageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        language = request.data.get('language')
        if language in ['en', 'ru', 'kk']:
            activate(language)
            return Response({"message": f"Language set to {language}"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid language code"}, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(request.user).data)

class VisaApplicationDocumentsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            app = VisaApplication.objects.get(pk=pk, user=request.user)
        except VisaApplication.DoesNotExist:
            return Response({'error': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)
        files = request.FILES.getlist('documents')
        if not files:
            return Response({'error': 'No files uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        # Сохраняем имена файлов в поле documents (или можно реализовать хранение файлов)
        app.documents = [f.name for f in files]
        app.save()
        return Response({'message': 'Documents uploaded successfully.', 'files': [f.name for f in files]})

class TestAuthenticatedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "This is a test endpoint for authenticated users."}, status=status.HTTP_200_OK)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# New ViewSets for Subscription, UserSubscription, and UserAnalytics

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing available subscription plans.
    """
    queryset = Subscription.objects.filter(is_active=True)
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny] # Anyone can see subscription plans

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user subscriptions.
    Users can view their subscription, create a new one (subscribe),
    and potentially update (e.g., change auto-renew) or cancel it.
    """
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only see and manage their own subscription."""
        return UserSubscription.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserSubscriptionCreateSerializer
        return UserSubscriptionSerializer

    def perform_create(self, serializer):
        """Создает заявку на подписку в статусе pending"""
        user = self.request.user
        
        # Проверяем есть ли уже активная заявка на подписку
        existing_subscription = UserSubscription.objects.filter(user=user).first()
        
        if existing_subscription:
            if existing_subscription.status == 'pending':
                raise serializers.ValidationError({"detail": "У вас уже есть заявка на подписку в ожидании одобрения."})
            elif existing_subscription.status == 'approved' and existing_subscription.is_currently_active():
                raise serializers.ValidationError({"detail": "У вас уже есть активная подписка."})
            # Если статус rejected, expired или cancelled - разрешаем создать новую заявку
            elif existing_subscription.status in ['approved', 'rejected', 'expired', 'cancelled']:
                # Деактивируем старую подписку если она была активна
                if existing_subscription.is_active:
                    existing_subscription.is_active = False
                    existing_subscription.save()

        subscription_plan = serializer.validated_data['subscription_plan']
        
        # Создаем заявку на подписку в статусе pending
        serializer.save(
            user=user,
            status='pending',
            is_active=False,
            payment_status='pending'
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_subscription(self, request, pk=None):
        """Cancels the user's active subscription."""
        try:
            user_subscription = self.get_object()
            if not user_subscription.is_active:
                return Response({"detail": "Subscription is not active."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Logic for cancellation: depending on policy, might end immediately or at period end.
            # For this example, we'll set it to inactive and keep the end_date.
            user_subscription.is_active = False
            user_subscription.auto_renew = False # Ensure auto-renew is off
            user_subscription.save()
            serializer = self.get_serializer(user_subscription)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response({"detail": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

    # Consider adding an action to change auto_renew status if not handled by general update

class VisaProbabilityView(APIView):
    """
    API endpoint for predicting visa application probability.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check for active subscription
        try:
            user_subscription = request.user.subscription_details
            if not user_subscription.is_currently_active():
                return Response(
                    {"detail": "Active subscription required for visa probability prediction."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except UserSubscription.DoesNotExist:
            return Response(
                {"detail": "No subscription found. Active subscription required for visa probability prediction."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProbabilityRequestSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            input_data = serializer.validated_data
            
            # --- Placeholder for ML model or rules engine --- 
            # This is where you would call your prediction logic.
            # For example:
            # probability = ml_model.predict(input_data)
            # or
            # probability = rules_engine.calculate(input_data)
            
            # Dummy probability for now
            probability = 0.75 # Example: 75% chance
            if input_data.get('country_id') == 1 and input_data.get('visa_type') == 'schengen': # Example Rule
                 probability = 0.85
            elif input_data.get('country_id') == 2:
                 probability = 0.60

            # Save the analytics data
            UserAnalytics.objects.create(
                user=user,
                input_data=input_data,
                predicted_probability=probability,
                prediction_model_version='dummy_v1.0' # Change as per your model versioning
            )
            
            return Response({"probability": probability, "input_data": input_data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Ensure UserAnalyticsViewSet if you need full CRUD on analytics (usually not exposed to end-users directly)
# For admins, it's handled via Django Admin. For user specific history, could be a list action on User model.

class UserActivityViewSet(viewsets.ModelViewSet):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Added missing views
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user) # Assuming UserSerializer is your CustomUser serializer
        return Response(serializer.data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], parser_classes=[MultiPartParser, FormParser])
def upload_document_for_application(request, application_id):
    # Placeholder for document upload logic
    # In a real scenario, you would handle file uploads, associate with VisaApplication, etc.
    try:
        application = VisaApplication.objects.get(id=application_id, user=request.user)
    except VisaApplication.DoesNotExist:
        return Response({"error": "Application not found or not owned by user"}, status=status.HTTP_404_NOT_FOUND)
    
    files = request.FILES.getlist('documents') # Assuming 'documents' is the field name for files
    if not files:
        return Response({"error": "No documents provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Example: Storing file names in the JSONField of VisaApplication (very basic)
    # A more robust solution would use a separate Document model and link it.
    if not isinstance(application.documents, list):
        application.documents = []
    
    for f in files:
        # Here you'd typically save the file to a storage (e.g., S3, local media) 
        # and store its path or URL.
        # For simplicity, just adding names.
        application.documents.append(f.name)
    
    application.save()
    return Response({"message": f"Documents uploaded for application {application_id}", "files": [f.name for f in files]}, status=status.HTTP_200_OK)

# Added missing ViewSets based on urls.py and previous errors

class VisaFeeViewSet(viewsets.ModelViewSet):
    queryset = VisaFee.objects.all()
    serializer_class = VisaFeeSerializer
    permission_classes = [IsAuthenticated] # Or AllowAny if fees are public

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    # Typically notifications are created by the system, not directly by user via API
    # So, might limit actions to list, retrieve, update (mark as read)

class FAQViewSet(viewsets.ReadOnlyModelViewSet): # Usually ReadOnly
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]

class SystemSettingViewSet(viewsets.ReadOnlyModelViewSet): # Usually ReadOnly for non-admins
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAdminUser] # Or a custom permission for system settings

class CurrencyRateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer
    permission_classes = [AllowAny]

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
    # Payment creation is usually part of another flow (e.g. subscription) and not a direct API endpoint for users

class UserFeedbackViewSet(viewsets.ModelViewSet):
    queryset = UserFeedback.objects.all()
    serializer_class = UserFeedbackSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

class VisaTypeCountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VisaTypeCountry.objects.all()
    serializer_class = VisaTypeCountrySerializer
    permission_classes = [AllowAny]

class CountryGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CountryGroup.objects.all()
    serializer_class = CountryGroupSerializer
    permission_classes = [AllowAny]

class UserSavedVisaViewSet(viewsets.ModelViewSet):
    queryset = UserSavedVisa.objects.all()
    serializer_class = UserSavedVisaSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return UserSavedVisa.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TravelItineraryViewSet(viewsets.ModelViewSet):
    queryset = TravelItinerary.objects.all()
    serializer_class = TravelItinerarySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return TravelItinerary.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmbassyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Embassy.objects.all()
    serializer_class = EmbassySerializer
    permission_classes = [AllowAny]

class VisaDocumentRuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VisaDocumentRule.objects.all()
    serializer_class = VisaDocumentRuleSerializer
    permission_classes = [AllowAny]

class VisaProgressViewSet(viewsets.ModelViewSet):
    queryset = VisaProgress.objects.all()
    serializer_class = VisaProgressSerializer
    permission_classes = [IsAuthenticated] # Or more complex, e.g., only user related to application
    # Add get_queryset to filter by user if needed

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_available=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        # Users should only see their own conversations
        return Conversation.objects.filter(user=self.request.user) 
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        # Users should only see messages in their conversations
        user_conversations = Conversation.objects.filter(user=self.request.user).values_list('id', flat=True)
        return ChatMessage.objects.filter(conversation_id__in=user_conversations)
    def perform_create(self, serializer):
        # Ensure the sender is the current user and the message is for one of their conversations
        conversation_id = self.request.data.get('conversation')
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=self.request.user)
            serializer.save(sender=self.request.user, conversation=conversation)
        except Conversation.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to post to this conversation.")

class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]

class TranslationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Translation.objects.all()
    serializer_class = TranslationSerializer
    permission_classes = [AllowAny] # Or based on language preference

class UserLoginHistoryViewSet(viewsets.ModelViewSet):
    queryset = UserLoginHistory.objects.all()
    serializer_class = UserLoginHistorySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return UserLoginHistory.objects.filter(user=self.request.user).order_by('-login_time')
    # Users should not be able to create/delete these, only view their own.
    # http_method_names = ['get', 'head', 'options'] for ReadOnly via API for users

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_stats(request):
    """Get statistics for user's visa applications"""
    user = request.user
    applications = VisaApplication.objects.filter(user=user)
    
    stats = {
        'total': applications.count(),
        'pending': applications.filter(status='pending').count(),
        'in_review': applications.filter(status='in_review').count(),
        'approved': applications.filter(status='approved').count(),
        'rejected': applications.filter(status='rejected').count()
    }
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_visa_cost(request):
    """Calculate visa cost based on parameters"""
    try:
        # Получаем параметры из запроса
        country_id = request.data.get('country_id')
        visa_type = request.data.get('visa_type')
        duration = request.data.get('duration')
        
        if not all([country_id, visa_type, duration]):
            return Response(
                {"error": "Missing required parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Здесь должна быть логика расчета стоимости визы
        # Для примера возвращаем фиксированную стоимость
        result = {
            "base_cost": 100,
            "service_fee": 50,
            "total_cost": 150,
            "processing_time": "10-15 business days",
            "currency": "USD"
        }
        
        return Response(result)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )