# Generated by Django 4.2.3 on 2024-10-06 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0017_remove_trainer_sports_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='sports_category',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]