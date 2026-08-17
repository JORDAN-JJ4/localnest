from django.shortcuts import redirect, get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Notification

class MarkNotificationReadView(LoginRequiredMixin, View):
    """Marks a specific notification as read and redirects back to previous page"""
    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect(request.META.get('HTTP_REFERER', 'dashboard:dispatcher'))


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Marks all notifications for current user as read"""
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard:dispatcher'))
