from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.second_user = User.objects.create_user(username='Anonymous')
        cls.post = Post.objects.create(
            text='Test_text' * 10,
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='Test_title',
            slug='Test_slug',
            description='Test_desc'
        )
        cls.templates_url_names = {
            'posts/index.html': '/',
            'posts/group.html': f'/group/{cls.group.slug}/',
            'posts/new.html': {'new': '/new/',
                               'edit':
                                f'/{cls.user.username}/{cls.post.id}/edit/'},
            'posts/profile.html': f'/{cls.user.username}/',
            'posts/post.html': f'/{cls.user.username}/{cls.post.id}/'}
        cls.url_for_group_which_not_exists = '/group/wrong_slug/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.second_authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.second_authorized_client.force_login(self.second_user)

    def test_home_url_exists_at_desired_location(self):
        """Главная доступна любому пользователю."""
        response = self.guest_client.get(
            self.templates_url_names['posts/index.html'])
        self.assertEqual(response.status_code, 200)

    def test_group_slug_exists_at_desired_location(self):
        """Страница /group/<slug>/ любому пользователю."""
        response = self.guest_client.get(
            self.templates_url_names['posts/group.html'])
        self.assertEqual(response.status_code, 200)

    def test_new_exists_at_desired_location_authorized(self):
        """Страница /new доступна авторизованному
        пользователю.
        """
        response = self.authorized_client.get(
            self.templates_url_names['posts/new.html']['new'])
        self.assertEqual(response.status_code, 200)

    def test_new_redirect_anonymous(self):
        """Страница /new перенапрявляет
        неавторизованного пользователя.
        """
        response = self.guest_client.get(
            self.templates_url_names['posts/new.html']['new'], follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_urls_uses_correct_template(self):
        """Однотипные тесты шаблонов через SubTest"""
        self.templates_url_names = {
            'index.html': '/',
            'group.html': '/group/Test_slug/',
            'new.html': '/new/',
        }
        for template, adress in self.templates_url_names.items():
            with self.subTest(adress=adress):
                cache.clear()
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_profile_page_exists_at_desired_location(self):
        """Страница profile доступна любому пользователю"""
        response = self.guest_client.get(
            self.templates_url_names['posts/profile.html'])
        self.assertEqual(response.status_code, 200)

    def test_single_post_page_exists_at_desired_location(self):
        """Страница /<username>/<post_id> доступна любому пользователю"""
        response = self.guest_client.get(
            self.templates_url_names['posts/post.html'])
        self.assertEqual(response.status_code, 200)

    def test_post_edit_page_exists_for_anonymous(self):
        """Страница /<username>/<post_id>/edit
        не доступна для анонимуса.
        """
        response = self.guest_client.get(
            self.templates_url_names['posts/new.html']['edit'])
        self.assertNotEqual(response.status_code, 200)

    def test_post_edit_page_exists_for_author(self):
        """Страница /<username>/<post_id>/edit доступна для
        авторизованного пользователя - автора поста.
        """
        response = self.authorized_client.get(
            self.templates_url_names['posts/new.html']['edit'])
        self.assertEqual(response.status_code, 200)

    def test_post_edit_page_exists_for_not_author(self):
        """Страница /<username>/<post_id>/edit доступна для
        авторизованного пользователя - НЕ автора поста.
        """
        response = self.second_authorized_client.get(
            self.templates_url_names['posts/new.html']['edit'])
        self.assertEqual(response.status_code, 200)

    def test_post_edit_page_uses_correct_template(self):
        """Страница edit использует правильный шаблон"""
        response = self.authorized_client.get(
            self.templates_url_names['posts/new.html']['edit'])
        self.assertTemplateUsed(response, 'new.html')

    def test_post_edit_page_redirects_anonymous(self):
        """Редирект со транцы /<username>/<post_id>/edit верно редиректит
        неавторизованного пользователя"""
        response = self.guest_client.get(
            self.templates_url_names['posts/new.html']['edit'])
        self.assertRedirects(response, '/auth/login/?next=/test/1/edit/')

    def test_server_returns_404_when_page_is_not_exist(self):
        """Сервер возвращает код 404, если страница не найдена"""
        response = self.guest_client.get(
            self.url_for_group_which_not_exists
        )
        self.assertEqual(response.status_code, 404)
