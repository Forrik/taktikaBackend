# Generated by Django 4.2.3 on 2024-09-16 11:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('backend', '0003_trainer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trainer',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                       related_name='trainer_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
