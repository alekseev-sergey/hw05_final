from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_pages_uses_correct_template(self):
        """URL использует корректные шаблоны HTML"""
        template_pages_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, reverse_name in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
