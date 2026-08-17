from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Avg, Count

from bookings.models import Booking, PassportBadge
from properties.models import Property, Wishlist
from accounts.models import HostProfile, User
from payments.models import Payment

class DispatcherDashboardView(LoginRequiredMixin, View):
    """Dispatcher view redirecting users to the dashboard that fits their role"""
    def get(self, request):
        if request.user.is_admin():
            return redirect('dashboard:admin_dashboard')
        elif request.user.is_host():
            return redirect('dashboard:host_dashboard')
        else:
            return redirect('dashboard:tourist_dashboard')


class TouristDashboardView(LoginRequiredMixin, View):
    """Tourist Dashboard displaying booking history and wishlist"""
    def get(self, request):
        if request.user.is_host():
            return redirect('dashboard:host_dashboard')
            
        bookings = Booking.objects.filter(guest=request.user).select_related('property', 'payment')
        wishlist = Wishlist.objects.filter(user=request.user).select_related('property').prefetch_related('property__images')
        passport_badges = PassportBadge.objects.filter(user=request.user)
        
        return render(request, 'dashboard/tourist.html', {
            'bookings': bookings,
            'wishlist': wishlist,
            'passport_badges': passport_badges
        })


class HostDashboardView(LoginRequiredMixin, View):
    """Host Dashboard displaying properties list, bookings manager, and earnings calculation"""
    def get(self, request):
        if not request.user.is_host():
            return redirect('dashboard:tourist_dashboard')

        properties = Property.objects.filter(host=request.user).prefetch_related('images', 'reviews')
        
        # All bookings for host's properties
        bookings = Booking.objects.filter(
            property__host=request.user
        ).select_related('property', 'guest', 'payment')
        
        # Calculate total earnings from approved bookings
        completed_earnings = Booking.objects.filter(
            property__host=request.user,
            status=Booking.StatusChoices.APPROVED
        ).aggregate(total=Sum('total_price'))['total'] or 0.0

        # Host profile status
        host_profile = getattr(request.user, 'host_profile', None)

        return render(request, 'dashboard/host.html', {
            'properties': properties,
            'bookings': bookings,
            'completed_earnings': completed_earnings,
            'host_profile': host_profile
        })


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Admin Dashboard displaying verification queues and platform statistics"""
    def test_func(self):
        return self.request.user.is_admin()

    def get(self, request):
        # Queues
        pending_hosts = HostProfile.objects.filter(
            verification_status=HostProfile.VerificationStatus.PENDING
        ).select_related('user')
        
        pending_properties = Property.objects.filter(
            is_approved=False
        ).select_related('host')

        # Statistics
        total_tourists = User.objects.filter(user_type=User.Types.TOURIST).count()
        total_hosts = User.objects.filter(user_type=User.Types.HOST).count()
        total_bookings = Booking.objects.count()
        
        total_revenue = Booking.objects.filter(
            status=Booking.StatusChoices.APPROVED
        ).aggregate(total=Sum('total_price'))['total'] or 0.0
        
        # System status lists for approvals
        return render(request, 'dashboard/admin.html', {
            'pending_hosts': pending_hosts,
            'pending_properties': pending_properties,
            'stats': {
                'tourists': total_tourists,
                'hosts': total_hosts,
                'bookings': total_bookings,
                'revenue': total_revenue
            }
        })


class AdminVerifyHostView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Admin action view to approve or reject a host profile request"""
    def test_func(self):
        return self.request.user.is_admin()

    def post(self, request, profile_id, action):
        profile = get_object_or_404(HostProfile, id=profile_id)
        notes = request.POST.get('verification_notes', '')

        if action == 'approve':
            profile.verification_status = HostProfile.VerificationStatus.APPROVED
            # Set user active and verified
            profile.user.email_verified = True
            profile.user.save()
        elif action == 'reject':
            profile.verification_status = HostProfile.VerificationStatus.REJECTED
        
        profile.verification_notes = notes
        profile.save()
        return redirect('dashboard:admin_dashboard')


class AdminApprovePropertyView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Admin action view to approve or reject a property listing"""
    def test_func(self):
        return self.request.user.is_admin()

    def post(self, request, property_id, action):
        property_obj = get_object_or_404(Property, id=property_id)
        
        if action == 'approve':
            property_obj.is_approved = True
            property_obj.save()
        elif action == 'reject':
            # Simply delete or mark unapproved
            property_obj.is_approved = False
            property_obj.save()
            
        return redirect('dashboard:admin_dashboard')
