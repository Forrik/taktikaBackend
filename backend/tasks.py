# tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Training, Subscription
from .notifications import send_confirmation_notification, send_cancellation_notification


@shared_task
def send_confirmation_reminders():
    now = timezone.now()
    for training in Training.objects.filter(date__gt=now):
        deadline = training.date - timezone.timedelta(days=2, hours=12)
        if now >= deadline:
            for user in training.participants.all():
                subscription = Subscription.objects.filter(
                    user=user, is_paid=True).first()
                if subscription and not subscription.confirmed:
                    send_confirmation_notification(user, training)


@shared_task
def cancel_unconfirmed_reservations():
    now = timezone.now()
    for training in Training.objects.filter(date__gt=now):
        deadline = training.date - timezone.timedelta(days=2, hours=15)
        if now >= deadline:
            for user in training.participants.all():
                subscription = Subscription.objects.filter(
                    user=user, is_paid=True).first()
                if subscription and not subscription.confirmed:
                    training.participants.remove(user)
                    send_cancellation_notification(user, training)
