# Generated by Django 4.2.3 on 2024-10-06 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0015_remove_gym_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainer',
            name='sports_category',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
