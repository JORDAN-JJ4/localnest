from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Avg, Q
from django.core.exceptions import PermissionDenied

from .models import Property, Amenity, FoodMenu, PropertyImage, Experience, Destination, Wishlist
from .forms import PropertyForm, FoodMenuForm, PropertyImageForm, ExperienceForm
from accounts.models import HostProfile

class VerifiedHostMixin(UserPassesTestMixin):
    """Mixin to ensure that only hosts with APPROVED verification status can create or manage properties."""
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated or not user.is_host():
            return False
        # Fetch verification status
        try:
            return user.host_profile.verification_status == HostProfile.VerificationStatus.APPROVED
        except HostProfile.DoesNotExist:
            return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated and self.request.user.is_host():
            messages.error(self.request, "Your host profile must be APPROVED by an administrator before you can manage listings.")
            return redirect('dashboard:dispatcher')
        messages.error(self.request, "You must register and be verified as a Host to perform this action.")
        return redirect('accounts:login')


class PropertySearchView(ListView):
    model = Property
    template_name = 'properties/search.html'
    context_object_name = 'properties'
    paginate_by = 9

    def get_queryset(self):
        search_type = self.request.GET.get('type', 'homes')
        
        if search_type == 'hosts':
            queryset = HostProfile.objects.filter(verification_status=HostProfile.VerificationStatus.APPROVED).select_related('user').order_by('id')
            query = self.request.GET.get('q', '').strip()
            if query:
                queryset = queryset.filter(
                    Q(user__first_name__icontains=query) |
                    Q(user__last_name__icontains=query) |
                    Q(bio__icontains=query) |
                    Q(address__icontains=query)
                )
            return queryset
            
        elif search_type == 'experiences':
            queryset = Experience.objects.select_related('host').order_by('id')
            query = self.request.GET.get('q', '').strip()
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(category__icontains=query)
                )
            return queryset
            
        else:
            queryset = Property.objects.filter(is_approved=True).select_related('host', 'food_menu').prefetch_related('images', 'reviews', 'amenities').order_by('id')
            
            # Apply filters from GET parameters
            query = self.request.GET.get('q', '').strip()
            state = self.request.GET.get('state', '').strip()
            city = self.request.GET.get('city', '').strip()
            village = self.request.GET.get('village', '').strip()
            price_max = self.request.GET.get('price_max', '').strip()
            private_room = self.request.GET.get('private_room', '').strip()
            vegetarian = self.request.GET.get('vegetarian', '').strip()
            non_vegetarian = self.request.GET.get('non_vegetarian', '').strip()
            vegan = self.request.GET.get('vegan', '').strip()
            jain = self.request.GET.get('jain', '').strip()
            breakfast = self.request.GET.get('breakfast', '').strip()
            language = self.request.GET.get('language', '').strip()
            rating_min = self.request.GET.get('rating_min', '').strip()
            
            # Selected amenities (list of IDs)
            selected_amenities = self.request.GET.getlist('amenity')

            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(city__icontains=query) |
                    Q(state__icontains=query) |
                    Q(village__icontains=query)
                )
            
            if state:
                queryset = queryset.filter(state__icontains=state)
            if city:
                queryset = queryset.filter(city__icontains=city)
            if village:
                queryset = queryset.filter(village__icontains=village)
                
            if price_max:
                try:
                    queryset = queryset.filter(price_per_night__lte=float(price_max))
                except ValueError:
                    pass
                    
            if private_room == '1':
                queryset = queryset.filter(private_room=True)
            elif private_room == '0':
                queryset = queryset.filter(private_room=False)

            # Food filters
            if vegetarian:
                queryset = queryset.filter(food_menu__vegetarian=True)
            if non_vegetarian:
                queryset = queryset.filter(food_menu__non_vegetarian=True)
            if vegan:
                queryset = queryset.filter(food_menu__vegan=True)
            if jain:
                queryset = queryset.filter(food_menu__jain=True)
            if breakfast:
                queryset = queryset.filter(food_menu__breakfast_included=True)

            if language:
                queryset = queryset.filter(languages_spoken__icontains=language)

            # Amenities filter
            if selected_amenities:
                for amenity_id in selected_amenities:
                    queryset = queryset.filter(amenities__id=amenity_id)

            # Dynamic Intent Filter (Discover by Feeling)
            intent = self.request.GET.get('intent', '').strip()
            if intent:
                if intent == 'slow_down':
                    queryset = queryset.filter(
                        Q(village__gt='') |
                        Q(description__icontains='slow') |
                        Q(description__icontains='quiet') |
                        Q(description__icontains='peaceful') |
                        Q(description__icontains='calm')
                    )
                elif intent == 'meet_people':
                    queryset = queryset.filter(
                        Q(private_room=False) |
                        Q(description__icontains='family') |
                        Q(description__icontains='conversation') |
                        Q(description__icontains='welcoming') |
                        Q(host__host_profile__bio__icontains='welcome')
                    )
                elif intent == 'homemade_food':
                    queryset = queryset.filter(
                        Q(food_menu__isnull=False) |
                        Q(description__icontains='food') |
                        Q(description__icontains='kitchen') |
                        Q(description__icontains='recipe')
                    )
                elif intent == 'experience_tradition':
                    queryset = queryset.filter(
                        Q(host__experiences__category__icontains='craft') |
                        Q(host__experiences__category__icontains='ritual') |
                        Q(host__experiences__category__icontains='tradition') |
                        Q(host__experiences__description__icontains='ancient') |
                        Q(description__icontains='heritage') |
                        Q(description__icontains='tradition')
                    ).distinct()
                elif intent == 'learn_something':
                    queryset = queryset.filter(
                        Q(host__experiences__title__icontains='learn') |
                        Q(host__experiences__title__icontains='cook') |
                        Q(host__experiences__title__icontains='weave') |
                        Q(host__experiences__title__icontains='harvest') |
                        Q(host__experiences__title__icontains='craft') |
                        Q(description__icontains='learn')
                    ).distinct()
                elif intent == 'disappear_into_nature':
                    queryset = queryset.filter(
                        Q(description__icontains='mist') |
                        Q(description__icontains='garden') |
                        Q(description__icontains='hills') |
                        Q(description__icontains='mountain') |
                        Q(description__icontains='forest') |
                        Q(description__icontains='nature') |
                        Q(description__icontains='tea')
                    )

            # Rating filter (annotate first then filter)
            queryset = queryset.annotate(avg_rating=Avg('reviews__overall_rating'))
            if rating_min:
                try:
                    queryset = queryset.filter(avg_rating__gte=float(rating_min))
                except ValueError:
                    pass

            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_type = self.request.GET.get('type', 'homes')
        context['search_type'] = search_type
        context['results'] = context['object_list']
        context['amenities_list'] = Amenity.objects.all()
        context['active_intent'] = self.request.GET.get('intent', '')
        # Pass filters back to keep form state in template
        context['filters'] = self.request.GET
        if self.request.user.is_authenticated:
            context['wishlisted_property_ids'] = list(self.request.user.wishlists.values_list('property_id', flat=True))
        else:
            context['wishlisted_property_ids'] = []
            
        # Development-time family image validation
        if search_type == 'hosts':
            from core.models import Family
            import logging
            logger = logging.getLogger(__name__)
            
            families = Family.objects.all()
            image_paths = {}
            for fam in families:
                if fam.photo:
                    path = fam.photo.name
                    if path in image_paths:
                        image_paths[path].append(fam.name)
                    else:
                        image_paths[path] = [fam.name]
            
            duplicates = {path: fams for path, fams in image_paths.items() if len(fams) > 1}
            if duplicates:
                warning_msg = "\n" + "="*60 + "\nWARNING: Duplicate family image detected:\n"
                for path, fams in duplicates.items():
                    warning_msg += f"Image '{path}' is used by: {', '.join(fams)}\n"
                warning_msg += "="*60 + "\n"
                logger.warning(warning_msg)
                print(warning_msg)
                
        return context


