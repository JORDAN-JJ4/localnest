from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Avg, Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.text import slugify
from properties.models import Property, Destination, Experience
from .models import BlogPost, StoryContributor, Family, Recipe, Tradition, VoiceRecording, Story, LocalSecret, SecretRecommendation

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch up to 3 featured properties with ratings and image count
        context['featured_homestays'] = Property.objects.filter(
            is_approved=True
        ).select_related('host', 'food_menu').annotate(
            avg_rating=Avg('reviews__overall_rating')
        ).prefetch_related('images')[:3]
        
        # Fetch up to 5 signature destinations
        context['destinations'] = Destination.objects.all()[:5]
        
        # Fetch up to 3 recent stories from the 1000 Stories archive
        context['recent_stories'] = Story.objects.filter(moderation_status='PUBLISHED').select_related('family', 'destination')[:3]
        
        # Fetch up to 3 families for "Meet the People"
        context['families'] = Family.objects.all()[:3]
        
        # Fetch up to 3 experiences for "Local Experiences"
        context['experiences'] = Experience.objects.all()[:3]
        
        # Fetch up to 3 local secrets
        context['local_secrets'] = LocalSecret.objects.all()[:3]
        
        # Fetch up to 3 recipes for "Local Food"
        context['recipes'] = Recipe.objects.select_related('family')[:3]
        
        return context



class RobotsView(TemplateView):
    template_name = 'core/robots.txt'
    content_type = 'text/plain'


class SitemapView(TemplateView):
    template_name = 'core/sitemap.xml'
    content_type = 'application/xml'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['properties'] = Property.objects.filter(is_approved=True)
        context['domain'] = self.request.build_absolute_uri('/')[:-1]
        return context


class BlogListView(ListView):
    model = BlogPost
    template_name = 'core/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        queryset = BlogPost.objects.select_related('author')
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogPost.CategoryChoices.choices
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'core/blog_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_posts'] = BlogPost.objects.exclude(id=self.object.id)[:3]
        return context


class StoryListView(ListView):
    model = Story
    template_name = 'core/stories_list.html'
    context_object_name = 'stories'
    paginate_by = 6

    def get_queryset(self):
        # Only show published and public/community stories based on login status
        queryset = Story.objects.filter(moderation_status='PUBLISHED')
        
        user = self.request.user
        if not user.is_authenticated:
            queryset = queryset.filter(visibility='PUBLIC')
        else:
            queryset = queryset.filter(visibility__in=['PUBLIC', 'COMMUNITY'])
            
        # Search query
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | 
                Q(intro__icontains=q) | 
                Q(content__icontains=q)
            )
            
        # Category filter
        cat = self.request.GET.get('category')
        if cat:
            queryset = queryset.filter(category=cat)

        # Destination filter
        dest = self.request.GET.get('destination')
        if dest:
            queryset = queryset.filter(destination__slug=dest)
            
        return queryset.select_related('family', 'destination')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_published = Story.objects.filter(moderation_status='PUBLISHED').count()
        context['progress_count'] = 142 + total_published
        context['progress_percentage'] = min(100, int((context['progress_count'] / 1000) * 100))
        
        context['categories'] = [
            ('FAMILY', 'Family Stories'),
            ('FOOD', 'Food Stories'),
            ('CRAFT', 'Craft Stories'),
            ('HERITAGE', 'Heritage Stories'),
            ('GENERATIONAL', 'Generational Stories')
        ]
        context['destinations'] = Destination.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_destination'] = self.request.GET.get('destination', '')
        context['q'] = self.request.GET.get('q', '')
        return context


