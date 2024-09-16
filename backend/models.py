from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    level = models.IntegerField(default=1)
    total_trainings = models.IntegerField(default=0)
    first_training_date = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    preferred_area = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=[(
        'M', 'Male'), ('F', 'Female')], blank=True)


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


class Training(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    trainer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='trainer_trainings')
    date = models.DateTimeField()
    level = models.IntegerField()
    max_participants = models.IntegerField()
    current_participants = models.IntegerField(default=0)
    intensity = models.IntegerField(null=True, blank=True)
    participants = models.ManyToManyField(
        User, related_name='participant_trainings')


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    trainings_left = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class TrainingFeedback(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
