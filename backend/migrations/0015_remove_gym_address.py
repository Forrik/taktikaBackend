# Generated by Django 4.2.3 on 2024-10-06 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0014_training_unenroll_deadline'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gym',
            name='address',
        ),
    ]
