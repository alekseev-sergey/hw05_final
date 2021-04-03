import shutil
import tempfile

from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Group, Post, User, Comment


class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создали временную папку для медиа файлов
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.guest_client = Client()
        cls.user = User.objects.create(username='Sergey')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Текст',
            pub_date='15.01.2021',
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):
        """Проверка перенаправления на главную страницу после создания поста"""
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
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, '/')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Новый пост',
            group=self.group.id,
            image='posts/small.gif').exists()
        )

    def test_edit_post(self):
        """Проверка редактирования поста через форму на странице
        /<username>/<post_id>/edit/ на изменение соответствующей записи
        в базе данных"""
        post_edit_page = reverse(
            "post_edit",
            kwargs={'username': self.user, 'post_id': self.post.id},
        )
        post_page = reverse(
            "post", kwargs={'username': self.user, 'post_id': self.post.id})
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            post_edit_page,
            data=form_data,
        )
        verbose = Post.objects.get(pk=self.post.id).text
        self.assertRedirects(response, post_page)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEquals(verbose, form_data['text'])


class TestCommentForm(TestCase):
    @classmethod
    def setUp(cls):
        cls.AUTHOR = 'Sergey'
        cls.guest_client = Client()
        cls.user_author = User.objects.create(username=cls.AUTHOR)
        cls.user_author_client = Client()
        cls.user_author_client.force_login(cls.user_author)
        cls.test_post = Post.objects.create(
            text='Test post',
            author=cls.user_author,
        )

    def test_add_comment(self):
        """Форма добавляет комментарий и редиректит обратно на пост."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Новый комментарий', }
        args = [self.user_author.username, self.test_post.id]
        response = self.user_author_client.post(
            reverse('add_comment', args=args),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse("post", args=args))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Новый комментарий',
                                   author=self.user_author).exists()
        )
