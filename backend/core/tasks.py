from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_status_update_email(email, status, comments):
    subject = 'Visa Application Status Update'
    message = f'Your application status has changed to {status}. Comments: {comments or "None"}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return f"Email sent successfully to {email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}" 