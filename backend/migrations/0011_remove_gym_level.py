# Generated by Django 4.2.3 on 2024-10-05 17:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_alter_customuser_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gym',
            name='level',
        ),
    ]
