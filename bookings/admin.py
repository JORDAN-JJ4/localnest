from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'guest', 'start_date', 'end_date', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'start_date', 'end_date', 'created_at')
    search_fields = ('id', 'property__name', 'guest__username', 'guest__email')
    ordering = ('-created_at',)
