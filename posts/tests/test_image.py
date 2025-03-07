from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import response
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from posts.models import Group
from posts.models import Post


User = get_user_model()


class ImageTests(TestCase):

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

    def test_create_post_with_image(self):
        self.assertEqual(Post.objects.count(), 0)
        username = 'Testuser1' 
        authorized_client = self.new_authorized_client(username)
        author = User.objects.get(username=username)
        new_group = self.new_group('group_1')
        new_group.save()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
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
        response = authorized_client.post(
            reverse('new_post'), 
            {
                'text': 'Это текст публикации',
                'author': author,
                'group': new_group.id,
                'image': uploaded,
            }, 
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)  

    def test_edit_post_with_image(self):
        self.assertEqual(Post.objects.count(), 0)
        username = 'my-user'
        authorized_client = self.new_authorized_client(username)
        author = User.objects.get(username=username)
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
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
        new_post = Post.objects.create(
            text='Пост авторизованного пользователя', 
            author=author,
            image=uploaded,
        )
        self.assertIsNotNone(new_post)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, 'Пост авторизованного пользователя')
        self.assertIsNone(post.group)
        self.assertEqual(post.author.username, username)
        new_group = self.new_group('group_1')
        new_group.save()
        small_gif_2 = (b'\x47\x49\x46\x38\x39\x61\x02\x01'
                b'\x01\x01\x80\x00\x01\x00\x00\x01'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x01'
                b'\x01\x01\x00\x2C\x00\x00\x01\x00'
                b'\x02\x00\x01\x00\x01\x02\x02\x0C'
                b'\x0A\x00\x3B'
        )
        uploaded_edit = SimpleUploadedFile(
            name='small_2.gif',
            content=small_gif_2,
            content_type='image/gif'
        )
        authorized_client.post(
            reverse(
                'post_edit', 
                kwargs={'username': author, 'post_id': post.id}
            ),
            {
                'text': 'Это отредактированная публикация', 
                'author': author,
                'group': new_group.id,
                'image': uploaded_edit,
            },
            follow=True
        )
        post.refresh_from_db()
        self.assertEqual(post.text, 'Это отредактированная публикация')
        self.assertEqual(post.group, new_group)
        self.assertEqual(post.author.username, username)       

    def test_image_on_pages(self):
        self.assertEqual(Post.objects.count(), 0)
        username = 'Testuser1' 
        authorized_client = self.new_authorized_client(username)
        author = User.objects.get(username=username)
        new_group = self.new_group('group_1')
        new_group.save()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
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
        Post.objects.create(
            text='Новый пост', 
            author=author, 
            group=new_group,
            image=uploaded,
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.last()
        urls = [
            reverse('post', kwargs={'username': username, 'post_id': post.id}),
            reverse('index'),
            reverse('profile', kwargs={'username': username}),
            reverse('group', kwargs={'slug': 'group_1'}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = authorized_client.get(url)
                self.assertContains(response, '<img')
    
    def test_post_with_not_image(self):
        self.assertEqual(Post.objects.count(), 0)
        username = 'Testuser1' 
        authorized_client = self.new_authorized_client(username)
        author = User.objects.get(username=username)
        new_group = self.new_group('group_1')
        new_group.save()
        txt_file = SimpleUploadedFile(
            'test.txt', 
            b'this is text not image',
            content_type='text/plain'
        )
        response = authorized_client.post( 
            reverse('new_post'), 
            {
                'text': 'Пост авторизованного пользователя',
                'author': author, 
                'group': new_group.id, 
                'image': txt_file,
            }, 
            follow=True 
            )
        self.assertFormError(
            response, 
            'form', 
            'image', 
            'Загрузите правильное изображение. ' 
            'Файл, который вы загрузили, поврежден или не является изображением.'
        )
