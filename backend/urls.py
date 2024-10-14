# backend/urls.py
from django.contrib import admin
from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, GymListView, GymDetailView, TrainingListView,
    SubscriptionListView, TrainingFeedbackListView, TrainerListView,
    TrainerDetailView, TrainingDetailView, TrainingEnrollView, TrainingUnenrollView, ManageRecurringTrainingsView,
    SubscriptionDetailView, CreateSubscriptionView, CreatePaymentView, payment_webhook, TrainingConfirmView,
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
    path('trainings/<int:pk>/confirm/', TrainingConfirmView.as_view(),
         name='training-confirm'),  # Добавлен маршрут для подтверждения записи
    path('subscriptions/', SubscriptionListView.as_view(),
         name='subscription-list'),
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(),
         name='subscription-detail'),
    path('feedback/', TrainingFeedbackListView.as_view(), name='feedback-list'),
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
    path('manage-recurring-trainings/', ManageRecurringTrainingsView.as_view(),
         name='manage-recurring-trainings'),
    path('oauth/callback/', views.amocrm_callback, name='amocrm_callback'),
    path('subscriptions/create/', CreateSubscriptionView.as_view(),
         name='subscription-create'),
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(),
         name='subscription-detail'),
    path('create_payment/', CreatePaymentView.as_view(), name='create_payment'),
    path('subscriptions/create/', CreateSubscriptionView.as_view(),
         name='subscription-create'),
    path('webhook/payment/', payment_webhook, name='payment_webhook'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