class PropertyDetailView(DetailView):
    model = Property
    template_name = 'properties/detail.html'
    context_object_name = 'property'

    def get_queryset(self):
        return Property.objects.select_related('host', 'food_menu').prefetch_related('images', 'reviews__author', 'amenities')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if the current user has favorited this property
        context['in_wishlist'] = False
        if self.request.user.is_authenticated:
            context['in_wishlist'] = self.object.wishlists.filter(user=self.request.user).exists()
            
        # Fetch related blog stories for this property or its host
        from core.models import BlogPost
        context['related_stories'] = BlogPost.objects.filter(
            Q(property=self.object) | Q(host=self.object.host)
        ).distinct()[:3]
        return context


class PropertyCreateView(LoginRequiredMixin, VerifiedHostMixin, View):
    def get(self, request):
        property_form = PropertyForm()
        food_form = FoodMenuForm()
        image_form = PropertyImageForm()
        return render(request, 'properties/property_form.html', {
            'property_form': property_form,
            'food_form': food_form,
            'image_form': image_form,
            'title': 'Add Property Listing'
        })

    def post(self, request):
        property_form = PropertyForm(request.POST)
        food_form = FoodMenuForm(request.POST)
        images = request.FILES.getlist('images')

        if property_form.is_valid() and food_form.is_valid():
            # Save Property
            property_obj = property_form.save(commit=False)
            property_obj.host = request.user
            # In development, auto-approve properties if configured, or default to false
            property_obj.is_approved = False  # Requires Admin Approval
            property_obj.save()
            property_form.save_m2m()  # For amenities ManyToMany relationship

            # Save Food Menu
            food_menu = food_form.save(commit=False)
            food_menu.property = property_obj
            food_menu.save()

            # Save Images
            for img in images:
                PropertyImage.objects.create(property=property_obj, image=img)

            messages.success(request, "Property listing submitted successfully! It is pending admin approval.")
            return redirect('dashboard:dispatcher')
            
        return render(request, 'properties/property_form.html', {
            'property_form': property_form,
            'food_form': food_form,
            'image_form': PropertyImageForm(),
            'title': 'Add Property Listing'
        })