class StoryDetailView(DetailView):
    model = Story
    template_name = 'core/story_detail.html'
    context_object_name = 'story'

    def get_object(self, queryset=None):
        story = super().get_object(queryset)
        
        if self.request.user.is_superuser:
            return story

        if story.moderation_status != 'PUBLISHED':
            raise PermissionDenied("This story is not published yet.")
        
        if story.visibility == 'COMMUNITY':
            if not self.request.user.is_authenticated:
                raise PermissionDenied("This story is reserved for the LocalNest community. Please sign in.")
        elif story.visibility == 'GUESTS':
            if not self.request.user.is_authenticated:
                raise PermissionDenied("This story is reserved for the LocalNest community. Please sign in.")
            from bookings.models import Booking
            has_booking = Booking.objects.filter(
                guest=self.request.user,
                property=story.property,
                status=Booking.StatusChoices.APPROVED
            ).exists()
            if not has_booking:
                raise PermissionDenied("This story is only accessible to guests who have booked a stay at this homestead.")
        elif story.visibility == 'PRIVATE':
            if story.contributor and story.contributor.email != self.request.user.email:
                raise PermissionDenied("This story is private.")
        return story

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        story = self.object
        
        context['family'] = story.family
        context['recipe'] = story.recipe
        context['tradition'] = story.tradition
        context['voice_recording'] = story.voice_recording
        
        if story.destination:
            context['related_stories'] = Story.objects.filter(
                destination=story.destination,
                moderation_status='PUBLISHED'
            ).exclude(id=story.id)[:3]
        return context


class StoryShareView(LoginRequiredMixin, TemplateView):
    template_name = 'core/share_story.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        occupation = request.POST.get('occupation')
        bio = request.POST.get('bio')
        title = request.POST.get('title')
        category = request.POST.get('category', 'FAMILY')
        intro = request.POST.get('intro')
        content = request.POST.get('content')
        consent = request.POST.get('consent') == 'on'
        visibility = request.POST.get('visibility', 'PUBLIC')

        if not title or not content or not name or not email:
            messages.error(request, "Please fill in all required fields.")
            return render(request, self.template_name, self.get_context_data())

        if not consent:
            messages.error(request, "You must give consent to publish your story.")
            return render(request, self.template_name, self.get_context_data())

        contributor = StoryContributor.objects.create(
            name=name,
            email=email,
            occupation=occupation,
            bio=bio,
            consent_given=True,
            consent_visibility=visibility
        )

        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Story.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        story = Story.objects.create(
            title=title,
            slug=slug,
            category=category,
            intro=intro,
            content=content,
            contributor=contributor,
            moderation_status='SUBMITTED',
            visibility=visibility
        )

        if 'featured_image' in request.FILES:
            story.featured_image = request.FILES['featured_image']
            story.save()

        messages.success(request, "Thank you! Your story has been submitted and is currently being reviewed by our editorial team.")
        return redirect('core:stories_list')


class SecretListView(ListView):
    model = LocalSecret
    template_name = 'core/secrets_list.html'
    context_object_name = 'secrets'
    paginate_by = 9

    def get_queryset(self):
        queryset = LocalSecret.objects.all()
        
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | 
                Q(description__icontains=q) | 
                Q(location_name__icontains=q)
            )
            
        cat = self.request.GET.get('category')
        if cat:
            queryset = queryset.filter(category=cat)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = LocalSecret.SecretCategoryChoices.choices
        context['selected_category'] = self.request.GET.get('category', '')
        context['q'] = self.request.GET.get('q', '')
        return context


class SecretDetailView(DetailView):
    model = LocalSecret
    template_name = 'core/secret_detail.html'
    context_object_name = 'secret'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        secret = self.object
        
        recommendations = secret.recommendations.filter(is_approved=True).select_related('recommended_by_family', 'recommended_by_user')
        
        user = self.request.user
        accessible_recs = []
        locked_recs = []
        
        for rec in recommendations:
            if rec.visibility == 'PUBLIC':
                accessible_recs.append(rec)
            elif rec.visibility == 'COMMUNITY':
                if user.is_authenticated:
                    accessible_recs.append(rec)
                else:
                    locked_recs.append(rec)
            elif rec.visibility == 'GUESTS':
                has_booking = False
                if user.is_authenticated:
                    from bookings.models import Booking
                    fam = rec.recommended_by_family
                    if fam:
                        has_booking = Booking.objects.filter(
                            guest=user,
                            property__host=fam.host_user,
                            status=Booking.StatusChoices.APPROVED
                        ).exists()
                if has_booking or user.is_superuser:
                    accessible_recs.append(rec)
                else:
                    locked_recs.append(rec)
            elif rec.visibility == 'PRIVATE':
                if user.is_authenticated and (user == rec.recommended_by_user or user.is_superuser):
                    accessible_recs.append(rec)
                else:
                    locked_recs.append(rec)
                    
        context['accessible_recommendations'] = accessible_recs
        context['locked_recommendations'] = locked_recs
        context['locked_count'] = len(locked_recs)
        return context
