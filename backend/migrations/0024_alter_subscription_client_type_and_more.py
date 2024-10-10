# Generated by Django 4.2.3 on 2024-10-09 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0023_remove_subscription_training_days_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='client_type',
            field=models.CharField(blank=True, choices=[('adult', 'Adult'), ('child', 'Child')], max_length=50),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='type',
            field=models.CharField(max_length=50),
        ),
    ]