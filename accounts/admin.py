from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, HostProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'email_verified', 'is_staff')
    list_filter = ('user_type', 'email_verified', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile Fields', {'fields': ('user_type', 'email_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile Fields', {
            'classes': ('wide',),
            'fields': ('user_type', 'email_verified'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city_state', 'created_at')
    search_fields = ('user__username', 'phone_number', 'address')

    def city_state(self, obj):
        return obj.address
    city_state.short_description = "Address"


@admin.register(HostProfile)
class HostProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'verification_status', 'created_at')
    list_filter = ('verification_status', 'created_at')
    search_fields = ('user__username', 'phone_number', 'address', 'verification_notes')
    actions = ['approve_hosts', 'reject_hosts']

    @admin.action(description="Approve selected hosts verification requests")
    def approve_hosts(self, request, queryset):
        rows_updated = queryset.update(verification_status=HostProfile.VerificationStatus.APPROVED)
        if rows_updated == 1:
            message_bit = "1 host profile was"
        else:
            message_bit = f"{rows_updated} host profiles were"
        self.message_user(request, f"{message_bit} successfully approved.")

    @admin.action(description="Reject selected hosts verification requests")
    def reject_hosts(self, request, queryset):
        rows_updated = queryset.update(verification_status=HostProfile.VerificationStatus.REJECTED)
        if rows_updated == 1:
            message_bit = "1 host profile was"
        else:
            message_bit = f"{rows_updated} host profiles were"
        self.message_user(request, f"{message_bit} marked as rejected.")


admin.site.register(User, CustomUserAdmin)
