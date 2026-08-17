from django.contrib import admin
from .models import Property, PropertyImage, Amenity, FoodMenu, Wishlist

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class FoodMenuInline(admin.StackedInline):
    model = FoodMenu
    can_delete = False


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'price_per_night', 'city', 'state', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'state', 'city', 'private_room', 'created_at')
    search_fields = ('name', 'description', 'city', 'state', 'village', 'host__username', 'host__email')
    inlines = [PropertyImageInline, FoodMenuInline]
    actions = ['approve_properties']

    @admin.action(description="Approve selected homestay properties")
    def approve_properties(self, request, queryset):
        rows_updated = queryset.update(is_approved=True)
        if rows_updated == 1:
            message_bit = "1 property was"
        else:
            message_bit = f"{rows_updated} properties were"
        self.message_user(request, f"{message_bit} successfully approved.")


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'property__name')


# Register remaining models
admin.site.register(PropertyImage)
admin.site.register(FoodMenu)