class PropertyUpdateView(LoginRequiredMixin, VerifiedHostMixin, View):
    def get(self, request, pk):
        property_obj = get_object_or_404(Property, pk=pk, host=request.user)
        food_menu = get_object_or_404(FoodMenu, property=property_obj)
        
        property_form = PropertyForm(instance=property_obj)
        food_form = FoodMenuForm(instance=food_menu)
        image_form = PropertyImageForm()
        
        return render(request, 'properties/property_form.html', {
            'property_form': property_form,
            'food_form': food_form,
            'image_form': image_form,
            'property': property_obj,
            'title': f'Edit Property: {property_obj.name}'
        })

    def post(self, request, pk):
        property_obj = get_object_or_404(Property, pk=pk, host=request.user)
        food_menu = get_object_or_404(FoodMenu, property=property_obj)
        
        property_form = PropertyForm(request.POST, instance=property_obj)
        food_form = FoodMenuForm(request.POST, instance=food_menu)
        images = request.FILES.getlist('images')

        if property_form.is_valid() and food_form.is_valid():
            property_obj = property_form.save()
            food_menu = food_form.save()

            # Save new images if uploaded
            for img in images:
                PropertyImage.objects.create(property=property_obj, image=img)

            # Re-verify listings on update
            property_obj.is_approved = False
            property_obj.save()

            messages.success(request, "Property updated! It has been submitted for admin re-verification.")
            return redirect('dashboard:dispatcher')

        return render(request, 'properties/property_form.html', {
            'property_form': property_form,
            'food_form': food_form,
            'image_form': PropertyImageForm(),
            'property': property_obj,
            'title': f'Edit Property: {property_obj.name}'
        })


