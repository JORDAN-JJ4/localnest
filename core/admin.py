from django.contrib import admin
from .models import BlogPost, StoryContributor, Family, Recipe, Tradition, VoiceRecording, Story, LocalSecret, SecretRecommendation

# Inlines
class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 1
    prepopulated_fields = {'slug': ('name',)}

class TraditionInline(admin.TabularInline):
    model = Tradition
    extra = 1
    prepopulated_fields = {'slug': ('name',)}

class SecretRecommendationInline(admin.StackedInline):
    model = SecretRecommendation
    extra = 1

# Admins
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(StoryContributor)
class StoryContributorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'occupation', 'consent_given', 'consent_visibility')
    list_filter = ('consent_given', 'consent_visibility')
    search_fields = ('name', 'email')

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'languages')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RecipeInline, TraditionInline]
    search_fields = ('name', 'bio')

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'family')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'ingredients')

@admin.register(Tradition)
class TraditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'family')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(VoiceRecording)
class VoiceRecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration')
    search_fields = ('title', 'transcript')

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'moderation_status', 'visibility', 'created_at')
    list_filter = ('category', 'moderation_status', 'visibility')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    
    actions = ['approve_stories', 'publish_stories', 'reject_stories']

    def approve_stories(self, request, queryset):
        queryset.update(moderation_status='APPROVED')
        self.message_user(request, "Selected stories approved.")
    approve_stories.short_description = "Mark selected stories as Approved"

    def publish_stories(self, request, queryset):
        queryset.update(moderation_status='PUBLISHED')
        self.message_user(request, "Selected stories published.")
    publish_stories.short_description = "Publish selected stories to web"

    def reject_stories(self, request, queryset):
        queryset.update(moderation_status='REJECTED')
        self.message_user(request, "Selected stories rejected.")
    reject_stories.short_description = "Reject selected stories"

@admin.register(LocalSecret)
class LocalSecretAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'location_name', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'description', 'location_name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SecretRecommendationInline]

@admin.register(SecretRecommendation)
class SecretRecommendationAdmin(admin.ModelAdmin):
    list_display = ('local_secret', 'visibility', 'is_approved', 'created_at')
    list_filter = ('visibility', 'is_approved')
    search_fields = ('local_secret__title', 'why_love')
    
    actions = ['approve_recommendations', 'reject_recommendations']

    def approve_recommendations(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Selected recommendations approved.")
    approve_recommendations.short_description = "Approve selected recommendations"

    def reject_recommendations(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "Selected recommendations disapproved/rejected.")
    reject_recommendations.short_description = "Disapprove/Reject selected recommendations"
