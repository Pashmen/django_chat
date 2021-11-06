from django.conf import settings
from django.utils import timezone

from dev.py.utils import CustomTestCase
from messages.managers import hash_time
from messages.models import Message


class TestMessages(CustomTestCase):
    def setUp(self):
        self.user1_id = 1
        self.user2_id = 2
        self.time = timezone.now()
        self.text = "text"
        self.message = Message(
            time=self.time,
            sender_id=self.user1_id, receiver_id=self.user2_id,
            text=self.text, is_unread=False
        )

    def test__fields(self):
        self.assertEqual(len(Message().__dict__), 9)

        self.assertEqual(Message.id.field.editable, False)
        self.assertEqual(Message.time.field.auto_now, True)
        self.assertEqual(Message.time.field.editable, False)
        self.assertEqual(Message.sender_id.field.editable, False)
        self.assertEqual(Message.sender_id.field.db_index, True)
        self.assertEqual(Message.receiver_id.field.editable, False)
        self.assertEqual(Message.receiver_id.field.db_index, True)
        self.assertEqual(
            Message.text.field.max_length,
            settings.FS_MAX_MESSAGE_LENGTH
        )
        self.assertEqual(Message.text.field.editable, False)
        self.assertEqual(Message.is_unread.field.default, True)
        self.assertEqual(Message.is_deleted_by_sender.field.default, False)
        self.assertEqual(Message.is_deleted_by_receiver.field.default, False)

    def test_as_dict(self):
        message_as_dict = {
            "time": self.time.strftime("%Y.%m.%d %H:%M:%S"),
            "user_owns_message": True,
            "is_unread": False,
            "text": self.text,
            "hash": hash_time(self.time)
        }
        self.assertEqual(
            self.message.as_dict(self.user1_id),
            message_as_dict
        )

        message_as_dict["user_owns_message"] = False
        self.assertEqual(
            self.message.as_dict(self.user2_id),
            message_as_dict
        )

        self.message.is_unread = True
        message_as_dict["is_unread"] = True
        self.assertEqual(
            self.message.as_dict(self.user2_id),
            message_as_dict
        )

    def test__str__(self):
        self.assertEqual(self.message.__str__(), self.text)
