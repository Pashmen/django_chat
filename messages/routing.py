from django.urls import re_path

from .consumers import DialogConsumer
from .consumers import DialogsConsumer


websocket_urlpatterns = [
    re_path(
        r"ws/dialogs/u(?P<interlocutor_id>[1-9]\d*)/",
        DialogConsumer.as_asgi(),
        name="dialog"
    ),
    re_path(
        r"ws/dialogs/",
        DialogsConsumer.as_asgi(),
        name="dialogs"
    )
]
