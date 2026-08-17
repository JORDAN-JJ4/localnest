import uuid
from django.db import models
from django.conf import settings

class BlogPost(models.Model):
    class CategoryChoices(models.TextChoices):
        STORIES = 'STORIES', 'Travel Stories'
        GEMS = 'GEMS', 'Hidden Gems'
        CULTURE = 'CULTURE', 'Local Culture'
        RECIPES = 'RECIPES', 'Traditional Recipes'
        FESTIVALS = 'FESTIVALS', 'Festivals'
        PHOTOGRAPHY = 'PHOTOGRAPHY', 'Photography'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(
        max_length=50,
        choices=CategoryChoices.choices,
        default=CategoryChoices.STORIES
    )
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts'
    )
    # Cross-linking entities for Content-to-Commerce Network
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stories'
    )
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stories'
    )
    experience = models.ForeignKey(
        'properties.Experience',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stories'
    )
    destination = models.ForeignKey(
        'properties.Destination',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class StoryContributor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    consent_given = models.BooleanField(default=False, help_text="Consent to publish this story")
    consent_visibility = models.CharField(
        max_length=50,
        choices=[
            ('PUBLIC', 'Public (Anyone can see)'),
            ('COMMUNITY', 'Community (Logged-in users)'),
            ('PRIVATE', 'Private (Review required)')
        ],
        default='PUBLIC'
    )

    def __str__(self):
        return self.name


class Family(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    host_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='host_families'
    )
    intro = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=255, blank=True)
    home_description = models.TextField(blank=True)
    home_history = models.TextField(blank=True)
    home_architecture = models.TextField(blank=True)
    photo = models.ImageField(upload_to='families/', blank=True, null=True)
    home_photo = models.ImageField(upload_to='families/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Families"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    ingredients = models.TextField()
    preparation_steps = models.TextField()
    family_memory = models.TextField(blank=True)
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='recipes')
    experience = models.ForeignKey(
        'properties.Experience',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes'
    )

    def __str__(self):
        return self.name


class Tradition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='traditions/', blank=True, null=True)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='traditions')

    def __str__(self):
        return self.name


class VoiceRecording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to='voices/', blank=True, null=True)
    transcript = models.TextField(blank=True)
    duration = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.title


class Story(models.Model):
    class ModerationStatusChoices(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        REVIEW = 'REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        PUBLISHED = 'PUBLISHED', 'Published'
        REJECTED = 'REJECTED', 'Rejected'

    class VisibilityChoices(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        COMMUNITY = 'COMMUNITY', 'Community (Logged-in Only)'
        GUESTS = 'GUESTS', 'LocalNest Guests (Booked Guests)'
        PRIVATE = 'PRIVATE', 'Private'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('FAMILY', 'Family Stories'),
            ('FOOD', 'Food Stories'),
            ('CRAFT', 'Craft Stories'),
            ('VILLAGE', 'Village Stories'),
            ('HERITAGE', 'Heritage Stories'),
            ('WOMEN', 'Women-led Stories'),
            ('GENERATIONAL', 'Generational Stories'),
            ('ARTISAN', 'Artisan Stories'),
            ('FARMER', 'Farmer Stories'),
            ('HOME', 'Home Stories')
        ],
        default='FAMILY'
    )
    intro = models.TextField(blank=True)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='stories/', blank=True, null=True)
    contributor = models.ForeignKey(StoryContributor, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    tradition = models.ForeignKey(Tradition, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    voice_recording = models.ForeignKey(VoiceRecording, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    
    # Links to core components
    destination = models.ForeignKey('properties.Destination', on_delete=models.SET_NULL, null=True, blank=True, related_name='destination_stories')
    property = models.ForeignKey('properties.Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='property_stories')
    experience = models.ForeignKey('properties.Experience', on_delete=models.SET_NULL, null=True, blank=True, related_name='experience_stories')
    
    moderation_status = models.CharField(
        max_length=50,
        choices=ModerationStatusChoices.choices,
        default=ModerationStatusChoices.DRAFT
    )
    visibility = models.CharField(
        max_length=50,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PUBLIC
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Stories"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class LocalSecret(models.Model):
    class SecretCategoryChoices(models.TextChoices):
        EAT = 'EAT', 'Eat Here'
        RITUAL = 'RITUAL', 'Morning Rituals'
        QUIET = 'QUIET', 'Quiet Places'
        CRAFT = 'CRAFT', 'Local Craft'
        WALK = 'WALK', 'Walk Here'
        CULTURE = 'CULTURE', 'Local Culture'
        SUNSET = 'SUNSET', 'Watch the Sunset'
        FAMILY = 'FAMILY', 'Family Favorites'
        HISTORY = 'HISTORY', 'Local History'
        SMALL_BIZ = 'SMALL_BIZ', 'Small Businesses'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(
        max_length=50,
        choices=SecretCategoryChoices.choices,
        default=SecretCategoryChoices.EAT
    )
    description = models.TextField()
    location_name = models.CharField(max_length=255, help_text="e.g. Dadar West Market, Shivaji Park")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to='secrets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class SecretRecommendation(models.Model):
    class VisibilityChoices(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        COMMUNITY = 'COMMUNITY', 'Community (Logged-in Only)'
        GUESTS = 'GUESTS', 'LocalNest Guests (Booked Guests)'
        PRIVATE = 'PRIVATE', 'Private'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local_secret = models.ForeignKey(LocalSecret, on_delete=models.CASCADE, related_name='recommendations')
    recommended_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='secret_recommendations')
    recommended_by_family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='secret_recommendations')
    
    why_love = models.TextField()
    what_to_try = models.TextField(blank=True)
    when_to_go = models.CharField(max_length=150, blank=True)
    local_etiquette = models.TextField(blank=True, help_text="Tips on how to behave respectfully")
    price_range = models.CharField(max_length=50, blank=True, help_text="e.g. Budget, Moderate, Splurge")
    
    visibility = models.CharField(
        max_length=50,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PUBLIC
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.recommended_by_family.name if self.recommended_by_family else (self.recommended_by_user.username if self.recommended_by_user else "Unknown")
        return f"{self.local_secret.title} recommended by {name}"

