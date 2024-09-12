# backend/backend/urls.py
from django.contrib import admin
from django.urls import path
from .views import RegisterView, LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
]
