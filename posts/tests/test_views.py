from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User, Comment, Follow


class PostPagesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Sergey')
        cls.second_user = User.objects.create(username='Oleg')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Текст',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client_non_author = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.second_user_client = Client()
        self.second_user_client.force_login(self.second_user)

    def test_posts_pages_uses_correct_template(self):
        """URL использует корректные шаблоны HTML"""
        template_pages_names = {
            'group.html': reverse('group_posts', kwargs={'slug': 'test-slug'}),
            'index.html': reverse('index'),
            'follow.html': reverse('follow_index'),
            'posts/new.html': reverse('new_post'),
            'posts/post.html': reverse(
                'post', kwargs={'username': 'Sergey', 'post_id': 1}
            ),
            'posts/profile.html': reverse(
                'profile', kwargs={'username': 'Sergey'}
            ),
        }
        for template, reverse_name in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_post_page_uses_correct_template(self):
        """URL c именем post_edit использует корректный шаблон"""
        response = self.authorized_user.get(
            reverse('post_edit', kwargs={'username': 'Sergey', 'post_id': 1}))
        self.assertTemplateUsed(response, 'posts/new.html')

    def test_new_post_page_show_correct_context_index(self):
        """Проверка заполнения формы нового поста"""
        response = self.authorized_user.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_page_show_correct_context(self):
        """Шаблон group/<slug:slug>/ сформирован с правильным контекстом"""
        response = self.authorized_user.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(response.context['group'].title, 'Заголовок')
        self.assertEqual(response.context['group'].description, 'Текст')
        self.assertEqual(response.context['group'].slug, 'test-slug')

    def test_group_post(self):
        """На странице группы отображается новый пост."""
        response = self.authorized_user.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'}))
        expected = self.post
        self.assertEqual(response.context['page'][0], expected)

    def test_index_pagenator_show(self):
        """Проверка главной страницы с паджинатором"""
        response = self.guest_client.get(reverse('index'))
        actual_post = response.context.get('page').object_list
        self.assertListEqual(list(actual_post), list(Post.objects.all()[:10]))

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_user.get(reverse('index'))
        post_author = response.context['page'][0].author
        post_text = response.context['page'][0].text
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_text, 'Тестовый текст')

    def test_creat_posts_index_group_pages_and_count_posts_(self):
        """Создает пост и проверяет его появление на страницах index, group"""
        Post.objects.create(text='Новый текст', author=self.user)
        response_group = self.authorized_user.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'})
        )
        response_index = self.authorized_user.get(reverse('index'))
        self.assertEqual(len(response_group.context['page']), 1)
        self.assertEqual(len(response_index.context['page']), 2)

    def test_cache(self):
        """Главная страница корректно кэширует список записей."""
        first_response = self.guest_client.get(reverse('index'))
        first_post = first_response.context['page'][0]
        self.post.text = 'Новый пост'
        second_response = self.guest_client.get(reverse('index'))
        second_post = second_response.context['page'][0]
        self.assertEqual(first_post, second_post)

    def test_auth_user_can_comment(self):
        """Только авторизированный пользователь может комментировать посты."""
        users = {
            self.guest_client: False,
            self.authorized_user: True,
        }
        for user, expected in users.items():
            with self.subTest(user=user):
                form_data = {'text': 'Комментарий', }
                user.post(
                    reverse('add_comment',
                            args=[self.authorized_user, self.post.id]),
                    data=form_data,
                    follow=True,
                )
                actual = Comment.objects.filter(
                    post=self.post,
                    author=self.user,
                    text=form_data['text'],
                ).exists()
                self.assertEqual(actual, expected)

    def test_new_post_exist_for_followers(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан на него."""
        post_second_user = Post.objects.create(
            text='Тестовый пост второго пользователя',
            author=self.second_user,
            group=self.group,
        )
        follow = reverse('profile_follow', args=[self.second_user])
        self.authorized_user.get(follow)

        response = self.authorized_user.get(reverse('follow_index'))
        actual = response.context['page'][0]
        expected = post_second_user

        self.assertEqual(actual, expected)

        response = self.second_user_client.get(reverse('follow_index'))
        actual = response.context['paginator'].count

        self.assertEqual(actual, 0)

    def test_auth_user_can_follow_unfollow(self):
        """Проверка подписки и отписки от автора"""
        urls = {
            reverse('profile_follow', args=[self.second_user]): True,
            reverse('profile_unfollow', args=[self.second_user]): False,
        }
        for url, expected in urls.items():
            with self.subTest(url=url):
                self.authorized_user.get(url)
                actual = Follow.objects.filter(
                    user=self.user,
                    author=self.second_user
                ).exists()
                self.assertEqual(actual, expected)
