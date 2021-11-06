import json
import logging
from copy import deepcopy

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.core.exceptions import ValidationError

from .forms import MessagesForm
from .managers import DialogIntegrityManager
from .managers import DialogsIntegrityManager
from .managers import hash_dialog
from .managers import UnreadDialogsManager
from .models import Message


logger = logging.getLogger(__name__)
LOG_WARNING_LEVEL = 30
LOG_INFO_LEVEL = 20


class CustomAsyncWebsocketConsumer(AsyncWebsocketConsumer):
    async def disconnect(self, event):
        self.log(LOG_INFO_LEVEL, "disconnect {}".format(event))
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_data(self, event):
        await self.send(
            json.dumps(event["data"])
        )

    async def check_current_user(self):
        if (not self.current_user.is_authenticated):
            await self.send(json.dumps({
                "command": "go_home"
            }))
            await self.close()

            return False
        else:
            return True

    def log(self, level, info):
        logger.log(
            level,
            "channel {}, {} {}: {}".format(
                self.channel_name, self.type,
                self.name, info
            )
        )


class DialogConsumer(CustomAsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.current_user = self.scope["user"]
        self.interlocutor_id = int(
            self.scope["url_route"]["kwargs"]["interlocutor_id"]
        )
        self.name = "{}-{}".format(
            self.current_user.id,
            self.interlocutor_id
        )
        self.type = "dialog"
        self.log(LOG_INFO_LEVEL, "connect")

        self.i_manager = DialogIntegrityManager(
            self.current_user.id,
            self.interlocutor_id
        )
        self.i_manager2 = DialogIntegrityManager(
            self.interlocutor_id,
            self.current_user.id
        )
        self.dsi_manager = DialogsIntegrityManager(
            self.current_user.id
        )
        self.dsi_manager2 = DialogsIntegrityManager(
            self.interlocutor_id
        )
        self.uds_manager = UnreadDialogsManager(
            self.current_user.id
        )
        self.uds_manager2 = UnreadDialogsManager(
            self.interlocutor_id
        )

        self.group_name = get_dialog_group_name(
            self.current_user.id,
            self.interlocutor_id
        )
        self.group_name2 = get_dialog_group_name(
            self.interlocutor_id,
            self.current_user.id
        )
        self.dialogs_group_name = get_dialogs_group_name(
            self.current_user.id
        )
        self.dialogs_group_name2 = get_dialogs_group_name(
            self.interlocutor_id
        )

        await clear_group(self.group_name)
        if (await self.check_current_user()):
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.send(json.dumps({
                "command": "check_integrity",
                "integrity_hash": await self.i_manager.get_hash(),
            }))

    async def receive(self, text_data):
        self.log(LOG_INFO_LEVEL, "receive {}".format(text_data))
        data = json.loads(text_data)

        if "command" not in data:
            self.log(LOG_WARNING_LEVEL, "command is needed")
            return

        if data["command"] == "get_new_message":
            received_form = MessagesForm({
                "text": data["message"]["text"]
            })
            if received_form.is_valid():
                new_message = await sync_to_async(
                    Message.objects.create
                )(
                    sender_id=self.current_user.id,
                    receiver_id=self.interlocutor_id,
                    text=received_form.cleaned_data["text"]
                )
            else:
                raise ValidationError(
                    "{} isn't valid!".format(MessagesForm.__name__)
                )

            await self.uds_manager2.add_dialog(self.current_user.id)
            await self.i_manager.add_to_hash(new_message.time)
            await self.i_manager2.add_to_hash(new_message.time)

            dialog_event = {
                "type": "send_data",
                "data": {
                    "command": "get_new_message",
                    "integrity_hash": await self.i_manager.get_hash()
                }
            }
            dialog_event["data"]["message"] = new_message.as_dict(
                self.current_user.id
            )
            await self.channel_layer.group_send(
                self.group_name,
                dialog_event
            )

            dialog_event2 = deepcopy(dialog_event)
            dialog_event2["data"]["message"] = new_message.as_dict(
                self.interlocutor_id
            )
            dialog_event2["data"]["integrity_hash"] = (
                await self.i_manager2.get_hash()
            )
            await self.channel_layer.group_send(
                self.group_name2,
                dialog_event2
            )

            dialog_hash = hash_dialog(
                self.interlocutor_id,
                new_message.time
            )
            await self.dsi_manager.consider_new(
                self.interlocutor_id,
                dialog_hash
            )
            dialogs_event = {
                "type": "send_data",
                "data": {
                    "command": "get_new_message",
                    "dialog": {
                        "id": self.interlocutor_id,
                        "text": new_message.text,
                        "is_unread": False,
                        "hash": dialog_hash
                    },
                    "integrity_hash": await self.dsi_manager.get_hash(),
                }
            }
            await self.channel_layer.group_send(
                self.dialogs_group_name,
                dialogs_event
            )

            dialog_hash2 = hash_dialog(
                self.current_user.id,
                new_message.time
            )
            await self.dsi_manager2.consider_new(
                self.current_user.id,
                dialog_hash2
            )
            dialogs_event2 = deepcopy(dialogs_event)
            dialogs_event2["data"]["dialog"]["id"] = (
                self.current_user.id
            )
            dialogs_event2["data"]["dialog"]["is_unread"] = (
                True
            )
            dialogs_event2["data"]["dialog"]["hash"] = dialog_hash2
            dialogs_event2["data"]["integrity_hash"] = (
                await self.dsi_manager2.get_hash()
            )

            await self.channel_layer.group_send(
                self.dialogs_group_name2,
                dialogs_event2
            )
        elif data["command"] == "mark_dialog_as_read":
            messages = await self.dsi_manager.mark_as_read(
                self.interlocutor_id
            )
            await self.uds_manager.mark_as_read(
                self.interlocutor_id
            )

            dialogs_event = {
                "type": "send_data",
                "data": {
                    "command": "mark_dialog_as_read",
                    "dialog_id": self.interlocutor_id,
                    "integrity_hash": await self.dsi_manager.get_hash()
                }
            }
            await self.channel_layer.group_send(
                self.dialogs_group_name,
                dialogs_event
            )
        elif data["command"] == "give_messages":
            messages, _ = await self.i_manager.get_messages()

            messages_as_dict = []
            for message in messages:
                messages_as_dict.append(
                    message.as_dict(self.current_user.id)
                )

            text_data = {
                "command": "get_messages",
                "messages": messages_as_dict,
            }
            await self.send(
                json.dumps(text_data)
            )
        else:
            self.log(LOG_WARNING_LEVEL, "invalid command")


class DialogsConsumer(CustomAsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.current_user = self.scope["user"]
        self.name = str(self.current_user.id)
        self.type = "dialogs"
        self.log(LOG_INFO_LEVEL, "connect")

        self.i_manager = DialogsIntegrityManager(
            self.current_user.id
        )
        self.uds_manager = UnreadDialogsManager(
            self.current_user.id
        )

        self.group_name = get_dialogs_group_name(
            self.current_user.id
        )

        await clear_group(self.group_name)
        if await self.check_current_user():
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.send(json.dumps({
                "command": "check_integrity",
                "integrity_hash": await self.i_manager.get_hash(),
            }))

    async def receive(self, text_data):
        self.log(LOG_INFO_LEVEL, "receive {}".format(text_data))

        data = json.loads(text_data)

        if "command" not in data:
            self.log(LOG_WARNING_LEVEL, "command is needed")
            return

        if data["command"] == "delete_dialog":
            dialog_id = data["dialog_id"]
            await self.i_manager.mark_as_deleted(dialog_id)
            await self.uds_manager.mark_as_read(dialog_id)

            di_manager = DialogIntegrityManager(
                self.current_user.id,
                dialog_id
            )
            await di_manager.delete()

            event = {
                "type": "send_data",
                "data": {
                    "command": "delete_dialog",
                    "dialog_id": dialog_id,
                    "integrity_hash": await self.i_manager.get_hash(),
                }
            }
            await self.channel_layer.group_send(
                self.group_name,
                event
            )
        elif data["command"] == "give_dialogs":
            dialogs, _, uds_set = await self.i_manager.get_dialogs()

            await self.uds_manager.reset(uds_set)

            await self.send(json.dumps({
                "command": "get_dialogs",
                "dialogs": dialogs
            }))
        else:
            self.log(LOG_WARNING_LEVEL, "invalid command")


def get_dialog_group_name(user1_id, user2_id):
    return "d{}-{}".format(user1_id, user2_id)


def get_dialogs_group_name(user_id):
    return "ds{}".format(user_id)


channel_layer = get_channel_layer()


async def clear_group(group_name):
    if group_name in channel_layer.groups:
        await channel_layer.group_send(
            group_name,
            {
                "type": "send_data",
                "data": {
                    "command": "go_home",
                }
            }
        )

        channels_names = deepcopy(channel_layer.groups[group_name])
        for channel_name in channels_names:
            await channel_layer.group_discard(
                group_name,
                channel_name
            )
