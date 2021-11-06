from itertools import chain

import redis
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import connection
from django.db import models
from django.db.models import F
from django.utils import timezone


class MessagesManager(models.Manager):
    def get_unread_dialogs_set(self, user_id):
        return set(self.filter(
            receiver_id=user_id,
            is_unread=True,
            is_deleted_by_receiver=False
        ).values_list(
            "sender_id",
            flat=True
        ).distinct())

    def get_dialog_messages(self, user1_id, user2_id):
        messages1 = self.filter(
            sender_id=user1_id,
            receiver_id=user2_id,
            is_deleted_by_sender=False
        )
        messages2 = self.filter(
            sender_id=user2_id,
            receiver_id=user1_id,
            is_deleted_by_receiver=False
        )
        return sorted(
            chain(messages1, messages2),
            key=lambda obj: obj.time
        )

    def get_dialogs(self, user_id):
        messages1 = self.filter(
            sender_id=user_id,
            is_deleted_by_sender=False
        ).annotate(
            interlocutor_id=F("receiver_id")
        ).values("interlocutor_id", "time", "text")
        messages2 = self.filter(
            receiver_id=user_id,
            is_deleted_by_receiver=False
        ).annotate(
            interlocutor_id=F("sender_id")
        ).values("interlocutor_id", "time", "text", "is_unread")

        max_time_dict = dict()
        for message in chain(messages1, messages2):
            if (message["interlocutor_id"] not in max_time_dict
                or message["time"]
                    > max_time_dict[message["interlocutor_id"]]["time"]
            ):
                max_time_dict[message["interlocutor_id"]] = message

        uds_set = set()
        for message in chain(messages1, messages2):
            if (message.get("is_unread", False)):
                uds_set.add(message["interlocutor_id"])

        dialogs = []
        for interlocutor_id, message in max_time_dict.items():
            dialog = dict()
            dialog["id"] = interlocutor_id
            dialog["time_for_sort"] = message["time"]
            dialog["text"] = message["text"]
            dialog["is_unread"] = interlocutor_id in uds_set
            dialog["hash"] = hash_dialog(interlocutor_id, message["time"])

            dialogs.append(dialog)

        dialogs.sort(
            key=lambda obj: obj["time_for_sort"],
            reverse=True
        )
        for dialog in dialogs:
            del(dialog["time_for_sort"])

        dialogs_hashes = dict()
        for dialog in dialogs:
            dialogs_hashes[dialog["id"]] = dialog["hash"]

        return dialogs, dialogs_hashes, uds_set

    def mark_dialog_messages_as_read(self, user1_id, user2_id):
        self.filter(
            sender_id=user2_id,
            receiver_id=user1_id,
            is_unread=True,
            is_deleted_by_receiver=False
        ).update(is_unread=False)

    def mark_dialog_messages_as_deleted(self, user1_id, user2_id):
        self.filter(
            sender_id=user1_id,
            receiver_id=user2_id,
            is_deleted_by_sender=False
        ).update(is_deleted_by_sender=True)
        self.filter(
            sender_id=user2_id,
            receiver_id=user1_id,
            is_deleted_by_receiver=False
        ).update(is_deleted_by_receiver=True)

    def get_users_to_notify(self):
        since_time = timezone.now() - timezone.timedelta(
            seconds=settings.FS_NEW_MESSAGES_PERIOD
        )
        query = """
        SELECT users.email, new_messages.number
        FROM accounts_customuser AS users
        INNER JOIN(
            SELECT
                owner_id
            FROM accounts_settings
            WHERE accounts_settings.notify_about_new_messages
        ) AS settings ON users.id = settings.owner_id
        INNER JOIN(
            SELECT
                COUNT(messages.receiver_id) AS number,
                messages.receiver_id AS user_id
            FROM custom_messages_message AS messages
            WHERE (
                NOT messages.is_deleted_by_receiver
                AND messages.is_unread
                AND messages.time >= '{}'
            )
            GROUP BY messages.receiver_id
        ) AS new_messages ON users.id = new_messages.user_id;
        """.format(str(since_time))

        users_info = []
        with connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                users_info.append({
                    "method": "email",
                    "contact": row[0],
                    "new_messages_number": row[1]
                })

            return users_info


