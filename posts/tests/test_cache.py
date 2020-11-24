from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.test import TransactionTestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class CachIndexTest(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key = make_template_fragment_key('index_page')
        cls.user = User.objects.create_user(username='User-1')
        cls.authorized_client = Client()        
        cls.authorized_client.force_login(cls.user)

    def test_cache_after_time(self):
        response_before = self.authorized_client.get(reverse('index'))
        new_group = Group(title='Тестовая группа', slug='testgroup', id=1)
        new_group.save()
        new_post = Post.objects.create(
            text='Новый пост', 
            author=self.user,
            group=new_group,
        )
        response_after = self.authorized_client.get(reverse('index'))
        self.assertEqual(response_before.content, response_after.content)
        cache.touch(self.key, 0)
        response_last = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(response_before.content, response_last.content)
        