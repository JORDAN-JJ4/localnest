from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse

from .models import Review
from .forms import ReviewForm
from bookings.models import Booking

class SubmitReviewView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Allows tourists to submit reviews for properties after completed stays"""
    def test_func(self):
        booking = get_object_or_404(Booking, id=self.kwargs['booking_id'])
        # Only the guest of the booking can leave a review
        return self.request.user == booking.guest and booking.status == Booking.StatusChoices.APPROVED

    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        # Check if review already exists
        if hasattr(booking, 'review'):
            messages.error(request, "You have already submitted a review for this booking stay.")
            return redirect('dashboard:dispatcher')

        form = ReviewForm()
        return render(request, 'reviews/submit_review.html', {
            'form': form,
            'booking': booking
        })

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        if hasattr(booking, 'review'):
            messages.error(request, "You have already submitted a review for this booking stay.")
            return redirect('dashboard:dispatcher')

        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.property = booking.property
            review.author = request.user
            review.save()
            
            messages.success(request, "Thank you! Your feedback has been published successfully.")
            return redirect('dashboard:dispatcher')

        return render(request, 'reviews/submit_review.html', {
            'form': form,
            'booking': booking
        })


class LikeReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if request.user in review.likes.all():
            review.likes.remove(request.user)
            liked = False
        else:
            review.likes.add(request.user)
            liked = True
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'liked': liked, 'likes_count': review.likes.count()})
        return redirect(request.META.get('HTTP_REFERER', reverse('properties:detail', kwargs={'pk': review.property.id})))
