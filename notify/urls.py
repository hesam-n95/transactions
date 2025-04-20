from django.urls import path
from .views import SendNotificationView,NotificationInquiry

urlpatterns = [
    path('api/notification/v1/send', SendNotificationView.as_view(), name='send-notification'),
    path('api/notification/v1', NotificationInquiry.as_view(), name='notification-inquiry')
]
