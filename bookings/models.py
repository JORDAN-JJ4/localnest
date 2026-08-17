import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from properties.models import Property

class Booking(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    guest = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    guest_count = models.PositiveIntegerField()
    experiences = models.ManyToManyField('properties.Experience', related_name='bookings', blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.id} for {self.property.name} by {self.guest.username}"

    def clean(self):
        # Validate dates
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("Check-out date must be after the check-in date.")
            
            # Check for overlapping bookings
            overlapping_bookings = Booking.objects.filter(
                property=self.property,
                status=self.StatusChoices.APPROVED
            ).filter(
                models.Q(start_date__lt=self.end_date, end_date__gt=self.start_date)
            )
            
            if self.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)
                
            if overlapping_bookings.exists():
                raise ValidationError("This property is already booked for the selected dates.")
        
        # Validate guest count
        if self.guest_count and self.property:
            if self.guest_count > self.property.max_guests:
                raise ValidationError(f"Guest count exceeds the maximum limit of {self.property.max_guests} for this property.")
            if self.guest_count < 1:
                raise ValidationError("Guest count must be at least 1.")

    def save(self, *args, **kwargs):
        # Automatically calculate price before clean validation
        if not self.total_price and self.start_date and self.end_date and self.property:
            nights = (self.end_date - self.start_date).days
            self.total_price = self.property.price_per_night * nights
        self.full_clean()
        super().save(*args, **kwargs)


class PassportBadge(models.Model):
    class BadgeType(models.TextChoices):
        DESTINATION = 'DESTINATION', 'Destination'
        CULTURE = 'CULTURE', 'Culture'
        FOOD = 'FOOD', 'Food'
        EXPERIENCE = 'EXPERIENCE', 'Experience'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='passport_badges'
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='passport_badges'
    )
    badge_type = models.CharField(
        max_length=20,
        choices=BadgeType.choices,
        default=BadgeType.DESTINATION
    )
    title = models.CharField(max_length=150)
    icon = models.CharField(max_length=50, default='bi-award')
    awarded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.badge_type} Badge: {self.title}"

