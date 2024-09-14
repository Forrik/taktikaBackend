
from django.contrib import admin
from django.urls import path
from .views import RegisterView, LoginView, ProfileView, GymListView, TrainingListView, SubscriptionListView, TrainingFeedbackListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('profile/<int:user_id>/', ProfileView.as_view(), name='profile'),
    path('gyms/', GymListView.as_view(), name='gym-list'),
    path('trainings/', TrainingListView.as_view(), name='training-list'),
    path('subscriptions/', SubscriptionListView.as_view(),
         name='subscription-list'),
    path('feedback/', TrainingFeedbackListView.as_view(), name='feedback-list'),
]
