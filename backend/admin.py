from django.contrib import admin
from .models import Profile, Gym, Training, Subscription, TrainingFeedback

admin.site.register(Profile)
admin.site.register(Gym)
admin.site.register(Training)
admin.site.register(Subscription)
admin.site.register(TrainingFeedback)
