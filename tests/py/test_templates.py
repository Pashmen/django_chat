from unittest.mock import Mock

from dev.py.utils import CustomTestCase
from messages.forms import MessagesForm


class TestDialogWithDeletedInterlocutor(CustomTestCase):
    def test(self):
        html_code = self.render(
            "messages/dialog_with_deleted_interlocutor.html"
        )

        self.assertIn("<title> Dialog </title>", html_code)
        self.assertIn("This user was deleted", html_code)
        self.assertIn("<b> Messages </b>:", html_code)
        self.assertIn('<div id="dialog-messages">', html_code)


class TestDialog(CustomTestCase):
    def test(self):
        interlocutor = Mock(id=2, email="2@email.com")
        data = {
            "interlocutor": interlocutor,
            "form": MessagesForm()
        }
        html_code = self.render(
            "messages/dialog.html",
            data
        )

        self.assertIn("<title> 2 Dialog </title>", html_code)
        self.assertIn('<a href="/u2/"> 2@email.com </a>', html_code)
        self.assertIn("<b> Messages </b>:", html_code)
        self.assertIn('<div id="dialog-messages">', html_code)
        self.assertIn('<form id="form">', html_code)
        self.assertIn('id="id_text"', html_code)
        self.assertIn('<button type="submit" name="Send"> Send', html_code)
        self.assertIn(
            '<script type="module" src="/static/messages/js/dialog.js">',
            html_code
        )


class TestDialogs(CustomTestCase):
    def test(self):
        html_code = self.render("messages/dialogs.html")

        self.assertIn("<title> Dialogs </title>", html_code)
        self.assertIn('<div id="dialogs">', html_code)
        self.assertIn(
            '<script type="module" src = "/static/messages/js/dialogs.js">',
            html_code
        )
