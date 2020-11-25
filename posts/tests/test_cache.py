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

    def test_cache(self):
        # Лента "до"
        response_get_before = self.authorized_client.get(reverse('index'))
        # Создаем новый пост
        new_group = Group(title='Тестовая группа', slug='testgroup')
        new_group.save()
        new_post = Post.objects.create(
            text='Новый пост', 
            author=self.user,
            group=new_group,
        )
        # Лента "после"
        response_get_after = self.authorized_client.get(reverse('index'))
        # Сравнение лент
        self.assertEqual(response_get_before.content, response_get_after.content)
        # Чистим кэш
        cache.clear()
        # Лента после очистки кэша
        response_cach_cleared = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(response_get_before.content, response_cach_cleared.content)
        