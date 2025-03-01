from django.urls import path
from .views import FCMTokenAPIView

urlpatterns = [
    path('fcm_device/', FCMTokenAPIView.as_view(), name='fcm_device'),
]