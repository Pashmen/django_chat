from django.contrib.auth.models import AbstractUser
from asgiref.sync import async_to_sync
from django.db import models


class CustomUser(AbstractUser):
    id = models.AutoField(primary_key=True)

    def unread_dialogs_exist(self):
        from messages.managers import UnreadDialogsManager

        if not hasattr(self, "_unread_dialogs_number_manager"):
            self._unread_dialogs = UnreadDialogsManager(self.id)

        return bool(async_to_sync(self._unread_dialogs.get_number)())
