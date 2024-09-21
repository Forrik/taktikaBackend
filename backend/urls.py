from django.contrib import admin
from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, GymListView, GymDetailView, TrainingListView,
    SubscriptionListView, TrainingFeedbackListView, TrainerListView,
    TrainerDetailView, TrainingDetailView, TrainingEnrollView, TrainingUnenrollView
)
from django.conf import settings
from django.conf.urls.static import static
from .permissions import IsAdminUser, IsTrainerUser, IsRegularUser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('profile/<int:user_id>/', ProfileView.as_view(), name='profile'),
    path('gyms/', GymListView.as_view(), name='gym-list'),
    path('gyms/<int:pk>/', GymDetailView.as_view(), name='gym-detail'),
    path('trainings/', TrainingListView.as_view(), name='training-list'),
    path('trainings/<int:pk>/', TrainingDetailView.as_view(), name='training-detail'),
    path('trainings/<int:pk>/enroll/',
         TrainingEnrollView.as_view(), name='training-enroll'),
    path('trainings/<int:pk>/unenroll/',
         TrainingUnenrollView.as_view(), name='training-unenroll'),
    path('subscriptions/', SubscriptionListView.as_view(),
         name='subscription-list'),
    path('feedback/', TrainingFeedbackListView.as_view(), name='feedback-list'),
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
