import uuid
from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Types(models.TextChoices):
        BOOKING_APPROVED = 'BOOKING_APPROVED', 'Booking Approved'
        BOOKING_CANCELLED = 'BOOKING_CANCELLED', 'Booking Cancelled'
        MESSAGE = 'MESSAGE', 'New Message'
        REVIEW_REMINDER = 'REVIEW_REMINDER', 'Review Reminder'
        SYSTEM = 'SYSTEM', 'System Alert'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30, 
        choices=Types.choices, 
        default=Types.SYSTEM
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
