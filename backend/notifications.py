# notifications.py
from django.core.mail import send_mail
from django.conf import settings
import requests


def send_confirmation_notification(user, training):
    subject = 'Подтвердите запись на тренировку'
    message = f'Уважаемый {user.first_name}, подтвердите запись на тренировку {training.date}.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

    # Отправка уведомления через AmoCRM
    send_amocrm_notification(user, message)


def send_cancellation_notification(user, training):
    subject = 'Ваша бронь на тренировку отменена'
    message = f'Уважаемый {user.first_name}, ваша бронь на тренировку {training.date} отменена.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

    # Отправка уведомления через AmoCRM
    send_amocrm_notification(user, message)


def send_amocrm_notification(user, message):
    url = 'https://ilya33533.amocrm.ru/api/v4/contacts'
    headers = {
        'Authorization': f'Bearer {settings.AMOCRM_ACCESS_TOKEN}'
    }
    data = {
        'name': user.first_name,
        'custom_fields_values': [
            {
                'field_id': 12345,  # ID поля для уведомления
                'values': [
                    {
                        'value': message
                    }
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f'Ошибка отправки уведомления в AmoCRM: {response.status_code}')
