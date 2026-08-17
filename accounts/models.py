import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    class Types(models.TextChoices):
        TOURIST = 'TOURIST', 'Tourist'
        HOST = 'HOST', 'Host'
        ADMIN = 'ADMIN', 'Admin'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(
        max_length=15, 
        choices=Types.choices, 
        default=Types.TOURIST
    )
    email_verified = models.BooleanField(default=False)

    def is_tourist(self):
        return self.user_type == self.Types.TOURIST

    def is_host(self):
        return self.user_type == self.Types.HOST

    def is_admin(self):
        return self.user_type == self.Types.ADMIN or self.is_staff or self.is_superuser


class Profile(models.Model):
    """Profile model for Tourists"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Tourist Profile"


class HostProfile(models.Model):
    """Profile and Verification documents for Hosts"""
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='host_profile')
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True, max_length=1000)
    profile_photo = models.ImageField(upload_to='host_profiles/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    
    # Extended Host Information
    family_intro = models.TextField(blank=True, max_length=1000)
    occupation = models.CharField(max_length=150, blank=True)
    years_hosting = models.PositiveIntegerField(default=0)
    response_time = models.CharField(max_length=100, default='Within a few hours')
    response_rate = models.PositiveIntegerField(default=100) # percentage
    fav_local_place = models.CharField(max_length=255, blank=True)
    fav_homemade_dish = models.CharField(max_length=255, blank=True)
    achievements = models.JSONField(default=list, blank=True) # list of strings or dicts
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    # Verification uploads
    government_id = models.FileField(upload_to='host_documents/ids/', blank=True, null=True)
    selfie_photo = models.ImageField(upload_to='host_documents/selfies/', blank=True, null=True)
    
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    verification_notes = models.TextField(blank=True, max_length=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Host Profile ({self.verification_status})"


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporter.username} against {self.reported_user.username}"


class Block(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked_user')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked_user.username}"


# Signals to automatically create profiles when a new user registers
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_host():
            HostProfile.objects.create(user=instance)
        elif instance.is_tourist():
            Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.is_host() and hasattr(instance, 'host_profile'):
        instance.host_profile.save()
    elif instance.is_tourist() and hasattr(instance, 'profile'):
        instance.profile.save()
