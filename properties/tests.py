from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from properties.models import Property, FoodMenu, Amenity

User = get_user_model()

class PropertyTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username='host_tester',
            password='testpassword123',
            user_type=User.Types.HOST
        )
        self.amenity_wifi = Amenity.objects.create(name='Wi-Fi', icon='bi-wifi')
        
        self.property = Property.objects.create(
            host=self.host,
            name='Scenic Mountain Nest',
            description='Enjoy fresh air and organic apples.',
            price_per_night=1500.00,
            max_guests=4,
            private_room=True,
            check_in_time='12:00:00',
            check_out_time='11:00:00',
            address='123 Orchard Lane',
            city='Manali',
            state='Himachal',
            latitude=32.2396,
            longitude=77.1887,
            languages_spoken='Hindi, English',
            is_approved=True
        )
        self.property.amenities.add(self.amenity_wifi)
        
        self.food_menu = FoodMenu.objects.create(
            property=self.property,
            breakfast_included=True,
            breakfast_details='Paratha with curd',
            vegetarian=True,
            non_vegetarian=False
        )

    def test_property_creation(self):
        """Verifies property field constraints and food relationships"""
        self.assertEqual(self.property.name, 'Scenic Mountain Nest')
        self.assertTrue(self.property.food_menu.vegetarian)
        self.assertEqual(self.property.amenities.count(), 1)

    def test_property_search_view(self):
        """Verifies search endpoint displays matching listings and applies filters"""
        search_url = reverse('properties:search')
        
        # Test basic match
        response = self.client.get(search_url, {'q': 'Scenic'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Scenic Mountain Nest')

        # Test location filter match
        response = self.client.get(search_url, {'state': 'Himachal'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Scenic Mountain Nest')
        
        # Test non-matching location filter
        response = self.client.get(search_url, {'state': 'Kerala'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Scenic Mountain Nest')
