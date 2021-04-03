from django.test import TestCase, Client

from posts.models import Group, Post, User, Comment


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AUTHOR = 'Sergey'
        cls.NON_AUTHOR = 'Andrey'
        cls.POST_ID = 1
        cls.user = User.objects.create(username=cls.AUTHOR)
        cls.user_non_author = User.objects.create(username=cls.NON_AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-group',
            description='тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст',
            pub_date='15.01.2021',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            text="Текст тестового комментария",
            author=cls.user,
            created='03.04.2021',
            post=cls.post
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_non_author = Client()
        self.authorized_client_non_author.force_login(self.user_non_author)

    def test_about_url_exists_at_desired_location(self):
        """Проверка возвращения сревером код 404 если страница не найдена"""
        response = self.guest_client.get('/a1b2r3a/')
        self.assertEqual(response.status_code, 404)

    def test_pages_urls_exists_at_desired_location(self):
        """Проверка доступа к страницам авторизованным пользователем"""
        pages = {
            'new_post': '/new/',
            'post_edit': f'/{self.AUTHOR}/{self.POST_ID}/edit/',
            'follow_index': '/follow/',
        }
        for name, url in pages.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_pages_urls_exists_at_desired_location_anonymos(self):
        """Проверка доступа к страницам неавторизованным пользвателем"""
        pages = {
            'homepage': '',
            'group': '/group/test-group/',
            'profile': f'/{self.AUTHOR}/',
            'post': f'/{self.AUTHOR}/{self.POST_ID}/',
        }
        for name, url in pages.items():
            with self.subTest(name=name):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_follow_page_anonymous(self):
        """Проверка доступа неавторизованного пользователя к странице
        follow"""
        response = self.guest_client.get('/follow/')
        self.assertEqual(response.status_code, 302)

    def test_post_edit_page_anonymous(self):
        """Проверка доступа неавторизованного пользователя к странице
        <post_id>/edit/"""
        response = self.guest_client.get(
            f'/{self.AUTHOR}/{self.POST_ID}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_post_edit_page_second_user(self):
        """Проверка доступа другого пользователя к странице
        <post_id>/edit/"""
        response = self.authorized_client_non_author.get(
            f'/{self.AUTHOR}/{self.POST_ID}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_pages_redirect_anonymous(self):
        """Страницы перенаправят неавторизованного пользователя на
        страницу авторизации"""
        pages = {
            '/new/': '/auth/login/?next=/new/',
            f'/{self.AUTHOR}/{self.POST_ID}/edit/':
            f'/auth/login/?next=/{self.AUTHOR}/{self.POST_ID}/edit/',
        }
        for name, url in pages.items():
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.assertRedirects(response, url)

    def test_edit_url_authorize_user(self):
        """Страница доступна для редактирования поста авторизованным
        пользователем"""
        response = self.authorized_client.get(
            f'/{self.AUTHOR}/{self.POST_ID}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '': 'index.html',
            '/follow/': 'follow.html',
            '/new/': 'posts/new.html',
            '/group/test-group/': 'group.html',
            f'/{self.AUTHOR}/': 'posts/profile.html',
            f'/{self.AUTHOR}/{self.POST_ID}/': 'posts/post.html',
            f'/{self.AUTHOR}/{self.POST_ID}/edit/': 'posts/new.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
