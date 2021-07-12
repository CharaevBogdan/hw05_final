from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AboutViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')

    def setUp(self):
        self.guest_client = Client()
        self.guest_client.force_login(self.user)

    def test_pages_accessible_by_name(self):
        """URL, генерируемый при помощи имени, доступен."""
        self.url_names_codes = {
            'about:tech': 200,
            'about:author': 200
        }
        for url, code in self.url_names_codes.items():
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url))
                self.assertEqual(response.status_code, code)
