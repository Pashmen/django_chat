import redis
from asgiref.sync import async_to_sync as ats
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Settings
from dev.py.utils import CustomTestCase
from messages.managers import DialogIntegrityManager
from messages.managers import DialogsIntegrityManager
from messages.managers import hash_dialog
from messages.managers import hash_time
from messages.managers import MessagesManager
from messages.managers import UnreadDialogsManager
from messages.models import Message


class TestMessagesManager(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = MessagesManager()
        cls.manager.model = Message

    def setUp(self):
        self.messages = []

        self.messages.append(self.manager.create(
            sender_id=1, receiver_id=2,
            text="message{}".format(len(self.messages)),
            is_unread=False,
            is_deleted_by_sender=True, is_deleted_by_receiver=True
        ))
        self.messages.append(self.manager.create(
            sender_id=1, receiver_id=2,
            text="message{}".format(len(self.messages)),
            is_unread=True,
            is_deleted_by_sender=True, is_deleted_by_receiver=True
        ))
        self.messages.append(self.manager.create(
            sender_id=2, receiver_id=1,
            text="message{}".format(len(self.messages)),
            is_unread=False,
            is_deleted_by_sender=True, is_deleted_by_receiver=False
        ))
        self.messages.append(self.manager.create(
            sender_id=1, receiver_id=2,
            text="message{}".format(len(self.messages)),
            is_unread=True,
            is_deleted_by_sender=False, is_deleted_by_receiver=False
        ))
        self.messages.append(self.manager.create(
            sender_id=2, receiver_id=1,
            text="message{}".format(len(self.messages)),
            is_unread=True,
            is_deleted_by_sender=False, is_deleted_by_receiver=False
        ))

        self.messages.append(self.manager.create(
            sender_id=3, receiver_id=1,
            text="message{}".format(len(self.messages)),
            is_unread=True,
            is_deleted_by_sender=False, is_deleted_by_receiver=True
        ))
        self.messages.append(self.manager.create(
            sender_id=3, receiver_id=1,
            text="message{}".format(len(self.messages)),
            is_unread=True,
            is_deleted_by_sender=False, is_deleted_by_receiver=False
        ))

        self.messages.append(self.manager.create(
            sender_id=4, receiver_id=1,
            text="message{}".format(len(self.messages)),
            is_unread=False,
            is_deleted_by_sender=True, is_deleted_by_receiver=False
        ))

    def test_get_unread_dialogs_set(self):
        self.assertCountEqual(
            self.manager.get_unread_dialogs_set(1),
            {2, 3}
        )
        self.assertCountEqual(
            self.manager.get_unread_dialogs_set(2),
            {1}
        )

    def test_get_dialog_messages(self):
        self.assertSequenceEqual(
            self.manager.get_dialog_messages(1, 2),
            [self.messages[2], self.messages[3], self.messages[4]]
        )
        self.assertSequenceEqual(
            self.manager.get_dialog_messages(1, 3),
            [self.messages[6]]
        )
        self.assertSequenceEqual(
            self.manager.get_dialog_messages(1, 4),
            [self.messages[7]]
        )

    def test_get_dialogs(self):
        dialogs, hashes, uds_set = self.manager.get_dialogs(1)

        hash2 = hash_dialog(2, self.messages[4].time)
        hash3 = hash_dialog(3, self.messages[6].time)
        hash4 = hash_dialog(4, self.messages[7].time)
        dialog2 = {
            "id": 2, "text": "message4",
            "is_unread": True, "hash": hash2
        }
        dialog3 = {
            "id": 3, "text": "message6",
            "is_unread": True, "hash": hash3
        }
        dialog4 = {
            "id": 4, "text": "message7",
            "is_unread": False, "hash": hash4
        }

        self.assertSequenceEqual(
            dialogs,
            [dialog4, dialog3, dialog2]
        )
        self.assertCountEqual(
            hashes,
            {
                2: hash2,
                3: hash3,
                4: hash4
            }
        )
        self.assertCountEqual(uds_set, {2, 3})

    def test_mark_dialog_messages_as_read(self):
        self.manager.mark_dialog_messages_as_read(
            1, 2
        )
        self.assertFalse(self.manager.filter(
            sender_id=2,
            receiver_id=1,
            is_unread=True, is_deleted_by_receiver=False
        ).exists())

        self.manager.mark_dialog_messages_as_read(
            3, 1
        )
        self.assertFalse(self.manager.filter(
            sender_id=1,
            receiver_id=3,
            is_unread=True, is_deleted_by_receiver=False
        ).exists())

    def test_mark_dialog_messages_as_deleted(self):
        self.manager.mark_dialog_messages_as_deleted(
            1, 2
        )
        self.assertFalse(self.manager.filter(
            sender_id=1,
            receiver_id=2,
            is_deleted_by_sender=False
        ).exists())
        self.assertFalse(self.manager.filter(
            sender_id=2,
            receiver_id=1,
            is_deleted_by_receiver=False
        ).exists())

    def test_get_users_to_notify(self):
        self.messages.append(self.manager.create(
            sender_id=1, receiver_id=3,
            text="message{}".format(len(self.messages)),
            is_unread=True,
            is_deleted_by_sender=False, is_deleted_by_receiver=False
        ))
        self.messages.append(self.manager.create(
            sender_id=1, receiver_id=5,
            text="message{}".format(len(self.messages)),
            is_unread=True,
            is_deleted_by_sender=False, is_deleted_by_receiver=False
        ))
        get_user_model().objects.create(id=1, email="1@email.com")
        get_user_model().objects.create(id=2, email="2@email.com")
        get_user_model().objects.create(id=4, email="4@email.com")
        get_user_model().objects.create(id=5, email="5@email.com")
        Settings.objects.filter(owner__in=[1, 2]).update(
            notify_about_new_messages=True
        )

        def get_item(contact, number):
            return {
                "method": "email",
                "contact": contact,
                "new_messages_number": number
            }

        self.assertCountEqual(
            self.manager.get_users_to_notify(),
            [get_item("1@email.com", 2), get_item("2@email.com", 1)]
        )


class TestDialogIntegrityManager(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.key = "di_1-2"

    def setUp(self):
        self.manager = DialogIntegrityManager(1, 2)
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )

    def tearDown(self):
        self.redis_cache.flushdb()

    def set_cache_value(self, value):
        self.redis_cache.set(self.key, value)

    def get_cache_value(self):
        value = self.redis_cache.get(self.key)
        if value is not None:
            value = int(value)

        return value

    def test_get_hash(self):
        self.assertEqual(ats(self.manager.get_hash)(), 0)
        self.assertEqual(self.get_cache_value(), 0)
        self.redis_cache.flushdb()

        self.set_cache_value(3)
        self.assertEqual(ats(self.manager.get_hash)(), 3)
        self.assertEqual(self.get_cache_value(), 3)

    def test_get_messages(self):
        message1 = Message.objects.create(
            sender_id=1, receiver_id=2, text="text1"
        )
        message2 = Message.objects.create(
            sender_id=1, receiver_id=2, text="text2"
        )
        received_messages, received_hash = ats(self.manager.get_messages)()

        self.assertSequenceEqual(
            received_messages,
            Message.objects.get_dialog_messages(1, 2)
        )

        hash_ = hash_time(message1.time) + hash_time(message2.time)
        self.assertEqual(hash_, received_hash)
        self.assertEqual(hash_, self.get_cache_value())

    def test_add_to_cache(self):
        hash_ = 10
        self.set_cache_value(hash_)
        time = timezone.now()
        ats(self.manager.add_to_hash)(time)

        self.assertEqual(ats(self.manager.get_hash)(), hash_ + hash_time(time))

    def test_delete(self):
        self.set_cache_value(200)
        ats(self.manager.delete)()

        self.assertEqual(self.get_cache_value(), 0)


class TestDialogsIntegrityManager(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.key = "dsi_1"

    def setUp(self):
        self.manager = DialogsIntegrityManager(1)
        ats(self.manager.uds_manager.reset)({2})
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )

    def tearDown(self):
        self.redis_cache.flushdb()

    def get_cache_value(self):
        cache_value = self.redis_cache.hgetall(self.key)
        value = dict()
        for x, y in cache_value.items():
            if x != "":
                value[int(x)] = int(y)
            else:
                value[x] = 0

        return value

    def test_get_hash(self):
        Message.objects.create(
            sender_id=2, receiver_id=1, text="text1"
        )
        _, ds_hashes, _ = Message.objects.get_dialogs(1)
        hash_ = ds_hashes[2] + 1
        self.assertEqual(ats(self.manager.get_hash)(), hash_)

        self.redis_cache.flushdb()
        ats(self.manager.uds_manager.reset)({2})
        self.redis_cache.hset(
            self.key,
            mapping={1: 100, 2: 200}
        )
        self.assertEqual(ats(self.manager.get_hash)(), 301)

    def test_get_dialogs(self):
        message1 = Message.objects.create(
            sender_id=1, receiver_id=2, text="text1"
        )
        Message.objects.create(
            sender_id=3, receiver_id=1, text="text2"
        )
        ds, ds_hashes, uds_set = ats(self.manager.get_dialogs)()
        ds_db, ds_hashes_db, uds_set_db = Message.objects.get_dialogs(1)
        ds_hashes_db[""] = 0

        self.assertSequenceEqual(ds, ds_db)
        self.assertCountEqual(ds_hashes, ds_hashes_db)
        self.assertCountEqual(uds_set, uds_set_db)
        self.assertCountEqual(self.get_cache_value(), ds_hashes)

        ###
        message1.delete()
        ds, ds_hashes, uds_set = ats(self.manager.get_dialogs)()
        ds_db, ds_hashes_db, uds_set_db = Message.objects.get_dialogs(1)
        ds_hashes_db[""] = 0

        self.assertSequenceEqual(ds, ds_db)
        self.assertCountEqual(ds_hashes, ds_hashes_db)
        self.assertCountEqual(uds_set, uds_set_db)
        self.assertCountEqual(self.get_cache_value(), ds_hashes)

    def test_consider_new(self):
        ats(self.manager.consider_new)(2, 200)
        self.assertCountEqual(
            self.get_cache_value(),
            {"": 0, 2: 200}
        )

        ats(self.manager.consider_new)(3, 300)
        self.assertCountEqual(
            self.get_cache_value(),
            {"": 0, 2: 200, 3: 300}
        )

    def test_mark_as_read(self):
        Message.objects.create(
            sender_id=2, receiver_id=1, text="text1"
        )
        ats(self.manager.mark_as_read)(2)

        self.assertFalse(
            Message.objects.filter(
                sender_id=2, receiver_id=1,
                is_unread=True
            ).exists()
        )

    def test_mark_as_deleted(self):
        Message.objects.create(
            sender_id=2, receiver_id=1, text="text1"
        )
        ats(self.manager.mark_as_deleted)(2)

        self.assertFalse(
            Message.objects.filter(
                sender_id=2, receiver_id=1,
                is_deleted_by_receiver=False
            ).exists()
        )


class TestUnreadDialogsManager(CustomTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.key = "uds_1"

    def setUp(self):
        self.manager = UnreadDialogsManager(1)
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )

    def tearDown(self):
        self.redis_cache.flushdb()

    def get_cache_value(self):
        cache_value = self.redis_cache.smembers(self.key)
        value = set()
        for member in cache_value:
            if member != "":
                value.add(int(member))
            else:
                value.add(member)

        return value

    def test_get_number(self):
        self.redis_cache.sadd(self.key, *{"", 3, 4})
        self.assertEqual(ats(self.manager.get_number)(), 2)

        self.redis_cache.flushdb()
        Message.objects.create(
            sender_id=2, receiver_id=1, text="text1"
        )
        self.assertEqual(ats(self.manager.get_number)(), 1)

    def test_reset(self):
        self.redis_cache.sadd(self.key, *{"", 2})
        ats(self.manager.reset)({3, 4})
        self.assertCountEqual(self.get_cache_value(), {"", 3, 4})

        ats(self.manager.reset)({})
        self.assertCountEqual(self.get_cache_value(), {""})

        self.redis_cache.sadd(self.key, *{"", 2})
        ats(self.manager.reset)({3}, maybe_exists=False)
        self.assertCountEqual(self.get_cache_value(), {"", 2, 3})

    def test_add_dialog(self):
        ats(self.manager.add_dialog)(2)
        self.assertCountEqual(self.get_cache_value(), {"", 2})

        ats(self.manager.add_dialog)(3)
        self.assertCountEqual(self.get_cache_value(), {"", 2, 3})

    def test_mark_as_read(self):
        self.redis_cache.sadd(self.key, *{"", 2, 3})
        ats(self.manager.mark_as_read)(2)
        self.assertCountEqual(self.get_cache_value(), {"", 3})


class TestUtilFunctions(CustomTestCase):
    def test_hash_dialog(self):
        time = timezone.now()
        self.assertEqual(hash_dialog(2, time), 2 + hash_time(time))

    def test_hash_dialog(self):
        time = timezone.now()
        self.assertEqual(
            hash_time(time),
            time.hour*3600 + time.minute*60 + time.second
        )
