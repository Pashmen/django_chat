from django.urls import reverse

from dev.py.utils import CustomTestCase


class TestBase(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.create_p_user(cls)

    def test_nonauthorised(self):
        html_code = self.render("base.html")

        self.assertIn(
            '<a href="{}">Log In'.format(reverse("login")),
            html_code
        )

    def test_authorised_common(self):
        html_code = self.render(
            "base.html", is_authorised=True,
            request_user_attrs={"unread_dialogs_exist": True}
        )
        self.assertIn(
            '<a href="{}">'.format(reverse("account")),
            html_code
        )
        self.assertIn(
            '<a href="{}" id="logout">Log Out'.format(reverse("logout")),
            html_code
        )

    def test_authorised_unread_dialogs_dont_exist(self):
        html_code = self.render(
            "base.html", is_authorised=True,
            request_user_attrs={"unread_dialogs_exist": False}
        )
        self.assertIn(
            '<a href="{}" id="dialogs-link">Dialogs'.format(
                reverse("dialogs")
            ),
            html_code
        )

    def test_authorised_unread_dialogs_exist(self):
        self.data = {"page_owner": self.user}
        html_code = self.render(
            "base.html", self.data, is_authorised=True,
            request_user_attrs={"unread_dialogs_exist": True}
        )
        self.assertIn(
            '<a href="{}" id="dialogs-link" '
            'class="unread-dialogs-exist">Dialogs'.format(
                reverse("dialogs"),
            ),
            html_code
        )

    def test_debug_for_js(self):
        with self.settings(DEBUG=True):
            html_code = self.render(
                "base.html", is_authorised=True,
            )
            self.assertIn(
                '<div id="is_debug" data-is-debug="true" style="display: none"',
                html_code
            )

        with self.settings(DEBUG=False):
            html_code = self.render(
                "base.html", is_authorised=True,
            )
            self.assertIn(
                '<div id="is_debug" data-is-debug="false" style="display: none',
                html_code
            )

    def test_base_js(self):
        self.data = {"is_debug": True}
        html_code = self.render(
            "base.html", self.data, is_authorised=True,
        )
        self.assertIn(
            '<script type="text/javascript" src="/static/common/js/base.js">',
            html_code
        )


class TestAccount(CustomTestCase):
    def test(self):
        html_code = self.render(
            "common/account.html", is_authorised=True,
            request_user_attrs={"username": "name"}
        )
        self.assertIn("<title>Account</title>", html_code)
        self.assertIn(
            "Your username: {}".format("name"), html_code
        )
