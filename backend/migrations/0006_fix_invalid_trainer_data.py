from django.db import migrations


def fix_invalid_trainer_data(apps, schema_editor):
    Training = apps.get_model('backend', 'Training')
    Trainer = apps.get_model('backend', 'Trainer')

    # Получаем все действительные id тренеров
    valid_trainer_ids = set(Trainer.objects.values_list('id', flat=True))

    # Находим все тренировки с недействительными trainer_id
    invalid_trainings = Training.objects.exclude(
        trainer__in=Trainer.objects.all())

    # Если есть хотя бы один тренер, назначаем его на все недействительные тренировки
    if valid_trainer_ids:
        default_trainer_id = min(valid_trainer_ids)
        for training in invalid_trainings:
            training.trainer_id = default_trainer_id
            training.save()
    else:
        # Если нет ни одного тренера, создаем нового
        new_trainer = Trainer.objects.create(
            user_id=1, experience_years=0, bio="Default trainer")
        for training in invalid_trainings:
            training.trainer = new_trainer
            training.save()


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_alter_training_participants_alter_training_trainer'),
    ]

    operations = [
        migrations.RunPython(fix_invalid_trainer_data),
    ]
