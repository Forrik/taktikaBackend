# Generated by Django 4.2.3 on 2024-10-05 18:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0011_remove_gym_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='city',
        ),
    ]
