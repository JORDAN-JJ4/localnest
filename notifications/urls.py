from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('mark-read/<uuid:notification_id>/', views.MarkNotificationReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
]
