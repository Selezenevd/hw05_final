from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, Client
from django.urls import reverse

from posts.models import Post
from posts.urls import urlpatterns


User = get_user_model()


class StaticURLTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Testuser1')
        cls.authorized_client = Client()        
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()
    
    def test_homepage(self):
        response = self.unauthorized_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
