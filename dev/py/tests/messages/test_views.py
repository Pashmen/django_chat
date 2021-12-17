from django.contrib.auth import get_user_model
from django.urls import reverse

from dev.py.utils import CustomTestCase
from messages.forms import MessagesForm
from messages.models import Message


class TestDialogsView(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.create_user(cls)
        cls.URL = reverse("dialogs")

    def test_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.URL)

        self.assertTemplateUsed(
            response,
            "messages/dialogs.html"
        )

    def test_nonauthorised(self):
        self.assertCustomRedirects(
            self.URL, "/login/?next=" + self.URL,
            302, 200
        )


class TestDialogView(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user_model().objects.create(
            id=1, username="1",
            email="1@email.com",
        )
        cls.user2 = get_user_model().objects.create(
            id=2, username="2",
            email="2@email.com",
        )
        cls.url1 = reverse("dialog", args=[1])
        cls.url2 = reverse("dialog", args=[2])

    def test_nonauthorised(self):
        self.assertCustomRedirects(
            self.url1,
            "/login/?next=" + self.url1,
            302, 200
        )

    def test_user_cant_message_self(self):
        self.client.force_login(self.user1)
        self.assertCustomRedirects(
            self.url1, reverse("dialogs"),
            302, 200
        )

    def test_existing_interlocutor(self):
        self.client.force_login(self.user1)
        response = self.client.get(self.url2)

        self.assertTemplateUsed(response, "messages/dialog.html")
        self.assertIsInstance(response.context["form"], MessagesForm)
        self.assertEqual(response.context["interlocutor"], self.user2)

    def test_nonexisting_interlocutor___no_messages(self):
        self.client.force_login(self.user1)
        self.assertCustomRedirects(
            reverse("dialog", args=[3]), reverse("dialogs"),
            302, 200
        )

    def test_nonexisting_interlocutor___with_messages(self):
        Message.objects.create(
            sender_id=1, receiver_id=3, text="text1"
        )
        self.client.force_login(self.user1)
        response = self.client.get(reverse("dialog", args=[3]))

        self.assertTemplateUsed(
            response,
            "messages/dialog_with_deleted_interlocutor.html"
        )


class TestMainPageView(CustomTestCase):
    def test(self):
        self.assertCustomRedirects(
            "/", reverse("dialogs"),
            302, 302
        )
