from django.conf import settings
from django.db import models

from .managers import hash_time
from .managers import MessagesManager


class Message(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    time = models.DateTimeField(auto_now=True, editable=False)
    sender_id = models.IntegerField(editable=False, db_index=True)
    receiver_id = models.IntegerField(editable=False, db_index=True)
    text = models.CharField(
        max_length=settings.FS_MAX_MESSAGE_LENGTH,
        editable=False
    )
    is_unread = models.BooleanField(default=True)
    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_receiver = models.BooleanField(default=False)

    objects = MessagesManager()

    def as_dict(self, current_user_id):
        if self.sender_id == current_user_id:
            user_owns_message = True
            is_unread = False
        else:
            user_owns_message = False
            is_unread = self.is_unread

        return {
            "time": self.time.strftime(settings.FS_TIME_FORMAT),
            "user_owns_message": user_owns_message,
            "is_unread": is_unread,
            "text": self.text,
            "hash": hash_time(self.time)
        }

    def __str__(self):
        return self.text