class DialogIntegrityManager:
    def __init__(self, user_id, interlocutor_id):
        # It's impossible to import as usually
        from .models import Message

        self.user_id = user_id
        self.interlocutor_id = interlocutor_id
        self.key = "di_{}-{}".format(
            self.user_id,
            self.interlocutor_id
        )
        self.messages_manager = Message.objects
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )
        self.timeout = settings.FS_DIALOG_INTEGRITY_TIMEOUT

    async def get_hash(self):
        hash_str = self.redis_cache.get(self.key)
        if hash_str is None:
            _, hash_ = await self.get_messages()
        else:
            hash_ = int(hash_str)

        return hash_

    async def get_messages(self):
        messages = await sync_to_async(
            self.messages_manager.get_dialog_messages
        )(
            self.user_id,
            self.interlocutor_id
        )

        hash_ = 0
        for message in messages:
            hash_ += hash_time(message.time)

        self.redis_cache.setex(
            self.key,
            self.timeout,
            hash_
        )

        return messages, hash_

    async def add_to_hash(self, time):
        self.redis_cache.incrby(self.key, hash_time(time))

    async def delete(self):
        self.redis_cache.setex(
            self.key,
            self.timeout,
            0
        )


class DialogsIntegrityManager:
    def __init__(self, user_id):
        # It's impossible to import as usually
        from .models import Message

        self.user_id = user_id
        self.key = "dsi_{}".format(self.user_id)
        self.messages_manager = Message.objects
        self.uds_manager = UnreadDialogsManager(self.user_id)
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )
        self.timeout = settings.FS_DIALOGS_INTEGRITY_TIMEOUT

    async def get_hash(self):
        dialogs_hashes = self.redis_cache.hgetall(self.key)

        if dialogs_hashes == {}:
            _, dialogs_hashes, _ = await self.get_dialogs()

        hash_ = 0
        for dialog_hash in dialogs_hashes.values():
            hash_ += int(dialog_hash)

        hash_ += await self.uds_manager.get_number()

        return hash_

    async def get_dialogs(self):
        dialogs, dialogs_hashes, uds_set = await sync_to_async(
            self.messages_manager.get_dialogs
        )(self.user_id)

        # It's needed because of Redis architecture
        dialogs_hashes[""] = 0

        self.redis_cache.delete(self.key)
        self.redis_cache.hset(
            self.key,
            mapping=dialogs_hashes
        )
        self.redis_cache.expire(name=self.key, time=self.timeout)

        return dialogs, dialogs_hashes, uds_set

    async def consider_new(self, dialog_id, dialog_hash):
        mapping = {dialog_id: dialog_hash}
        if not self.redis_cache.exists(self.key):
            # It's needed because of Redis architecture
            mapping[""] = 0

        self.redis_cache.hset(
            self.key,
            mapping=mapping
        )

    async def mark_as_read(self, dialog_id):
        await sync_to_async(
            self.messages_manager.mark_dialog_messages_as_read
        )(self.user_id, dialog_id)

    async def mark_as_deleted(self, dialog_id):
        await sync_to_async(
            self.messages_manager.mark_dialog_messages_as_deleted
        )(self.user_id, dialog_id)
        self.redis_cache.hdel(self.key, dialog_id)


class UnreadDialogsManager:
    def __init__(self, user_id):
        # It's impossible to import as usually
        from .models import Message

        self.user_id = user_id
        self.key = "uds_{}".format(self.user_id)
        self.messages_manager = Message.objects
        self.redis_cache = redis.Redis(
            decode_responses=True,
            db=settings.FS_REDIS_DB
        )
        self.timeout = settings.FS_UNREAD_DIALOGS_TIMEOUT

    async def get_number(self):
        pre_uds_number = self.redis_cache.scard(self.key)

        if pre_uds_number == 0:
            uds_set = await sync_to_async(
                self.messages_manager.get_unread_dialogs_set
            )(self.user_id)
            uds_number = len(uds_set)

            await self.reset(uds_set, maybe_exists=False)
        else:
            # It's needed because of Redis architecture
            uds_number = pre_uds_number - 1

        return uds_number

    async def reset(self, uds_set, maybe_exists=True):
        if maybe_exists:
            self.redis_cache.delete(self.key)

        # It's needed because of Redis architecture
        self.redis_cache.sadd(self.key, "")

        if len(uds_set) != 0:
            self.redis_cache.sadd(self.key, *uds_set)

    async def add_dialog(self, id):
        if not self.redis_cache.exists(self.key):
            # It's needed because of Redis architecture
            self.redis_cache.sadd(self.key, "")

        self.redis_cache.sadd(self.key, id)

    async def mark_as_read(self, id):
        self.redis_cache.srem(self.key, id)


def hash_dialog(dialog_id, time):
    return dialog_id + hash_time(time)


def hash_time(time):
    return time.hour*3600 + time.minute*60 + time.second
