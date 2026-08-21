import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Amenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50, 
        help_text="Bootstrap Icon class, e.g., 'bi-wifi' or 'bi-snow'"
    )

    class Meta:
        verbose_name_plural = "Amenities"
        ordering = ['name']

    def __str__(self):
        return self.name


class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    description = models.TextField()
    best_season = models.CharField(max_length=150, blank=True)
    local_food = models.CharField(max_length=255, blank=True)
    weather = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name


class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='properties'
    )
    destination = models.ForeignKey(
        Destination,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties'
    )
    name = models.CharField(max_length=150)
    description = models.TextField()
    price_per_night = models.DecimalField(
        max_length=10, 
        decimal_places=2, 
        max_digits=8, 
        validators=[MinValueValidator(0.0)]
    )
    max_guests = models.PositiveIntegerField(default=1)
    private_room = models.BooleanField(
        default=True, 
        help_text="True if guests get a private room; False if shared living space"
    )
    
    # House rules & Times
    house_rules = models.TextField(blank=True)
    check_in_time = models.TimeField()
    check_out_time = models.TimeField()
    
    # Address details
    address = models.CharField(max_length=255)
    village = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    
    # Map Coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Amenities & Languages
    amenities = models.ManyToManyField(Amenity, related_name='properties', blank=True)
    languages_spoken = models.CharField(
        max_length=255, 
        help_text="Comma-separated languages spoken by host family (e.g., English, Hindi)"
    )
    nearby_attractions = models.TextField(blank=True)
    
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_average_rating(self):
        # Calculated via relationship reviews
        ratings = self.reviews.all()
        if ratings.exists():
            return round(sum(r.overall_rating for r in ratings) / ratings.count(), 1)
        return 0.0

    def get_food_rating(self):
        ratings = self.reviews.all()
        if ratings.exists():
            return round(sum(r.food_rating for r in ratings) / ratings.count(), 1)
        return 0.0

    def get_food_rating_percentage(self):
        return int(self.get_food_rating() * 20)

    def get_cleanliness_rating(self):
        ratings = self.reviews.all()
        if ratings.exists():
            return round(sum(r.cleanliness_rating for r in ratings) / ratings.count(), 1)
        return 0.0

    def get_cleanliness_rating_percentage(self):
        return int(self.get_cleanliness_rating() * 20)

    def get_host_behaviour_rating(self):
        ratings = self.reviews.all()
        if ratings.exists():
            return round(sum(r.host_behaviour_rating for r in ratings) / ratings.count(), 1)
        return 0.0

    def get_host_behaviour_rating_percentage(self):
        return int(self.get_host_behaviour_rating() * 20)

    def get_cultural_experience_rating(self):
        ratings = self.reviews.all()
        if ratings.exists():
            return round(sum(r.cultural_experience_rating for r in ratings) / ratings.count(), 1)
        return 0.0

    def get_cultural_experience_rating_percentage(self):
        return int(self.get_cultural_experience_rating() * 20)



class PropertyImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='property_images/')

    class Meta:
        ordering = ['image']

    def __str__(self):
        return f"Image for {self.property.name}"


class Experience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='experiences'
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.CharField(max_length=100)  # e.g., "3 hours"
    image = models.ImageField(upload_to='experiences/', blank=True, null=True)
    category = models.CharField(max_length=100, default='Village Walk')

    def __str__(self):
        return self.title


class FoodMenu(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.OneToOneField(
        Property, 
        on_delete=models.CASCADE, 
        related_name='food_menu'
    )
    
    # Meal inclusion
    breakfast_included = models.BooleanField(default=False)
    breakfast_details = models.CharField(max_length=255, blank=True)
    
    lunch_included = models.BooleanField(default=False)
    lunch_details = models.CharField(max_length=255, blank=True)
    
    dinner_included = models.BooleanField(default=False)
    dinner_details = models.CharField(max_length=255, blank=True)
    
    # Dietary choices
    vegetarian = models.BooleanField(default=True)
    non_vegetarian = models.BooleanField(default=False)
    vegan = models.BooleanField(default=False)
    jain = models.BooleanField(default=False)
    
    # Extended Culinary Experience
    weekly_menu = models.JSONField(default=dict, blank=True) # e.g. {"Monday": "...", "Tuesday": "..."}
    special_dishes = models.CharField(max_length=255, blank=True) # e.g. "Siddu, Kafru"
    cooking_style = models.CharField(max_length=100, default='Traditional wood-fired')
    spice_level = models.CharField(max_length=50, default='Medium')
    local_desserts = models.CharField(max_length=255, blank=True)
    
    # Food Photos
    food_photo_1 = models.ImageField(upload_to='food_menus/', blank=True, null=True)
    food_photo_2 = models.ImageField(upload_to='food_menus/', blank=True, null=True)
    
    custom_notes = models.TextField(blank=True, max_length=1000)

    def __str__(self):
        return f"Food Menu for {self.property.name}"


class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wishlists'
    )
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        related_name='wishlists',
        null=True,
        blank=True
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='host_wishlists',
        null=True,
        blank=True
    )
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='destination_wishlists',
        null=True,
        blank=True
    )
    experience = models.ForeignKey(
        Experience,
        on_delete=models.CASCADE,
        related_name='experience_wishlists',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.property:
            return f"{self.user.username}'s wishlist item: {self.property.name}"
        elif self.host:
            return f"{self.user.username}'s wishlist host: {self.host.username}"
        elif self.destination:
            return f"{self.user.username}'s wishlist destination: {self.destination.name}"
        elif self.experience:
            return f"{self.user.username}'s wishlist experience: {self.experience.title}"
        return f"{self.user.username}'s empty wishlist item"

