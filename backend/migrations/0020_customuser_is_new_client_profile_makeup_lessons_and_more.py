# Generated by Django 4.2.3 on 2024-10-09 11:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0019_training_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_new_client',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='makeup_lessons',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='MakeupLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expiration_date', models.DateField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
