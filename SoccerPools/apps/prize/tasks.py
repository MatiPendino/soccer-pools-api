from celery import shared_task
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from apps.app_user.models import AppUser
from .models import Prize

@shared_task
def send_prize_request_email_task(user_id, prize_id):
    """Sends the prize request received email to the user and site admins"""
    user = get_object_or_404(AppUser, id=user_id)
    prize = get_object_or_404(Prize, id=prize_id, state=True)
    today = timezone.localdate()
    subject = 'Prize request received'
    context = {
        'user_first_name': user.name,
        'prize_name': prize.title,
        'submission_date': today,
    }
    message = render_to_string('prize_request_received.html', context=context)
    recipients = [user.email] + [email for _, email in settings.ADMINS]
    email = EmailMessage(subject, message, to=recipients)
    email.content_subtype = 'html'  
    email.send()
