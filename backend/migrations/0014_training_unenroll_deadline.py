# Generated by Django 4.2.3 on 2024-10-06 07:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_customuser_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='training',
            name='unenroll_deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
