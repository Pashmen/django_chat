from django.conf import settings

from dev.py.utils import CustomTestCase
from messages.forms import MessagesForm


class TestMessagesForm(CustomTestCase):
    def test_text_max_length(self):
        self.assertEqual(
            MessagesForm.base_fields["text"].max_length,
            settings.FS_MAX_MESSAGE_LENGTH
        )

    def test_price(self):
        data = {"text": "a \r\n z"}
        form = MessagesForm(data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["text"], "a \n z")
