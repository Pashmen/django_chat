from django.conf import settings
from django.core import mail
from django.core.management.base import BaseCommand

from messages.models import Message


class Command(BaseCommand):
    def handle(self, *args, **options):
        email_notifications = []
        body_template = "Hello! You have new messages (number: {})"
        for user_info in Message.objects.get_users_to_notify():
            if user_info["method"] == settings.FS_EMAIL_METHOD:
                email_notifications.append(mail.EmailMessage(
                    subject="New messages",
                    body=body_template.format(user_info["new_messages_number"]),
                    to=[user_info["contact"]]
                ))

        connection = mail.get_connection()
        connection.send_messages(email_notifications)
