from django.urls import resolve
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from dev.py.utils import CustomTestCase
from messages.views import dialog_view
from messages.views import dialogs_view
from messages.views import main_page_view


class TestUrls(CustomTestCase):
    def test_main_page(self):
        self.assertEqual(resolve("/").func, main_page_view)

    def test_dialogs(self):
        self.assertEqual(reverse("dialogs"), "/dialogs/")
        self.assertEqual(resolve("/dialogs/").func, dialogs_view)

    def test_dialog(self):
        self.assertEqual(reverse("dialog", args=[123]), "/dialogs/u123/")
        self.assertRaises(NoReverseMatch, reverse, "dialog", args=[-123])
        self.assertRaises(NoReverseMatch, reverse, "dialog", args=[0])
        self.assertEqual(resolve("/dialogs/u123/").func, dialog_view)
