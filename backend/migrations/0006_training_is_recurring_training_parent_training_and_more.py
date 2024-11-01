# Generated by Django 4.2.3 on 2024-09-27 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_remove_profile_bio_remove_profile_birth_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='training',
            name='is_recurring',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='training',
            name='parent_training',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recurring_trainings', to='backend.training'),
        ),
        migrations.AddField(
            model_name='training',
            name='recurrence_end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