class PropertyDeleteView(LoginRequiredMixin, VerifiedHostMixin, DeleteView):
    model = Property
    template_name = 'properties/property_confirm_delete.html'
    success_url = reverse_lazy('dashboard:dispatcher')

    def get_queryset(self):
        return Property.objects.filter(host=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Property listing deleted successfully.")
        return super().delete(request, *args, **kwargs)


class WishlistToggleView(LoginRequiredMixin, View):
    """View to toggle properties in user Wishlist"""
    def post(self, request, pk):
        property_obj = get_object_or_404(Property, pk=pk)
        from .models import Wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, property=property_obj)
        
        if wishlist_item.exists():
            wishlist_item.delete()
            added = False
            messages.success(request, f"Removed {property_obj.name} from your wishlist.")
        else:
            Wishlist.objects.create(user=request.user, property=property_obj)
            added = True
            messages.success(request, f"Added {property_obj.name} to your wishlist.")
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'added': added, 'status': 'success'})
            
        return redirect(request.META.get('HTTP_REFERER', reverse('properties:detail', kwargs={'pk': pk})))


class ExperienceCreateView(LoginRequiredMixin, VerifiedHostMixin, CreateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'properties/experience_form.html'
    success_url = reverse_lazy('dashboard:dispatcher')

    def form_valid(self, form):
        form.instance.host = self.request.user
        messages.success(self.request, "Signature local experience created successfully!")
        return super().form_valid(form)


class ExperienceUpdateView(LoginRequiredMixin, VerifiedHostMixin, UpdateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'properties/experience_form.html'
    success_url = reverse_lazy('dashboard:dispatcher')

    def get_queryset(self):
        return Experience.objects.filter(host=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Local experience details updated successfully!")
        return super().form_valid(form)


class ExperienceDeleteView(LoginRequiredMixin, VerifiedHostMixin, DeleteView):
    model = Experience
    template_name = 'properties/experience_confirm_delete.html'
    success_url = reverse_lazy('dashboard:dispatcher')

    def get_queryset(self):
        return Experience.objects.filter(host=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Signature experience removed.")
        return super().delete(request, *args, **kwargs)


class DestinationWishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from .models import Destination
        destination = get_object_or_404(Destination, pk=pk)
        wishlist_item = Wishlist.objects.filter(user=request.user, destination=destination)
        if wishlist_item.exists():
            wishlist_item.delete()
            messages.success(request, f"Removed {destination.name} from your wishlist.")
        else:
            Wishlist.objects.create(user=request.user, destination=destination)
            messages.success(request, f"Added {destination.name} to your wishlist.")
        return redirect(request.META.get('HTTP_REFERER', reverse('core:home')))


class ExperienceWishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        experience = get_object_or_404(Experience, pk=pk)
        wishlist_item = Wishlist.objects.filter(user=request.user, experience=experience)
        if wishlist_item.exists():
            wishlist_item.delete()
            messages.success(request, f"Removed {experience.title} from your wishlist.")
        else:
            Wishlist.objects.create(user=request.user, experience=experience)
            messages.success(request, f"Added {experience.title} to your wishlist.")
        return redirect(request.META.get('HTTP_REFERER', reverse('core:home')))


class DestinationDetailView(DetailView):
    model = Destination
    template_name = 'properties/destination_detail.html'
    context_object_name = 'destination'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destination = self.object
        
        # Stays in this destination
        context['properties'] = Property.objects.filter(destination=destination, is_approved=True)
        
        # Experiences offered in this destination area
        context['experiences'] = Experience.objects.filter(host__properties__destination=destination).distinct()
        
        # Top Hosts operating in this destination
        context['hosts'] = HostProfile.objects.filter(user__properties__destination=destination, verification_status=HostProfile.VerificationStatus.APPROVED).distinct()[:4]
        
        # Wishlist status
        context['in_wishlist'] = False
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(user=self.request.user, destination=destination).exists()
            
        return context

