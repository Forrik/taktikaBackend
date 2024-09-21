from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.base_user import BaseUserManager


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
    phone = models.CharField(max_length=15, blank=True)
    level = models.IntegerField(default=1)
    total_trainings = models.IntegerField(default=0)
    first_training_date = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    preferred_area = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=[
                              ('M', 'Male'), ('F', 'Female')], blank=True)

    def __str__(self):
        return f"Profile for {self.user.email}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.user.role == 'trainer':
            Trainer.objects.get_or_create(user=self.user)


@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


class Gym(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    metro_station = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='gym_photos/', blank=True)
    level = models.IntegerField()

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
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, null=False)
    trainer = models.ForeignKey(
        Trainer, on_delete=models.CASCADE, related_name='trainings')
    date = models.DateTimeField()
    level = models.IntegerField()
    max_participants = models.IntegerField()
    current_participants = models.IntegerField(default=0)
    intensity = models.IntegerField(null=True, blank=True)
    participants = models.ManyToManyField(
        CustomUser, related_name='trainings', blank=True)

    def __str__(self):
        return f"Training at {self.gym.name} on {self.date}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Если это новый объект
            self.current_participants = 0  # Устанавливаем начальное значение
        super().save(*args, **kwargs)  # Сохраняем объект один раз
        self.current_participants = self.participants.count()
        if self.pk:  # Если объект уже существует, обновляем его
            super().save(update_fields=['current_participants'])


class Subscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    type = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    trainings_left = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Subscription for {self.user.email}"


class TrainingFeedback(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.training} by {self.user.email}"
