from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import datetime

from .models import Booking
from properties.models import Property
from payments.services import PaymentService
from payments.models import Payment
from notifications.models import Notification

class CreateBookingView(LoginRequiredMixin, View):
    """View to handle submitting check-in, check-out dates and creating booking requests"""
    def post(self, request, property_id):
        # Only tourists are allowed to book properties
        if not request.user.is_tourist():
            messages.error(request, "Only Tourist accounts can book properties.")
            return redirect('properties:detail', pk=property_id)

        property_obj = get_object_or_404(Property, pk=property_id, is_approved=True)
        
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        guest_count_str = request.POST.get('guest_count')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            guest_count = int(guest_count_str)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid check-in/check-out dates and guest counts.")
            return redirect('properties:detail', pk=property_id)

        # Build booking model instance to validate
        booking = Booking(
            property=property_obj,
            guest=request.user,
            start_date=start_date,
            end_date=end_date,
            guest_count=guest_count
        )

        try:
            booking.clean()
            booking.save()
        except ValidationError as e:
            messages.error(request, f"Booking Error: {e.message if hasattr(e, 'message') else e.messages[0]}")
            return redirect('properties:detail', pk=property_id)

        # Add experiences and recalculate price
        experience_ids = request.POST.getlist('experiences')
        if experience_ids:
            for exp_id in experience_ids:
                booking.experiences.add(exp_id)
            # Recalculate price: stay cost + (experiences cost * guests)
            nights = (end_date - start_date).days
            stay_cost = property_obj.price_per_night * nights
            exp_cost = sum(exp.price for exp in booking.experiences.all()) * guest_count
            booking.total_price = stay_cost + exp_cost
            booking.save()

        # Notify host about the new request
        Notification.objects.create(
            user=property_obj.host,
            title="New Booking Request",
            message=f"You have received a new booking request for '{property_obj.name}' from {request.user.get_full_name() or request.user.username}.",
            notification_type=Notification.Types.SYSTEM
        )

        messages.success(request, "Booking request submitted! Please select your payment method.")
        return redirect('bookings:select_payment', booking_id=booking.id)


class SelectPaymentView(LoginRequiredMixin, View):
    """View to choose between Cash on Arrival and simulated online payments"""
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
        online_order = PaymentService.generate_online_order(booking)
        return render(request, 'bookings/select_payment.html', {
            'booking': booking,
            'online_order': online_order
        })

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
        payment_method = request.POST.get('payment_method')

        if payment_method not in [Payment.PaymentMethod.CASH_ON_ARRIVAL, Payment.PaymentMethod.RAZORPAY]:
            messages.error(request, "Invalid payment method selected.")
            return redirect('bookings:select_payment', booking_id=booking.id)

        # Initialize payment instance
        payment = PaymentService.initialize_payment(booking, payment_method)

        if payment_method == Payment.PaymentMethod.CASH_ON_ARRIVAL:
            PaymentService.process_cash_payment(payment)
            messages.success(request, "Your booking request is complete! Your payment is set to Cash on Arrival.")
            return redirect('dashboard:dispatcher')
        else:
            # For Razorpay (online) simulated path:
            # We redirect to a simulated payment success processor
            return redirect('bookings:simulated_checkout', booking_id=booking.id)


class SimulatedCheckoutView(LoginRequiredMixin, View):
    """Simple view to simulate payment success callback for testing Razorpay integration"""
    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
        return render(request, 'bookings/simulated_checkout.html', {
            'booking': booking
        })

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
        # Fetch or initialize payment
        payment, created = Payment.objects.get_or_create(
            booking=booking,
            defaults={'amount': booking.total_price, 'payment_method': Payment.PaymentMethod.RAZORPAY}
        )

        import uuid
        mock_payment_id = f"pay_mock_{uuid.uuid4().hex[:12]}"
        mock_order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
        mock_signature = "mock_sig_12345"

        success = PaymentService.verify_online_payment(payment, mock_payment_id, mock_order_id, mock_signature)
        if success:
            messages.success(request, "Simulated online payment successful!")
        else:
            messages.error(request, "Simulated online payment failed.")
            
        return redirect('dashboard:dispatcher')


