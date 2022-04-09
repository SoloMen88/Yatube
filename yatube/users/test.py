from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class UserURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/auth/logout/': 'users/logged_out.html',
            # '/auth/password_change/': 'users/password_change_form.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template_signup(self):
        """URL-адрес использует соответствующий шаблон для автора."""
        response = self.guest_client.get(
            '/auth/signup/')
        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template_unauthorized(self):
        """URL-адрес использует соответствующий шаблон для гостя."""
        templates_url_names = {
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)
