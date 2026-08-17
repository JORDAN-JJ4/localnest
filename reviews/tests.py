from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from properties.models import Property
from bookings.models import Booking
from reviews.models import Review

User = get_user_model()

class ReviewTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username='host_review',
            password='testpassword123',
            user_type=User.Types.HOST
        )
        self.tourist = User.objects.create_user(
            username='tourist_review',
            password='testpassword123',
            user_type=User.Types.TOURIST
        )
        self.property = Property.objects.create(
            host=self.host,
            name='Scenic Nest',
            description='A scenic homestay.',
            price_per_night=800.00,
            max_guests=2,
            private_room=True,
            check_in_time='12:00:00',
            check_out_time='11:00:00',
            address='Kullu',
            city='Kullu',
            state='Himachal',
            latitude=32.0,
            longitude=77.0,
            languages_spoken='English',
            is_approved=True
        )
        self.booking = Booking.objects.create(
            property=self.property,
            guest=self.tourist,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=2),
            guest_count=1,
            status=Booking.StatusChoices.APPROVED
        )

    def test_review_creation(self):
        """Verifies review star criteria and relationship binds"""
        review = Review.objects.create(
            property=self.property,
            author=self.tourist,
            booking=self.booking,
            overall_rating=5,
            food_rating=4,
            cleanliness_rating=5,
            host_behaviour_rating=5,
            cultural_experience_rating=4,
            comments='Absolutely amazing food and host hospitality!'
        )
        self.assertEqual(review.overall_rating, 5)
        self.assertEqual(self.property.get_average_rating(), 5.0)

    def test_invalid_star_ratings_raise_errors(self):
        """Verifies ratings outside 1-5 scale throw ValidationError"""
        invalid_review = Review(
            property=self.property,
            author=self.tourist,
            booking=self.booking,
            overall_rating=6,  # Out of bounds
            food_rating=0,     # Out of bounds
            cleanliness_rating=5,
            host_behaviour_rating=5,
            cultural_experience_rating=4,
            comments='Bad rating ranges.'
        )
        with self.assertRaises(ValidationError):
            invalid_review.full_clean()
