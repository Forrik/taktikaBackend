# Generated by Django 4.2.3 on 2024-10-09 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0024_alter_subscription_client_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
    ]
