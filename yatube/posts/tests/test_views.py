import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()

NUM_OF_POSTS_CREATE = 12
POSTS_PER_PAGE = 10


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='one',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:posts_list'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}): (
                        'posts/group_list.html'),
            reverse('posts:profile', kwargs={
                'username': self.user.username}): (
                'posts/profile.html'),
            reverse('posts:post_detail', kwargs={
                'post_id': PostPagesTests.post.pk}): (
                    'posts/post_detail.html'),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': PostPagesTests.post.pk}): (
                    'posts/create_post.html'),
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_list_page_show_correct_context(self):
        """Шаблон post_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:posts_list'))
        first_object = response.context.get('page_obj').object_list[0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, (
            PostPagesTests.post.author))
        self.assertEqual(post_group_0, Group.objects.get(pk=1))
        self.assertEqual(post_image_0.name, f'posts/{self.uploaded.name}')

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:post_detail', kwargs={
                        'post_id': PostPagesTests.post.pk})))
        self.assertEqual(response.context.get
                         ('post').author,
                         PostPagesTests.post.author)
        self.assertEqual(response.context.get('post').text,
                         'Тестовый пост')
        self.assertEqual(response.context.get('post').group,
                         PostPagesTests.group)
        self.assertEqual(response.context.get(
            'post').image.name, f'posts/{self.uploaded.name}')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={
                'slug': PostPagesTests.group.slug}))
        first_object = response.context.get(
            'page_obj').object_list[0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, (
            PostPagesTests.post.author))
        self.assertEqual(post_group_0, PostPagesTests.group)
        group_object = response.context.get('group')
        self.assertEqual(group_object, (
            PostPagesTests.group))
        self.assertEqual(post_image_0.name, f'posts/{self.uploaded.name}')

    def test_profile_list_page_show_correct_context(self):
        """Шаблон profile_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user.username}))
        first_object = response.context.get('page_obj').object_list[0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_author_0, (
            PostPagesTests.post.author))
        self.assertEqual(post_group_0, PostPagesTests.group)
        author_object = response.context.get('author')
        self.assertEqual(author_object, (
            PostPagesTests.post.author))
        self.assertEqual(post_image_0.name, f'posts/{self.uploaded.name}')

    def test_post_create_pages_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': PostPagesTests.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        is_edit_context = response.context.get('is_edit')
        self.assertTrue(is_edit_context)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='one',
            description='Тестовое описание',
        )
        cls.post = []
        for _ in range(NUM_OF_POSTS_CREATE):
            cls.post.append(Post(
                text='Тестовый пост',
                author=cls.user,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.post)

    def test_paginator_page_contains_three_records(self):
        """Проверяем паждинатор для posts_list."""
        response = self.client.get(
            reverse('posts:posts_list'))
        self.assertEqual(len(response.context['page_obj']),
                         POSTS_PER_PAGE)
        response = self.client.get(reverse(
            'posts:posts_list') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), (
            NUM_OF_POSTS_CREATE - POSTS_PER_PAGE))

    def test_group_paginator_page_contains_three_records(self):
        """Проверяем паждинатор для group_list."""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={
                'slug': PaginatorViewsTest.group.slug}))
        self.assertEqual(len(response.context[
            'page_obj']), POSTS_PER_PAGE)
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': PaginatorViewsTest.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), (
            NUM_OF_POSTS_CREATE - POSTS_PER_PAGE))

    def test_profile_paginator_page_contains_three_records(self):
        """Проверяем паждинатор для profile."""
        response = self.client.get(
            reverse('posts:posts_list'))
        self.assertEqual(len(response.context['page_obj']),
                         POSTS_PER_PAGE)
        response = self.client.get(reverse(
            'posts:profile', kwargs={
                'username': self.user.username}) + '?page=2')
        self.assertEqual(len(response.context[
            'page_obj']), NUM_OF_POSTS_CREATE - POSTS_PER_PAGE)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTests.user)

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first_state = self.authorized_client.get(reverse('posts:posts_list'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный пост'
        post_1.save()
        second_state = self.authorized_client.get(reverse('posts:posts_list'))
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(reverse('posts:posts_list'))
        self.assertNotEqual(first_state.content, third_state.content)
