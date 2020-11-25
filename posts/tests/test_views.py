from django.core.cache import cache
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from posts.models import  Comment, Follow, Group, Post, User


class ViewsTests(TestCase):

    def new_unauthorized_client(self):
        return Client()

    def new_group(self, slug):
        return Group.objects.create(
            title='Тестовая группа',
            slug=slug,
        )

    def new_authorized_client(self, username):
        user = User.objects.create(username=username)
        user.save()

        client = Client()
        client.force_login(user)
        return client

    def test_new_post(self):
        """Авторизованный пользователь может опубликовать пост"""
        current_posts_count = Post.objects.count()
        new_group = self.new_group('group_1')
        new_group.save()
        response = self.new_authorized_client('user-1').post(
            reverse('new_post'), 
            {'text': 'Это текст публикации', 'group': new_group.id}, 
            follow=True
        )
        self.assertEqual(
            response.status_code,
            200,
            'Функция добавления нового поста работает неправильно'
        )
        self.assertEqual(
            Post.objects.count(),
            current_posts_count + 1,
            'Новый пост не сохраняется в базе данных'
        )
        post = Post.objects.last()
        self.assertEqual(
            post.text,
            'Это текст публикации',
            'Текст сохранен некорректно'
        )
        self.assertEqual(
            post.author.username,
            'user-1',
            'Некорректно указан автор'
        )
        self.assertEqual(
            post.group.id,
            new_group.id,
            'Некорректно указана группа'
        )
        
    def test_new_profile(self):
        """После регистрации пользователя создается его персональная страница"""
        username = 'Testuser1'
        client = self.new_authorized_client(username)
        response = client.get(reverse(
            'profile', 
            kwargs={'username': username}
        ))
        self.assertEqual(
            response.status_code,
            200,
            'Персональная страница не создается после регистрации'
        )

    def test_unauthorized_user_newpage(self):
        """Неавторизованный посетитель не может опубликовать пост 
        (его редиректит на страницу входа)"""
        #Проверка количества постов до попытки публикации
        self.assertEqual(Post.objects.count(), 0)
        redirect_url = reverse('login') + '?next=' + reverse('new_post')
        # GET-запрос
        with self.subTest('GET'):
            response = self.new_unauthorized_client().get(reverse('new_post'))
            self.assertRedirects(
                response, redirect_url,
                status_code=302, target_status_code=200
            )
        # POST-запрос
        with self.subTest('POST'):
            response = self.new_unauthorized_client().post(reverse('new_post'))
            self.assertRedirects(
                response, redirect_url,
                status_code=302, target_status_code=200
            )
        #Проверка количества постов после попытки публикации
        self.assertEqual(Post.objects.count(), 0)

    def test_show_post(self):
        """После публикации поста новая запись появляется на главной 
        странице сайта (index), на персональной странице пользователя 
        (profile), и на отдельной странице поста (post)"""
        username = 'user-2'
        client = self.new_authorized_client(username)
        # После публикации поста
        new_group = Group(title='Тестовая группа', slug='testgroup', id=1)
        new_group.save()
        author = User.objects.get(username=username)
        new_post = Post.objects.create(
            text='Новый пост', 
            author=author, 
            group=new_group,
        )
        self.assertIsNotNone(new_post)
        urls = [
            reverse('index'), 
            reverse('profile', kwargs={'username': username}), 
        ]
        cache.clear()
        for url in urls:
            cache.clear()
            with self.subTest(url=url):
                cache.clear() 
                response = client.get(url)
                self.assertIn(new_post, response.context['page'].object_list)
        post_url = reverse(
            'post', 
            kwargs={'username': username, 'post_id': new_post.id}
        )
        with self.subTest(post_url):
            response = client.get(post_url)
            self.assertEqual(new_post, response.context['post'])

    def test_edit_post(self):
        """Авторизованный пользователь может отредактировать свой пост, 
        после этого содержимое поста изменится на всех связанных страницах."""
        self.assertEqual(Post.objects.count(), 0)
        username = 'my-user'
        authorized_client = self.new_authorized_client(username)
        author = User.objects.get(username=username)
        new_post = Post.objects.create(
            text='Пост авторизованного пользователя', 
            author=author,
        )
        self.assertIsNotNone(new_post)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, 'Пост авторизованного пользователя')
        self.assertIsNone(post.group)
        self.assertEqual(post.author.username, username)
        new_group = Group(title='Тестовая группа', slug='testgroup')
        new_group.save()
        authorized_client.post(
            reverse(
                'post_edit', 
                kwargs={'username': author, 'post_id': post.id}
            ),
            {
                'text': 'Это отредактированная публикация', 
                'group': new_group.id,
            },
            follow=True
        )
        post.refresh_from_db()
        self.assertEqual(post.text, 'Это отредактированная публикация')
        self.assertEqual(post.group, new_group)
        self.assertEqual(post.author.username, username)

    def test_404(self):
        client = Client()
        response = client.get(reverse('response_404'))
        self.assertEqual(
            response.status_code,
            404,
            'Страница не найдена'
        )

    def test_auth_follow_other_users(self):
        author = User.objects.create(username="Tester")
        follower_name = 'User-1'
        authorized_client = self.new_authorized_client(follower_name)
        self.assertEqual(author.following.count(), 0)
        authorized_client.get(
            reverse(
                "profile_follow",
                kwargs={"username": author},
            )
        )
        self.assertEqual(author.following.count(), 1)
        follow_exists = Follow.objects.filter(
            author=author, 
            user__username=follower_name).exists()
        self.assertTrue(follow_exists)

    def test_auth_follow_self(self):
        follower_name = 'User-1'
        authorized_client = self.new_authorized_client(follower_name)
        author = User.objects.get(username=follower_name)
        self.assertEqual(author.following.count(), 0)
        authorized_client.get(
            reverse(
                "profile_follow",
                kwargs={"username": author},
            )
        )
        self.assertEqual(author.following.count(), 0)
    
    def test_auth_follow_author_not_exists(self):
        authorized_client = self.new_authorized_client('User-1')
        response = authorized_client.get(
            "profile_follow", 
            kwargs = {"username": 'some_author'}
        )
        self.assertEqual(response.status_code, 404)

    def test_auth_unfollow(self):
        author = User.objects.create(username="Author")
        subscriber = User.objects.create(username="my-user1")
        subscription = Follow.objects.create(user=subscriber, author=author)
        client = Client()
        client.force_login(subscriber)   
        client.get(
            reverse(
                "profile_unfollow",
                kwargs={"username": author.username},
            )
        )
        self.assertEqual(author.following.count(), 0)
    
    def view_new_post_follow(self):
        author = User.objects.create(username="Author")
        subscriber = User.objects.create(username="User-1")
        not_subscriber = User.objects.create(username="User-2")
        subscription = Follow.objects.create(user=subscriber, author=author)
        author_post = Post.objects.create(
            text='Пост автора', 
            author=author,
        )
        with self.subTest(subscriber.username):
            client = self.new_authorized_client(subscriber.username) 
            response = client.get(reverse('follow_index'))
            self.assertContains(response.context['page'], author_post)
        with self.subTest(not_subscriber.username):
            client = self.new_authorized_client(not_subscriber.username) 
            response = client.get(reverse('follow_index'))
            self.assertNotContains(response.context['page'], author_post)

    def view_auth_add_comment(self):
        author = User.objects.create(username="Author")
        authorized_client = self.new_authorized_client(username='User-1')
        author_post = Post.objects.create(
            text='Пост автора', 
            author=author,
        )
        self.assertEqual(Comment.objects.count(), 0)
        comment_text = 'Новый комментарий'
        authorized_client.post(
            reverse(
                'add_comment', 
                kwargs={'username': author.username, 'post_id': author_post.id}
            ),
            {'text': comment_text},
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(
            Comment.objects.last(),
            comment_text,
            'Текст сохранен некорректно'
        )

    def view_unauth_add_comment(self):
        author = User.objects.create(username="Author")
        authorized_client = self.new_unauthorized_client()
        author_post = Post.objects.create(
            text='Пост автора', 
            author=author,
        )
        self.assertEqual(Comment.objects.count(), 0)
        authorized_client.post(
            reverse(
                'add_comment', 
                kwargs={'username': author.username, 'post_id': author_post.id}
            ),
            {'text': 'Новый комментарий'},
        )
        self.assertEqual(Comment.objects.count(), 0)
