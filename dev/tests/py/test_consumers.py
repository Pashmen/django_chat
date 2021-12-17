import json
from copy import deepcopy
from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import patch

import redis
from asgiref.sync import async_to_sync as ats
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.exceptions import ValidationError

from dev.py.utils import CustomTestCase
from messages.consumers import clear_group
from messages.consumers import CustomAsyncWebsocketConsumer
from messages.consumers import DialogConsumer
from messages.consumers import DialogsConsumer
from messages.consumers import get_dialog_group_name
from messages.consumers import get_dialogs_group_name
from messages.consumers import LOG_INFO_LEVEL
from messages.consumers import LOG_WARNING_LEVEL
from messages.forms import MessagesForm
from messages.managers import DialogIntegrityManager
from messages.managers import DialogsIntegrityManager
from messages.managers import hash_dialog
from messages.managers import hash_time
from messages.managers import UnreadDialogsManager
from messages.models import Message


channel_layer = get_channel_layer()
redis_cache = redis.Redis(
    decode_responses=True,
    db=settings.FS_REDIS_DB
)


class TestCustomAsyncWebsocketConsumer(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.consumer = CustomAsyncWebsocketConsumer()
        cls.consumer.group_name = "fake-group"
        cls.consumer.channel_name = "fake-channel-name"
        cls.consumer.name = "name"
        cls.consumer.type = "type"

    def setUp(self):
        self.consumer.channel_layer = channel_layer

    def test_disconnect(self):
        ats(channel_layer.group_add)(
            self.consumer.group_name,
            self.consumer.channel_name
        )

        ats(self.consumer.disconnect)("")
        self.assertNotIn(self.consumer.group_name, channel_layer.groups)

    @patch("messages.consumers.CustomAsyncWebsocketConsumer.send")
    def test_send_data(self, p_send):
        event = {"data": "event_data"}
        ats(self.consumer.send_data)(event)
        p_send.assert_called_with(
            json.dumps(event["data"])
        )

    @patch("messages.consumers.CustomAsyncWebsocketConsumer.send")
    @patch("messages.consumers.CustomAsyncWebsocketConsumer.close")
    def test_check_current_user(self, p_close, p_send):
        self.consumer.current_user = Mock()
        self.consumer.current_user.is_authenticated = False
        res = ats(self.consumer.check_current_user)()
        self.assertFalse(res)
        p_send.assert_called_with(json.dumps({
            "command": "go_home"
        }))
        p_close.assert_called()

        self.consumer.current_user.is_authenticated = True
        self.assertTrue(ats(self.consumer.check_current_user)())

    @patch("messages.consumers.logger.log")
    def test_log(self, p_logger_log):
        info = "info"
        self.consumer.log(20, info)
        p_logger_log.assert_called_with(
            20,
            "channel {}, {} {}: {}".format(
                self.consumer.channel_name, self.consumer.type,
                self.consumer.name, info
            )
        )


class TestDialogConsumer(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.create_user(cls)

    def setUp(self):
        self.consumer = DialogConsumer()
        self.channel_name = "channel-name"
        self.consumer.channel_name = self.channel_name
        self.consumer.channel_layer = channel_layer
        self.consumer.scope = {
            "user": self.user,
            "url_route": {
                "kwargs": {
                    "interlocutor_id": 2
                }
            }
        }
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )

    def tearDown(self):
        redis_cache.flushdb()

    def additional_setUp(self):
        self.consumer.current_user = self.user
        self.consumer.interlocutor_id = 2
        self.consumer.name = "1-2"
        self.consumer.type = "dialog"
        self.consumer.i_manager = DialogIntegrityManager(1, 2)
        self.consumer.i_manager2 = DialogIntegrityManager(2, 1)
        self.consumer.dsi_manager = DialogsIntegrityManager(1)
        self.consumer.dsi_manager2 = DialogsIntegrityManager(2)
        self.consumer.uds_manager = UnreadDialogsManager(1)
        self.consumer.uds_manager2 = UnreadDialogsManager(2)
        self.consumer.group_name = get_dialog_group_name(1, 2)
        self.consumer.group_name2 = get_dialog_group_name(2, 1)
        self.consumer.dialogs_group_name = get_dialogs_group_name(1)
        self.consumer.dialogs_group_name2 = get_dialogs_group_name(2)

    @patch("messages.consumers.DialogConsumer.check_current_user")
    @patch("messages.consumers.DialogConsumer.send")
    @patch("messages.consumers.DialogConsumer.accept")
    def test_connect(
        self, p_accept,
        p_send, p_check_current_user
    ):
        group_name = get_dialog_group_name(self.user.id, 2)
        ats(channel_layer.group_add)(
            group_name,
            "fake-channel-name"
        )
        p_check_current_user.return_value = False

        ats(self.consumer.connect)()
        self.assertEqual(self.consumer.current_user, self.user)
        self.assertEqual(self.consumer.interlocutor_id, 2)
        self.assertEqual(self.consumer.name, "1-2")
        self.assertEqual(self.consumer.i_manager.user_id, 1)
        self.assertEqual(self.consumer.i_manager.interlocutor_id, 2)
        self.assertEqual(self.consumer.i_manager2.user_id, 2)
        self.assertEqual(self.consumer.i_manager2.interlocutor_id, 1)
        self.assertEqual(self.consumer.dsi_manager.user_id, 1)
        self.assertEqual(self.consumer.dsi_manager2.user_id, 2)
        self.assertEqual(self.consumer.uds_manager.user_id, 1)
        self.assertEqual(self.consumer.uds_manager2.user_id, 2)
        self.assertEqual(
            self.consumer.group_name, get_dialog_group_name(1, 2)
        )
        self.assertEqual(
            self.consumer.group_name2, get_dialog_group_name(2, 1)
        )
        self.assertEqual(
            self.consumer.dialogs_group_name, get_dialogs_group_name(1)
        )
        self.assertEqual(
            self.consumer.dialogs_group_name2, get_dialogs_group_name(2)
        )
        self.assertEqual(self.consumer.group_name, group_name)
        self.assertNotIn(self.consumer.group_name, channel_layer.groups)
        p_accept.assert_called()
        p_check_current_user.assert_called()
        p_send.assert_not_called()

        p_check_current_user.return_value = True
        ats(self.consumer.connect)()
        p_check_current_user.assert_called()
        self.assertEqual(
            list(channel_layer.groups[group_name].keys()),
            [self.channel_name]
        )
        p_send.assert_called_with(json.dumps({
            "command": "check_integrity",
            "integrity_hash": 0,
        }))

    def test_receive___get_new_message___invalid(self):
        self.additional_setUp()
        text = ""
        for _ in range(settings.FS_MAX_MESSAGE_LENGTH + 1):
            text += "a"
        data = {
            "command": "get_new_message",
            "message": {
                "text": text
            }
        }
        with self.assertRaises(ValidationError) as cm:
            ats(self.consumer.receive)(json.dumps(data))
        self.assertEqual(
            list(cm.exception),
            ["{} isn't valid!".format(MessagesForm.__name__)]
        )

    @patch("dev.py.tests.messages.test_consumers.channel_layer.group_send")
    def test_receive___get_new_message(self, p_group_send):
        self.additional_setUp()
        consumer = self.consumer
        text = "text1"
        data = {
            "command": "get_new_message",
            "message": {
                "text": text
            }
        }

        ats(self.consumer.receive)(json.dumps(data))
        messages = Message.objects.all()
        self.assertEqual(len(messages), 1)
        self.assertCountEqual(self.redis_cache.smembers("uds_2"), {"", "1"})
        message = messages.first()
        hash_ = hash_time(message.time)
        self.assertCountEqual(self.redis_cache.get("di_1-2"), str(hash_))
        self.assertCountEqual(self.redis_cache.get("di_2-1"), str(hash_))
        dialog_hash = hash_dialog(2, message.time)
        dialog_hash2 = hash_dialog(self.user.id, message.time)
        self.assertCountEqual(
            self.redis_cache.hgetall("dsi_1"),
            {"": 0, "2": str(dialog_hash)}
        )
        self.assertCountEqual(
            self.redis_cache.hgetall("dsi_2"),
            {"": 0, "1": str(dialog_hash2)}
        )
        dialog_event = {
            "type": "send_data",
            "data": {
                "command": "get_new_message",
                "integrity_hash": ats(consumer.i_manager.get_hash)(),
                "message": message.as_dict(self.user.id)
            }
        }
        dialog_event2 = {
            "type": "send_data",
            "data": {
                "command": "get_new_message",
                "integrity_hash": ats(consumer.i_manager2.get_hash)(),
                "message": message.as_dict(2)
            }
        }
        dialogs_event = {
            "type": "send_data",
            "data": {
                "command": "get_new_message",
                "dialog": {
                    "id": 2,
                    "text": message.text,
                    "is_unread": False,
                    "hash": dialog_hash
                },
                "integrity_hash": ats(consumer.dsi_manager.get_hash)(),
            }
        }
        dialogs_event2 = deepcopy(dialogs_event)
        dialogs_event2["data"]["dialog"]["id"] = self.user.id
        dialogs_event2["data"]["dialog"]["is_unread"] = True
        dialogs_event2["data"]["dialog"]["hash"] = dialog_hash2
        dialogs_event2["data"]["integrity_hash"] = ats(
            consumer.dsi_manager2.get_hash
        )()
        p_group_send.assert_has_calls([
            call(consumer.group_name, dialog_event),
            call(consumer.group_name2, dialog_event2),
            call(consumer.dialogs_group_name, dialogs_event),
            call(consumer.dialogs_group_name2, dialogs_event2)
        ])

    @patch("dev.py.tests.messages.test_consumers.channel_layer.group_send")
    @patch("messages.consumers.DialogsIntegrityManager.mark_as_read")
    @patch("messages.consumers.UnreadDialogsManager.mark_as_read")
    def test_receive___mark_dialog_as_read(
        self, p_uds_mark_as_read,
        p_dim_mark_as_read, p_group_send
    ):
        self.additional_setUp()
        Message.objects.create(
            sender_id=2, receiver_id=self.user.id, text="text1"
        )
        data = {
            "command": "mark_dialog_as_read",
        }

        ats(self.consumer.receive)(json.dumps(data))
        p_dim_mark_as_read.assert_called_with(2)
        p_uds_mark_as_read.assert_called_with(2)
        event = {
            "type": "send_data",
            "data": {
                "command": "mark_dialog_as_read",
                "dialog_id": self.consumer.interlocutor_id,
                "integrity_hash": ats(self.consumer.dsi_manager.get_hash)()
            }
        }
        p_group_send.assert_called_with(
            self.consumer.dialogs_group_name, event
        )

    @patch("messages.consumers.DialogConsumer.send")
    def test_receive___give_messages(self, p_send):
        self.additional_setUp()
        Message.objects.create(
            sender_id=2, receiver_id=self.user.id, text="text1"
        )
        Message.objects.create(
            sender_id=1, receiver_id=2, text="text2"
        )

        data = {"command": "give_messages"}

        ats(self.consumer.receive)(json.dumps(data))
        messages, _ = ats(self.consumer.i_manager.get_messages)()

        messages_as_dict = []
        for message in messages:
            messages_as_dict.append(
                message.as_dict(1)
            )
        p_send.assert_called_with(json.dumps({
            "command": "get_messages",
            "messages": messages_as_dict,
        }))

    @patch("messages.consumers.DialogConsumer.log")
    def test_receive___invalid(self, p_log):
        self.additional_setUp()
        data = {}
        ats(self.consumer.receive)(json.dumps(data))
        p_log.assert_called_with(LOG_WARNING_LEVEL, "command is needed")

        data = {"command": "asdfasdf"}
        ats(self.consumer.receive)(json.dumps(data))
        p_log.assert_called_with(LOG_WARNING_LEVEL, "invalid command")


class TestDialogsConsumer(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.create_user(cls)

    def setUp(self):
        self.consumer = DialogsConsumer()
        self.channel_name = "channel-name"
        self.consumer.channel_name = self.channel_name
        self.consumer.channel_layer = channel_layer
        self.consumer.scope = {"user": self.user}
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )

    def tearDown(self):
        self.redis_cache.flushdb()

    def additional_setUp(self):
        self.consumer.current_user = self.user
        self.consumer.name = "1"
        self.consumer.type = "dialogs"
        self.consumer.i_manager = DialogsIntegrityManager(
            self.user.id
        )
        self.consumer.uds_manager = UnreadDialogsManager(
            self.user.id
        )
        self.consumer.group_name = get_dialogs_group_name(
            self.user.id
        )

    @patch("messages.consumers.DialogsConsumer.check_current_user")
    @patch("messages.consumers.DialogsConsumer.send")
    @patch("messages.consumers.DialogsConsumer.accept")
    def test_connect(
        self, p_accept,
        p_send, p_check_current_user
    ):
        group_name = get_dialogs_group_name(self.user.id)
        ats(channel_layer.group_add)(
            group_name,
            "fake-channel-name"
        )
        p_check_current_user.return_value = False

        ats(self.consumer.connect)()
        self.assertEqual(self.consumer.group_name, group_name)
        self.assertNotIn(self.consumer.group_name, channel_layer.groups)
        p_accept.assert_called()
        p_check_current_user.assert_called()
        p_send.assert_not_called()

        p_check_current_user.return_value = True
        ats(self.consumer.connect)()
        p_check_current_user.assert_called()
        self.assertEqual(
            list(channel_layer.groups[group_name].keys()),
            [self.channel_name]
        )
        p_send.assert_called_with(json.dumps({
            "command": "check_integrity",
            "integrity_hash": 0,
        }))

    @patch("dev.py.tests.messages.test_consumers.channel_layer.group_send")
    @patch("messages.consumers.DialogsIntegrityManager.mark_as_deleted")
    @patch("messages.consumers.UnreadDialogsManager.mark_as_read")
    def test_receive___delete_dialog(
        self, p_uds_mark_as_read,
        p_dim_mark_as_deleted, p_group_send
    ):
        self.additional_setUp()
        Message.objects.create(
            sender_id=2, receiver_id=self.user.id, text="text1"
        )
        di_manager = DialogIntegrityManager(
            self.user.id, 2
        )
        self.assertNotEqual(ats(di_manager.get_hash)(), 0)
        data = {
            "command": "delete_dialog",
            "dialog_id": 2
        }

        ats(self.consumer.receive)(json.dumps(data))
        p_dim_mark_as_deleted.assert_called_with(2)
        p_uds_mark_as_read.assert_called_with(2)
        self.assertEqual(ats(di_manager.get_hash)(), 0)
        event = {
            "type": "send_data",
            "data": {
                "command": "delete_dialog",
                "dialog_id": 2,
                "integrity_hash": ats(self.consumer.i_manager.get_hash)(),
            }
        }
        p_group_send.assert_called_with(
            self.consumer.group_name, event
        )

    @patch("messages.consumers.DialogsConsumer.send")
    @patch("messages.consumers.UnreadDialogsManager.reset")
    def test_receive___give_dialogs(
        self, p_uds_reset, p_send
    ):
        self.additional_setUp()
        Message.objects.create(
            sender_id=2, receiver_id=1, text="text1"
        )
        data = {"command": "give_dialogs"}

        ats(self.consumer.receive)(json.dumps(data))
        dialogs, _, uds_set = ats(self.consumer.i_manager.get_dialogs)()
        p_uds_reset.assert_called_with(uds_set)
        p_send.assert_called_with(json.dumps({
            "command": "get_dialogs",
            "dialogs": dialogs
        }))

    @patch("messages.consumers.DialogsConsumer.log")
    def test_receive___invalid(self, p_log):
        data = {}
        ats(self.consumer.receive)(json.dumps(data))
        p_log.assert_called_with(LOG_WARNING_LEVEL, "command is needed")

        data = {"command": "asdfasdf"}
        ats(self.consumer.receive)(json.dumps(data))
        p_log.assert_called_with(LOG_WARNING_LEVEL, "invalid command")


class TestUtils(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.create_user(cls)

    def test_get_dialog_group_name(self):
        self.assertEqual(get_dialog_group_name(1, 2), "d1-2")

    def test_get_dialogs_group_name(self):
        self.assertEqual(get_dialogs_group_name(1), "ds1")

    @patch("messages.consumers.channel_layer.group_send")
    def test_clear_group(self, p_group_send):
        group_name = "my-group"
        ats(channel_layer.group_add)(
            group_name,
            "fake-channel-name"
        )
        ats(clear_group)(group_name)

        p_group_send.assert_called_with(
            group_name,
            {
                "type": "send_data",
                "data": {
                    "command": "go_home",
                }
            }

        )
        self.assertNotIn(group_name, channel_layer.groups)

    def test_constants(self):
        self.assertEqual(LOG_WARNING_LEVEL, 30)
        self.assertEqual(LOG_INFO_LEVEL, 20)
