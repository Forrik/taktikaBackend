from django.contrib import admin
from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, GymListView, GymDetailView, TrainingListView,
    SubscriptionListView, TrainingFeedbackListView, TrainerListView,
    TrainerDetailView, TrainingDetailView, TrainingEnrollView, TrainingUnenrollView, ManageRecurringTrainingsView,
    SubscriptionDetailView, CreateSubscriptionView  # Добавлены новые представления
)
from django.conf import settings
from django.conf.urls.static import static
from . import views

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
    path('subscriptions/create/', CreateSubscriptionView.as_view(),
         name='subscription-create'),  # Добавлен маршрут для создания абонемента
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(),
         name='subscription-detail'),  # Добавлен маршрут для деталей абонемента
    path('feedback/', TrainingFeedbackListView.as_view(), name='feedback-list'),
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
    path('manage-recurring-trainings/', ManageRecurringTrainingsView.as_view(),
         name='manage-recurring-trainings'),
    path('oauth/callback/', views.amocrm_callback, name='amocrm_callback'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
