from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Этот будет автором
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='one',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост15345',
            group=PostURLTests.group
        )

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованного юзера, но не автора поста
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user)

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': (
                'posts/group_list.html'),
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/comment/': 'posts/comments.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_author(self):
        """URL-адрес использует соответствующий шаблон для автора."""
        response = self.author_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_uses_correct_template_unauthorized(self):
        """URL-адрес использует соответствующий шаблон для гостя."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': (
                'posts/group_list.html'),
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_404(self):
        """Проверяем несуществующию страницу"""
        response = self.author_client.get('/error/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_task_detail_url_redirect_anonymous_on_admin_login(self):
        """Страницы перенаправят анонимного пользователя на страницу
        логина."""
        templates_url_names = {
            f'/posts/{self.post.pk}/edit/': (
                f'/auth/login/?next=/posts/{self.post.pk}/edit/'),
            '/create/': '/auth/login/?next=/create/',
        }
        for address, redirect in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, redirect)

    def test_task_detail_url_redirect_anonymous_on_admin_login(self):
        """Редирект не автора на карточку поста."""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, (f'/posts/{self.post.pk}/'))
