import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()


class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Bogdan')
        cls.group = Group.objects.create(title='test_title',
                                         slug='Test_slug',
                                         description='Test_desc',
                                         )
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('posts:index'),
            'group.html': reverse('posts:group',
                                  kwargs={'slug': self.group.slug}),
            'new.html': reverse('posts:new_post'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон posts:index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, self.post.text)

    def test_group_page_shows_correct_context(self):
        """Шаблон posts:group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, self.post.text)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон posts:new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_show_correct_context(self):
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:edit', kwargs={'username': self.user.username,
                                          'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_context(self):
        """Страница posts:profile сформирована с корректным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        first_object = response.context['author']
        second_object = response.context['page'][0]
        post_author = first_object.username
        post_text = second_object.text
        self.assertEqual(post_author, self.user.username)
        self.assertEqual(post_text, self.post.text)

    def test_post_page_shows_correct_context(self):
        """Страница posts:post сформирована с корректным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post', kwargs={'username': self.user.username,
                                          'post_id': self.post.id})
        )
        first_object = response.context['author']
        second_object = response.context['post']
        post_author = first_object.username
        post_text = second_object.text
        self.assertEqual(post_author, self.user.username)
        self.assertEqual(post_text, self.post.text)

    def test_new_post_with_group_diplayed_on_index_page(self):
        """При создании пост появится на главной"""
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        first_object = response.context['page'][0]
        post_group_title = first_object.group.title
        self.assertEqual(post_group_title, self.group.title)

    def test_new_post_with_group_diplayed_on_group_page(self):
        """При создании пост появится на странице группы"""
        response = self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page'][0]
        post_group_title = first_object.group.title
        self.assertEqual(post_group_title, self.group.title)

    def test_authorized_client_can_subscribe(self):
        """Авторизованный юзер может подписываться и отписываться"""
        self.user2 = User.objects.create(username='tester')
        # нет подписок
        self.assertFalse(
            self.user2.following.all().exists()
        )
        # перешел по кнопке подписаться
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user2.username})
        )
        # проверил, подписка появилась
        self.assertTrue(
            self.user2.following.filter(user=self.user).exists()
        )

    def test_authorized_client_can_unsubscribe(self):
        """Авторизованный пользователь может отписываться"""
        # создаем юзера2 и подписываем на него юзера 1
        self.user2 = User.objects.create(username='tester')
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user2.username})
        )
        self.assertTrue(
            self.user2.following.filter(user=self.user).exists()
        )
        # все проверили подписка появилась, теперь отписываем
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user2.username})
        )
        # подписка исчезла
        self.assertFalse(
            self.user2.following.filter(user=self.user).exists()
        )

    def test_new_page_exists_on_follow_index(self):
        self.user2 = User.objects.create(username='tester')
        self.user3 = User.objects.create(username='tes')
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user2.username})
        )
        new_post = Post.objects.create(
            text='sample', author=self.user2
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context.get('page')[0].text, new_post.text
        )
        # Cчитаю посты для ауторайзед клиента
        count_of_posts_on_follow_index = len(
            response.context.get('page').object_list
        )
        # Создаю пост юзером на которого не подписан ауторайзед клиент.
        Post.objects.create(
            text='tes',
            author=self.user3
        )
        # Пост не поялвляется в фолоу индексе.
        self.assertEqual(
            len(response.context.get('page').object_list),
            count_of_posts_on_follow_index
        )

    def test_only_authorized_client_can_comment(self):
        """Только авторизованный пользователь может комментировать посты"""
        self.form_data = {
            'text': 'sample_text'
        }
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}),
            data=self.form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(author=self.user,
                                   post=self.post,
                                   text=self.form_data['text']).exists()
        )

    def test_guest_client_cant_comment(self):
        self.form_data = {
            'text': 'sample_text'
        }
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}),
            data=self.form_data,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(author=self.user,
                                   post=self.post,
                                   text=self.form_data['text']).exists()
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        number_of_posts_per_page = 10
        cls.user = User.objects.create_user(username='TestBro')
        cls.group = Group.objects.create(title='test_title',
                                         slug='test_slug',
                                         description='test_desc')

        for i in range(number_of_posts_per_page + 3):
            cls.post = Post.objects.create(text=f'Test_text{i}',
                                           author=cls.user,
                                           group=cls.group)

    def setUp(self):

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Первая страница показывает 10 постов."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        """Вторая страница показывает оставшиеся посты(3)."""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_first_pages_contains_ten_records(self):
        """Первые страницы posts:index, posts:group, posts:profile
        отображают по 10 постов
        """
        page_names = {
            reverse('posts:index'): 10,
            reverse('posts:group',
                    kwargs={'slug':
                            f'{PaginatorViewsTest.post.group.slug}'}): 10,
            reverse('posts:profile',
                    kwargs={'username':
                            f'{PaginatorViewsTest.post.author}'}): 10,
        }
        for reverse_name, expected_number in page_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                posts_on_page = len(response.context.get('page').object_list)
                self.assertEqual(posts_on_page, expected_number)

    def test_second_page_contains_three_records(self):
        """Вторые страницы путей posts:index, posts:group, posts:profile
        отображают по 3 поста
        """
        page_names = {
            reverse('posts:index') + '?page=2': 3,
            reverse('posts:group',
                    kwargs={'slug':
                            f'{PaginatorViewsTest.post.group.slug}'}
                    ) + '?page=2': 3,
            reverse('posts:profile',
                    kwargs={'username':
                            f'{PaginatorViewsTest.post.author}'}
                    ) + '?page=2': 3,
        }
        for reverse_name, expected_number in page_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                posts_on_page = len(response.context.get('page').object_list)
                self.assertEqual(posts_on_page, expected_number)


class CacheTestView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='User')
        cls.post = Post.objects.create(text='Text',
                                       author=cls.user)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_cache(self):
        """Кэширование на странице index работает корректно"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        # контент по дефолту
        content_before_new = response.content
        Post.objects.create(text='qwerty', author=self.user)
        response = self.authorized_client.get(reverse('posts:index'))
        # взял контент с новым постом.
        content_after_new = response.content
        # сравнил, они равны - кэш работает
        self.assertEqual(
            content_after_new, content_before_new
        )
        # почистил кэш взял контент, он не равен с первоначальным
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        content_after_cache_clear = response.content
        self.assertNotEqual(
            content_before_new, content_after_cache_clear
        )


class ImagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='TestBro')
        cls.group = Group.objects.create(title='test_title',
                                         slug='test_slug',
                                         description='test_desc')
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B'
                     )
        uploaded = SimpleUploadedFile(name='small.gif',
                                      content=small_gif,
                                      content_type='image/gif'
                                      )
        cls.post = Post.objects.create(text='Sample_text',
                                       author=cls.user,
                                       group=cls.group,
                                       image=uploaded,
                                       )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()

    def test_image_shows_correctly_on_pages_with_paginator(self):
        """Картинка отображается на страницах: -group,
                                               -profile,
        """
        target_responses = {
            'group': self.guest_client.get(
                reverse('posts:group', kwargs={'slug': self.group.slug})
            ),
            'profile': self.guest_client.get(
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ),
        }
        for response in target_responses.values():
            with self.subTest(response=response):
                self.assertEqual(
                    response.context['page'][0].image, self.post.image
                )

    def test_image_shows_correctly_on_indexpage(self):
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            response.context['page'][0].image, self.post.image
        )

    def test_images_shows_correctly_on_single_post_page(self):
        """Картинка отображается на странице поста."""
        cache.clear()
        response = self.guest_client.get(
            reverse('posts:post',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id})
        )
        self.assertEqual(
            response.context['post'].image, self.post.image
        )
