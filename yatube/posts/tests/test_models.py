from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Test_text' * 10,
            author=User.objects.create_user(username='TestUser',
                                            password='TestPass',
                                            email='testem@mail.com'),
        )

        cls.group = Group.objects.create(
            title='Test_title',
            slug='Test_slug',
            description='Test_desc'
        )

    def test_title_is_text_0_15(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_group_object_name_is_title(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