class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Booking
    template_name = 'bookings/detail.html'
    context_object_name = 'booking'

    def test_func(self):
        booking = self.get_object()
        return self.request.user == booking.guest or self.request.user == booking.property.host

    def get_queryset(self):
        return Booking.objects.select_related('property__host', 'guest', 'payment')


def award_passport_badges(booking):
    from bookings.models import PassportBadge
    
    # Check if badges already exist for this booking to avoid duplication
    if PassportBadge.objects.filter(booking=booking).exists():
        return
        
    # Award Destination Badge
    dest_name = booking.property.destination.name if booking.property.destination else booking.property.city
    PassportBadge.objects.create(
        user=booking.guest,
        booking=booking,
        badge_type=PassportBadge.BadgeType.DESTINATION,
        title=f"{dest_name} Pioneer",
        icon="bi-geo-alt-fill"
    )
    
    # Award Culture Badge
    PassportBadge.objects.create(
        user=booking.guest,
        booking=booking,
        badge_type=PassportBadge.BadgeType.CULTURE,
        title=f"{dest_name} Culture Scholar",
        icon="bi-bookmark-heart-fill"
    )
    
    # Award Food Badge
    PassportBadge.objects.create(
        user=booking.guest,
        booking=booking,
        badge_type=PassportBadge.BadgeType.FOOD,
        title=f"{dest_name} Culinary Connoisseur",
        icon="bi-egg-fried"
    )
    
    # Award Experience Badge if they booked experiences
    if booking.experiences.exists():
        exp_title = booking.experiences.first().title
        PassportBadge.objects.create(
            user=booking.guest,
            booking=booking,
            badge_type=PassportBadge.BadgeType.EXPERIENCE,
            title=f"{exp_title} Champion",
            icon="bi-award-fill"
        )
    else:
        # Default Experience badge
        PassportBadge.objects.create(
            user=booking.guest,
            booking=booking,
            badge_type=PassportBadge.BadgeType.EXPERIENCE,
            title=f"{dest_name} Explorer",
            icon="bi-compass-fill"
        )


class BookingStatusUpdateView(LoginRequiredMixin, View):
    """View for host to approve or reject guest bookings"""
    def post(self, request, booking_id, action):
        booking = get_object_or_404(Booking, id=booking_id, property__host=request.user)

        if action == 'approve':
            try:
                booking.status = Booking.StatusChoices.APPROVED
                booking.save()
                
                # Award Passport Badges automatically
                award_passport_badges(booking)
                
                # Notify guest
                Notification.objects.create(
                    user=booking.guest,
                    title="Booking Request Approved!",
                    message=f"Your booking for homestay '{booking.property.name}' has been approved by the host family.",
                    notification_type=Notification.Types.BOOKING_APPROVED
                )
                messages.success(request, "Booking approved and passport badges awarded successfully!")
            except ValidationError as e:
                messages.error(request, f"Error: {e.messages[0]}")
        elif action == 'reject':
            booking.status = Booking.StatusChoices.REJECTED
            booking.save()
            
            # Notify guest
            Notification.objects.create(
                user=booking.guest,
                title="Booking Request Declined",
                message=f"Unfortunately, your booking request for '{booking.property.name}' was declined by the host family.",
                notification_type=Notification.Types.BOOKING_CANCELLED
            )
            messages.success(request, "Booking request declined.")
            
        return redirect('dashboard:dispatcher')


class BookingCancelView(LoginRequiredMixin, View):
    """View for guests to cancel their pending or approved bookings"""
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
        
        # Save old status for notification text
        old_status = booking.status
        
        booking.status = Booking.StatusChoices.CANCELLED
        booking.save()

        # Notify host
        Notification.objects.create(
            user=booking.property.host,
            title="Booking Cancelled by Guest",
            message=f"The booking request from {request.user.get_full_name() or request.user.username} for '{booking.property.name}' was cancelled by the guest.",
            notification_type=Notification.Types.BOOKING_CANCELLED
        )

        messages.success(request, "Booking cancelled successfully.")
        return redirect('dashboard:dispatcher')
