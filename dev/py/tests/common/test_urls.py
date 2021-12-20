from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.urls import resolve
from django.urls import reverse

from common.views import account_view
from dev.py.utils import CustomTestCase


class TestUrls(CustomTestCase):
    def test_slash_redirect(self):
        self.assertCustomRedirects("/dialogs", "/dialogs/", 301, 302)

    def test_admin(self):
        self.assertEqual(resolve("/admin/").func.__name__, "index")

    def test_login(self):
        self.assertEqual(reverse("login"), "/login/")

        self.assertEqual(
            resolve("/login/").func.view_class,
            LoginView
        )

    def test_logout(self):
        self.assertEqual(reverse("logout"), "/logout/")

        self.assertEqual(
            resolve("/logout/").func.view_class,
            LogoutView
        )

    def test_account(self):
        self.assertEqual(reverse("account"), "/account/")

        self.assertEqual(
            resolve("/account/").func,
            account_view
        )
