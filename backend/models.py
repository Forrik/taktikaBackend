from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
import logging
from django.db.models import Q
logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)

        # Удаляем 'username' из extra_fields, если он там есть
        extra_fields.pop('username', None)

        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('trainer', 'Trainer'),
        ('user', 'User'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES, default='user')
    middle_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)  # Добавлено
    birth_date = models.DateField(null=True, blank=True)  # Добавлено
    gender = models.CharField(max_length=10, choices=[(
        'M', 'Male'), ('F', 'Female')], blank=True)  # Добавлено
    passport_data = models.CharField(max_length=100, blank=True)  # Добавлено
    experience_years = models.IntegerField(default=0)  # Добавлено
    bio = models.TextField(blank=True)  # Добавлено
    sports_title = models.CharField(max_length=100, blank=True)  # Добавлено
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    account_id = models.CharField(
        max_length=100, blank=True)  # Добавленный атрибут
    level = models.IntegerField(default=1)  # Добавленное поле
    sports_category = models.CharField(
        max_length=100, blank=True)  # Добавленное поле
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    total_trainings = models.IntegerField(default=0)
    first_training_date = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    preferred_area = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Profile for {self.user.email}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.user.role == 'trainer':
            Trainer.objects.get_or_create(user=self.user)


class Gym(models.Model):
    name = models.CharField(max_length=100)
    metro_station = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='gym_photos/', blank=True, null=True)

    def __str__(self):
        return self.name


class Trainer(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='trainer_profile')
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Trainer"


class Training(models.Model):
    GENDER_CHOICES = [
        ('any', 'Any'),
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, null=False)
    trainer = models.ForeignKey(
        Trainer, on_delete=models.CASCADE, related_name='trainings')
    date = models.DateTimeField()
    level = models.IntegerField()
    max_participants = models.IntegerField()
    current_participants = models.IntegerField(default=0)
    unenroll_deadline = models.DateTimeField(null=True, blank=True)
    intensity = models.IntegerField(null=True, blank=True)
    participants = models.ManyToManyField(
        CustomUser, related_name='trainings', blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_end_date = models.DateField(null=True, blank=True)
    parent_training = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='recurring_trainings')
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default='any')  # Добавленное поле
    reserve_participants = models.ManyToManyField(
        CustomUser, related_name='reserve_trainings', blank=True)
    priority_participants = models.ManyToManyField(
        CustomUser, related_name='priority_trainings', blank=True)

    def add_to_reserve(self, user):
        self.reserve_participants.add(user)
        self.save()

    def add_to_priority(self, user):
        self.priority_participants.add(user)
        self.save()

    def __str__(self):
        return f"Training at {self.gym.name} on {self.date}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.current_participants = 0
        super().save(*args, **kwargs)
        self.current_participants = self.participants.count()
        if self.pk:
            super().save(update_fields=['current_participants'])

    def create_next_recurring(self):
        if self.is_recurring and self.recurrence_end_date and self.date.date() + timezone.timedelta(days=7) <= self.recurrence_end_date:
            next_date = self.date + timezone.timedelta(days=7)
            Training.objects.create(
                gym=self.gym,
                trainer=self.trainer,
                date=next_date,
                level=self.level,
                max_participants=self.max_participants,
                intensity=self.intensity,
                is_recurring=True,
                recurrence_end_date=self.recurrence_end_date,
                parent_training=self,
                gender=self.gender
            )


