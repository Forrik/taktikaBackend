# Generated by Django 4.2.3 on 2024-10-06 15:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0016_trainer_sports_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trainer',
            name='sports_category',
        ),
    ]