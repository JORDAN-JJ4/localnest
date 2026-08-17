import uuid
from django.db import models
from bookings.models import Booking

class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH_ON_ARRIVAL = 'CASH_ON_ARRIVAL', 'Cash on Arrival'
        RAZORPAY = 'RAZORPAY', 'Razorpay Online'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='payment'
    )
    payment_method = models.CharField(
        max_length=30, 
        choices=PaymentMethod.choices, 
        default=PaymentMethod.CASH_ON_ARRIVAL
    )
    transaction_id = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Online gateway transaction or order identifier"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=PaymentStatus.choices, 
        default=PaymentStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} for Booking {self.booking.id} - Status: {self.status}"
