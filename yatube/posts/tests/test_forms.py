import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='one',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='two',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=PostCreateFormTests.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        self.not_author = User.objects.create_user(username='Auth')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_create_post(self):
        """Проверяем создание поста авторизованным пользователем."""
        posts_count = Post.objects.count()
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
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data={
                'text': 'Тестовый текст',
                'image': uploaded,
            },
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                author=PostCreateFormTests.user,
                group=None,
                image='posts/small.gif'
            ).exists(),
        )

    def test_edit_post_authorized(self):
        """Проверяем что при POST запросе авторизованного
        пользователя пост будет отредактирован."""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostCreateFormTests.post.pk}),
            data={'text': 'Тестовый текст'},
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostCreateFormTests.post.pk})
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                author=PostCreateFormTests.user,
                group=None
            ).exists(),
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_unauthorized(self):
        """Проверяем что при POST запросе неавторизованного
        пользователя пост не будет отредактирован."""
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostCreateFormTests.post.pk}),
            data={'text': 'Тестовый текст2'},
            follow=True
        )
        self.assertRedirects(
            response, (
                f'/auth/login/?next=/posts/'
                f'{PostCreateFormTests.post.pk}/edit/'
            )
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                author=PostCreateFormTests.user,
                group=PostCreateFormTests.group.pk).exists(),
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post_unauthorized(self):
        """Проверяем что при POST запросе не будет создаваться
        новый пост для неавторизованного пользователя"""
        posts_count = Post.objects.count()
        self.guest_client.post(
            reverse('posts:post_create'),
            data={'text': 'Тестовый текст'},
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post_with_group(self):
        """Проверяем создание поста с группой
        авторизованным пользователем."""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Тестовый текст2',
                  'group': {PostCreateFormTests.group.pk},
                  },
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
                author=PostCreateFormTests.user,
                group=PostCreateFormTests.group.pk).exists(),
        )

    def test_edit_post_authorizedwith_group(self):
        """Проверяем что при POST запросе авторизованного
        пользователя группа у постa будет отредактирована."""
        self.post2 = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=PostCreateFormTests.group
        )
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post2.pk}),
            data={'text': 'Тестовый текст2',
                  'group': {PostCreateFormTests.group2.pk},
                  },
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': self.post2.pk})
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
                author=PostCreateFormTests.user,
                group=PostCreateFormTests.group2.pk
            ).exists(),
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_not_author(self):
        """Проверяем что при POST запросе не автора
        пост не будет отредактирован."""
        posts_count = Post.objects.count()
        response = self.not_author_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostCreateFormTests.post.pk}),
            data={'text': 'Тестовый текст2'},
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostCreateFormTests.post.pk}))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                author=PostCreateFormTests.user,
                group=PostCreateFormTests.group.pk
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count)
