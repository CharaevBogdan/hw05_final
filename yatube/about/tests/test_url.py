from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class AboutUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')

    def setUp(self):
        self.guest_client = Client()
        self.guest_client.force_login(self.user)

    def test_pages_exists_at_desired_location(self):
        """Страницы /about/author/ и /about/tech/
        доступы неавторизованному пользователю
        """
        self.url_names_codes = {
            '/about/author/': 200,
            '/about/tech/': 200
        }
        for url, code in self.url_names_codes.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
