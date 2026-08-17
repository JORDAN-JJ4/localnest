from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from properties.models import Property
from bookings.models import Booking

User = get_user_model()

class BookingTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username='host_test',
            password='testpassword123',
            user_type=User.Types.HOST
        )
        self.tourist = User.objects.create_user(
            username='tourist_test',
            password='testpassword123',
            user_type=User.Types.TOURIST
        )
        self.property = Property.objects.create(
            host=self.host,
            name='Orchard Stay',
            description='Calm orchard retreat.',
            price_per_night=1000.00,
            max_guests=2,
            private_room=True,
            check_in_time='12:00:00',
            check_out_time='11:00:00',
            address='Manali',
            city='Manali',
            state='Himachal',
            latitude=32.23,
            longitude=77.18,
            languages_spoken='English',
            is_approved=True
        )

    def test_booking_price_calculation(self):
        """Verifies total price defaults to price per night times number of nights"""
        start = date.today() + timedelta(days=1)
        end = date.today() + timedelta(days=4)  # 3 nights
        booking = Booking.objects.create(
            property=self.property,
            guest=self.tourist,
            start_date=start,
            end_date=end,
            guest_count=1
        )
        self.assertEqual(booking.total_price, 3000.00)

    def test_overlapping_booking_validation(self):
        """Verifies duplicate/overlapping bookings fail validation check"""
        start = date.today() + timedelta(days=1)
        end = date.today() + timedelta(days=5)
        
        # Approve first booking
        Booking.objects.create(
            property=self.property,
            guest=self.tourist,
            start_date=start,
            end_date=end,
            guest_count=1,
            status=Booking.StatusChoices.APPROVED
        )

        # Overlapping booking attempt
        overlapping_booking = Booking(
            property=self.property,
            guest=self.tourist,
            start_date=start + timedelta(days=2),
            end_date=start + timedelta(days=4),
            guest_count=1
        )
        
        with self.assertRaises(ValidationError):
            overlapping_booking.clean()
