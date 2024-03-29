from ..forms import PostForm
from ..models import Post, Group, Comment

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

import shutil
import tempfile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа_1',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):

        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_create_post(self):

        post_count = Post.objects.count()

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
            content_type='image/gif',
        )

        data_form = {
            'text': 'Тестовый текст_2',
            'group': self.group.pk,
            'image': uploaded,
        }

        response = self.author_client.post(
            reverse('posts:post_create'),
            data=data_form,
            follow=True,
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': f'{self.user.username}'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=data_form.get('text'),
                group=data_form.get('group'),

            ).exists()
        )

    def test_image_in_create(self):

        test_video = (
            b'test_video'
        )
        uploaded = SimpleUploadedFile(
            name='test_video.mp4',
            content=test_video,
            content_type='video/mp4',
        )

        data_form = {
            'text': 'Тестовый текст_3',
            'group': self.group.pk,
            'image': uploaded,
        }

        response = self.author_client.post(
            reverse('posts:post_create'),
            data=data_form,
            follow=True,
        )
        self.assertFormError(
            response, 'form', 'image', 'Загрузите правильное изображение. '
                                       'Файл, который вы загрузили, '
                                       'поврежден или не является '
                                       'изображением.'
        )

    def test_edit_post(self):

        post_count = Post.objects.count()

        test_kwargs = {'post_id': self.post.pk}

        data_edit = {
            'text': 'Проверка redirect',
            'group': self.group.pk,
        }

        response = self.author_client.post(
            reverse('posts:post_edit', kwargs=test_kwargs),
            data=data_edit,
            follow=True,
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs=test_kwargs))

        data_edit_form = {
            'text': 'Измененный текст',
            'group': self.group.pk,
        }
        self.author_client.post(
            reverse('posts:post_edit', kwargs=test_kwargs),
            data=data_edit_form,
            follow=True,
        )

        response_edit = Post.objects.get(pk=self.post.pk)
        self.assertTrue(
            data_edit_form.get('text') == response_edit.text,
            data_edit_form.get('group') == response_edit.group,
        )

        self.assertEqual(Post.objects.count(), post_count)


class CommentCreateFormTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create(username='auth')
        cls.author = User.objects.create(username='author')
        cls.text = {
            'text': 'Тестовый комментарий'
        }
        cls.group = Group.objects.create(
            title='Тестовая группа_1',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.auth)

    def test_create_comment(self):
        count = Post.objects.get(pk=self.post.pk).comments.count()

        self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=self.text,
        )

        self.assertEqual(
            Post.objects.get(pk=self.post.pk).comments.count(), count + 1)

    def test_redirect_after_comment(self):
        response = self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=self.text,
        )

        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.pk})
        )

    def test_check_context_comment(self):
        self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=self.text,
        )

        self.assertTrue(
            Comment.objects.filter(
                text=self.text.get('text'),
            ).exists()
        )
