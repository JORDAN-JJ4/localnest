from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import HostProfile, Profile

User = get_user_model()

class AccountTests(TestCase):
    def setUp(self):
        self.tourist_data = {
            'username': 'tourist_user',
            'password': 'testpassword123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'tourist@localnest.com',
            'phone_number': '1234567890',
            'address': 'Tourist Address'
        }
        self.host_data = {
            'username': 'host_user',
            'password': 'testpassword123',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'host@localnest.com',
            'phone_number': '0987654321',
            'address': 'Host Address',
            'bio': 'A lovely host family'
        }

    def test_tourist_creation_and_profile_signal(self):
        """Verifies custom user role creation and profile signal creation"""
        user = User.objects.create_user(
            username=self.tourist_data['username'],
            password=self.tourist_data['password'],
            email=self.tourist_data['email'],
            user_type=User.Types.TOURIST
        )
        self.assertTrue(user.is_tourist())
        self.assertFalse(user.is_host())
        # Check profile was created via signal
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_host_creation_and_profile_signal(self):
        """Verifies custom host creation and verification default state"""
        user = User.objects.create_user(
            username=self.host_data['username'],
            password=self.host_data['password'],
            email=self.host_data['email'],
            user_type=User.Types.HOST
        )
        self.assertTrue(user.is_host())
        # Check HostProfile verification status default
        self.assertTrue(HostProfile.objects.filter(user=user).exists())
        self.assertEqual(user.host_profile.verification_status, HostProfile.VerificationStatus.PENDING)

    def test_login_flow(self):
        """Verifies standard login redirection works"""
        user = User.objects.create_user(
            username='loginuser',
            password='loginpass123',
            user_type=User.Types.TOURIST
        )
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {'username': 'loginuser', 'password': 'loginpass123'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard:dispatcher'), target_status_code=302)

