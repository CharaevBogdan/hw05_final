import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Bogdan')
        cls.group = Group.objects.create(title='t_title',
                                         slug='t_slug',
                                         description='t_desc',
                                         id=1)
        cls.group2 = Group.objects.create(title='t2_title',
                                          slug='t2_slug',
                                          description='t2_desc',
                                          id=2)
        cls.url_reverses = {
            'my_target_url': reverse('posts:new_post'),
            'login_url': reverse('login'),
        }
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        # Модуль shutil - библиотека Python с прекрасными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок|файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.post = Post.objects.create(text='t_text',
                                        author=self.user,
                                        group=self.group,
                                        id=1)
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        target_redirect = reverse('posts:index')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, target_redirect)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image__endswith=form_data['image'].name
            ).exists()
        )

    def test_created_by_form_post_adds_to_db(self):
        """Пост создается в базе после отправки формы"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        post_1 = Post.objects.first()
        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(post_1.group.id, form_data['group'])
        self.assertEqual(post_1.author.username, self.user.username)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, 200)

    def test_annonymous_cant_add_posts_to_db(self):
        """Неавторизованный пользователь не может создавать пост"""
        posts_count = Post.objects.count()
        login_url = self.url_reverses["login_url"]
        target_url = self.url_reverses["my_target_url"]

        target_redirects = f'{login_url}?next={target_url}'
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:new_post'),
            data=form_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, target_redirects)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edited_post_adds_to_db(self):
        """Отредактированный пост обновляется в базе
        после отправки формы
        """
        form_data = {
            'text': 'Текст для теста',
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            reverse('posts:edit', kwargs={'username': self.user.username,
                                          'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': self.group.id}))

        post_1 = Post.objects.get(id=1)

        self.assertRedirects(response, reverse('posts:post',
                             kwargs={'username': self.user.username,
                                     'post_id': self.post.id}))

        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(response.status_code, 200)

        self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': self.group.id}))

        self.assertFalse(
            Post.objects.filter(
                group=self.group,
                text=self.post.text,
            ).exists()
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
                                       id=1
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
