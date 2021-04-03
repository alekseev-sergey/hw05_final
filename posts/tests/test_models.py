from django.test import TestCase

from posts.models import Comment, Post, Group, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Sergey')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст' * 20,
            pub_date='15.01.2021',
            author=cls.user,
            group=cls.group,
        )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        help_texts = {
            'text': 'Введите текст',
            'group': 'Выберите группу',
        }
        for value, expected in help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'текст',
            'pub_date': 'Дата публикации',
            'author': 'автор',
            'group': 'группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_object_name_is_title_field(self):
        """Метод __str__ переводит group в строку с содержимым group.title"""
        group = PostModelTest.group
        expected_object_name_group = group.title
        self.assertEquals(expected_object_name_group, str(group))

    def test_object_name_post_is_title_field(self):
        """Метод __str__ переводит text в строку с содержимым post.text и
        проверяет срез в 15 символов"""
        post = PostModelTest.post
        expected_object_name_post = post.text
        self.assertEquals(expected_object_name_post[:15], str(post))


class CommentModelTest(TestCase):

    @classmethod
    def setUp(cls):
        cls.user = User.objects.create(username='Sergey')
        cls.post = Post.objects.create(
            text='Текст поста' * 20,
            pub_date='15.01.2021',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text="Текст комментария",
            author=cls.user,
            created='03.04.2021',
            post=cls.post
        )

    def test_verbose_name_comment(self):
        """verbose_name в поле совпадает с ожидаемым"""
        comment = CommentModelTest.comment
        field_verboses = {
            'text': 'Текст комментария',
            'created': 'Дата публикации',
            'post': 'Комментарий',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)
