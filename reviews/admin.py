from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'author', 'overall_rating', 'food_rating', 'cleanliness_rating', 'created_at')
    list_filter = ('overall_rating', 'food_rating', 'cleanliness_rating', 'created_at')
    search_fields = ('id', 'property__name', 'author__username', 'comments')
    ordering = ('-created_at',)
