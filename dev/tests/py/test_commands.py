from unittest.mock import Mock
from unittest.mock import patch

from django.core import mail

from dev.py.utils import CustomTestCase
from messages.management.commands.notify_about_new_messages import Command


class TestNotifyAboutNewMessages(CustomTestCase):
    M = "messages.management.commands.notify_about_new_messages"

    @patch(M + ".Message.objects.get_users_to_notify")
    @patch(M + ".mail.get_connection")
    def test(self, p_get_connection, p_get_users_to_notify):
        def get_email_message(contact, number):
            body_template = "Hello! You have new messages (number: {})"
            return mail.EmailMessage(
                subject="New messages",
                body=body_template.format(number),
                to=[contact]
            )
        email_notifications = [
            get_email_message("1@email.com", 3),
            get_email_message("2@email.com", 1),
        ]

        def get_user_info(method, contact, number):
            return {
                "method": method,
                "contact": contact,
                "new_messages_number": number
            }
        connection = Mock()
        connection.send_messages = Mock()
        p_get_connection.return_value = connection
        p_get_users_to_notify.return_value = [
            get_user_info("email", "1@email.com", 3),
            get_user_info("email", "2@email.com", 1),
            get_user_info("vk", "1@email.com", 3)
        ]

        cmd = Command()
        cmd.handle()
        call_arg = connection.send_messages.call_args[0][0]
        self.assertEqual(
            len(call_arg), len(email_notifications)
        )
        for i in range(len(call_arg)):
            self.assertEqual(
                call_arg[i].subject, email_notifications[i].subject
            )
            self.assertEqual(
                call_arg[i].body, email_notifications[i].body
            )
            self.assertEqual(
                call_arg[i].to, email_notifications[i].to
            )