class Subscription(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    CLIENT_TYPES = [
        ('adult', 'Adult'),
        ('child', 'Child'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=50)  # Увеличиваем длину поля
    start_date = models.DateField()
    end_date = models.DateField()
    trainings_left = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    trainer = models.ForeignKey(
        Trainer, on_delete=models.CASCADE, null=True, blank=True)
    # Добавлено для хранения ID платежа
    payment_id = models.CharField(max_length=100, blank=True, null=True)

    # Новые поля
    days_of_week = models.CharField(max_length=50, blank=True)
    client_type = models.CharField(
        max_length=50, choices=CLIENT_TYPES, blank=True)  # Увеличиваем длину поля
    month = models.CharField(max_length=20, blank=True)
    is_paid = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    reserve_priority = models.IntegerField(default=0)

    def enroll_user_to_trainings(self):
        """
        Автоматически записывает пользователя на тренировки, соответствующие абонементу.
        """
        logger.info(
            f"Starting enroll_user_to_trainings for subscription {self.id}")

        if not self.is_paid:
            logger.info(
                f"Subscription {self.id} is not paid, skipping enrollment")
            return

        logger.info(
            f"Enrolling user {self.user.id} with level {self.user.level} and gender {self.user.gender} "
            f"to trainings in gym {self.gym.id} from {self.start_date} to {self.end_date}"
        )

        try:
            trainings = Training.objects.filter(
                gym=self.gym,
                date__gte=self.start_date,
                date__lte=self.end_date,
                level=self.user.level,
            ).filter(Q(gender=self.user.gender) | Q(gender='any'))

            logger.info(
                f"Found {trainings.count()} potential trainings for subscription {self.id}")
            if not trainings:
                logger.info(f"No trainings found for subscription {self.id}")
                return

            for training in trainings:
                logger.info(
                    f"Potential training: ID {training.id}, Date {training.date}, Level {training.level}, Gender {training.gender}")

            enrolled_count = 0
            for training in trainings:
                logger.info(f"Checking training {training.id} for enrollment")
                if self.is_valid_for_training(training):  # Исправлено
                    if training.current_participants < training.max_participants:
                        if self.trainings_left > 0:
                            logger.info(
                                f"Enrolling user {self.user.id} to training {training.id}")
                            training.participants.add(self.user)
                            training.current_participants = training.participants.count()
                            training.save()
                            self.use_training()
                            enrolled_count += 1
                            logger.info(
                                f"Successfully enrolled user {self.user.id} to training {training.id}")
                        else:
                            logger.info(
                                f"No trainings left in subscription {self.id}")
                            break
                    else:
                        logger.info(
                            f"Training {training.id} is full. Current participants: {training.current_participants}, Max participants: {training.max_participants}")
                else:
                    logger.info(
                        f"Training {training.id} is not valid for subscription {self.id}")

            logger.info(
                f"Enrolled user to {enrolled_count} trainings for subscription {self.id}")

        except Exception as e:
            logger.error(
                f"Error enrolling user to trainings for subscription {self.id}: {e}")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.is_paid and not self.confirmed:
            logger.info(
                f"New paid subscription {self.id} created, enrolling user to trainings")
            self.enroll_user_to_trainings()
        else:
            logger.info(
                f"Subscription {self.id} saved, but not enrolling user to trainings")

    def is_valid_for_training(self, training):
        """
        Проверяет, действителен ли абонемент для записи на данное занятие.
        """
        logger.info(
            f"Checking if subscription {self.id} is valid for training {training.id}")

        if not self.is_paid:
            logger.info(f"Subscription {self.id} is not paid.")
            return False

        training_day_of_week = training.date.strftime('%a').lower()[:3]
        if self.days_of_week:
            if training_day_of_week not in self.days_of_week.split(','):
                logger.info(
                    f"Training day {training_day_of_week} does not match subscription days {self.days_of_week}.")
                return False
        else:
            logger.info(
                f"No specific days set for subscription {self.id}, allowing all days.")

        training_month_year = f"{training.date.year}-{training.date.month}"
        if self.month:
            if training_month_year not in self.month.split(','):
                logger.info(
                    f"Training month {training_month_year} does not match subscription month {self.month}.")
                return False
        else:
            logger.info(
                f"No specific month set for subscription {self.id}, allowing all months.")

        logger.info(
            f"Subscription {self.id} is valid for training {training.id}")
        return True

    def use_training(self):
        """
        Уменьшает количество оставшихся тренировок в абонементе.
        """
        if self.trainings_left > 0:
            self.trainings_left -= 1
            self.save()
        else:
            logger.warning(f"No trainings left in subscription {self.id}.")


class TrainingFeedback(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.training} by {self.user.email}"
