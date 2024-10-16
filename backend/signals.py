# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Training, Subscription, Notification
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Training)
def check_training_confirmations(sender, instance, **kwargs):
    now = timezone.now()
    deadline = instance.date - timezone.timedelta(days=2, hours=12)

    if now >= deadline:
        for user in instance.participants.all():
            if user not in instance.confirmed_participants.all():
                send_confirmation_reminder(user, instance)
                create_confirmation_notification(user, instance)

    # Снятие брони через 3 часа после уведомления
    if now >= deadline + timezone.timedelta(hours=3):
        for user in instance.participants.all():
            if user not in instance.confirmed_participants.all():
                instance.participants.remove(user)
                instance.save()
                send_unenroll_notification(user, instance)
                create_unenroll_notification(user, instance)


def send_confirmation_reminder(user, training):
    subject = "Подтвердите запись на тренировку"
    message = f"Уважаемый {user.first_name}, пожалуйста, подтвердите вашу запись на тренировку {training.id} до 15:00 сегодня."
    send_mail(subject, message, 'noreply@example.com', [user.email])


def send_unenroll_notification(user, training):
    subject = "Ваша бронь на тренировку снята"
    message = f"Уважаемый {user.first_name}, ваша бронь на тренировку {training.id} была снята из-за отсутствия подтверждения."
    send_mail(subject, message, 'noreply@example.com', [user.email])


def create_confirmation_notification(user, training):
    Notification.objects.create(
        user=user,
        message=f"Вам нужно подтвердить запись на тренировку {training.id}",
        type="confirm_training",
        training_id=training.id
    )
    logger.info(
        f"Created confirmation notification for user {user.id} and training {training.id}")


def create_unenroll_notification(user, training):
    Notification.objects.create(
        user=user,
        message=f"Ваша бронь на тренировку {training.id} была снята из-за отсутствия подтверждения.",
        type="unenroll_training",
        training_id=training.id
    )
    logger.info(
        f"Created unenroll notification for user {user.id} and training {training.id}")


@receiver(post_save, sender=Subscription)
def create_subscription_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.user,
            message=f"Вы купили абонемент '{instance.type}'",
            type="subscription_created"
        )
        logger.info(
            f"Created subscription notification for user {instance.user.id}")
