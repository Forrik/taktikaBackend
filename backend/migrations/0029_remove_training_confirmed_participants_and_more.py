# Generated by Django 4.2.3 on 2024-10-14 12:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0028_training_confirmed_participants_notification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='training',
            name='confirmed_participants',
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
    ]