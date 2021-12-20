from django.urls import reverse

from dev.py.utils import CustomTestCase


class TestAccountView(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.create_user(cls)
        cls.URL = reverse("account")

    def test_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.URL)

        self.assertTemplateUsed(
            response,
            "common/account.html"
        )

    def test_nonauthorised(self):
        self.assertCustomRedirects(
            self.URL, "/login/?next=" + self.URL,
            302, 200
        )
