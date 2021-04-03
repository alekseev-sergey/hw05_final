from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов"""
        pages = {
            'tech': '/about/tech/',
            'author': '/about/author/',
        }
        for name, url in pages.items():
            with self.subTest(name=name):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)
