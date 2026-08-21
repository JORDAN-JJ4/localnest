from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, TemplateView, View, DetailView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy, reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from .models import HostProfile, Profile
from .forms import TouristRegistrationForm, HostRegistrationForm, TouristProfileForm, HostProfileForm
from properties.models import Property, Experience, Wishlist
from reviews.models import Review

User = get_user_model()

def send_verification_email(request, user):
    """Generates token and sends a verification link via email"""
    try:
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'uidb64': uidb64, 'token': token})
        )
        
        subject = "Verify your LocalNest Account"
        message = f"Hi {user.username},\n\nWelcome to LocalNest! Please click the link below to verify your email address:\n{verify_url}\n\nLive Like a Local!\nLocalNest Team"
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Non-fatal error in send_verification_email: {e}")


class TouristRegisterView(CreateView):
    model = User
    form_class = TouristRegistrationForm
    template_name = 'accounts/register_tourist.html'
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        send_verification_email(self.request, user)
        # Log the user in directly after registration
        login(self.request, user)
        messages.success(self.request, "Account created successfully! A verification email has been sent.")
        return response


class HostRegisterView(CreateView):
    model = User
    form_class = HostRegistrationForm
    template_name = 'accounts/register_host.html'
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        send_verification_email(self.request, user)
        login(self.request, user)
        messages.success(self.request, "Host registration complete! Your details are pending admin review.")
        return response


class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.email_verified = True
            user.save()
            messages.success(request, "Your email has been verified successfully! You can now access your dashboard.")
            return redirect('dashboard:dispatcher')
        else:
            messages.error(request, "The verification link was invalid or has expired.")
            return render(request, 'accounts/verification_failed.html')


class RegistrationSuccessView(TemplateView):
    template_name = 'accounts/registration_success.html'


class CustomLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard:dispatcher')


class CustomLogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('core:home')


class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_host():
            profile = get_object_or_404(HostProfile, user=request.user)
            form = HostProfileForm(instance=profile)
            template_name = 'accounts/edit_host_profile.html'
        else:
            profile = get_object_or_404(Profile, user=request.user)
            form = TouristProfileForm(instance=profile)
            template_name = 'accounts/edit_tourist_profile.html'
        
        return render(request, template_name, {'form': form, 'profile': profile})

    def post(self, request):
        if request.user.is_host():
            profile = get_object_or_404(HostProfile, user=request.user)
            form = HostProfileForm(request.POST, request.FILES, instance=profile)
            template_name = 'accounts/edit_host_profile.html'
        else:
            profile = get_object_or_404(Profile, user=request.user)
            form = TouristProfileForm(request.POST, request.FILES, instance=profile)
            template_name = 'accounts/edit_tourist_profile.html'
        
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('dashboard:dispatcher')
            
        return render(request, template_name, {'form': form, 'profile': profile})


class CustomPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully!")
        return super().form_valid(form)


class CustomPasswordChangeDoneView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/password_change_done.html'


class HostDetailView(DetailView):
    model = HostProfile
    template_name = 'accounts/host_profile_detail.html'
    context_object_name = 'host_profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        host_user = self.object.user
        
        # Listings & Experiences
        context['properties'] = Property.objects.filter(host=host_user, is_approved=True)
        context['experiences'] = Experience.objects.filter(host=host_user)
        
        # Reviews context
        reviews = Review.objects.filter(property__host=host_user)
        context['reviews'] = reviews
        context['reviews_count'] = reviews.count()
        
        # Calculate overall host stats
        ratings = [p.get_average_rating() for p in Property.objects.filter(host=host_user) if p.get_average_rating() > 0]
        context['average_rating'] = round(sum(ratings) / len(ratings), 2) if ratings else 5.0
        
        # Wishlist status
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(user=self.request.user, host=host_user).exists()
            
        return context


class HostWishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        host_profile = get_object_or_404(HostProfile, pk=pk)
        host_user = host_profile.user
        wishlist_item = Wishlist.objects.filter(user=request.user, host=host_user)
        if wishlist_item.exists():
            wishlist_item.delete()
            messages.success(request, f"Removed {host_user.username} from your wishlist.")
        else:
            Wishlist.objects.create(user=request.user, host=host_user)
            messages.success(request, f"Saved {host_user.username} to your wishlist.")
        return redirect(request.META.get('HTTP_REFERER', reverse('accounts:host_profile_detail', kwargs={'pk': pk})))
