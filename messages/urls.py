from django.urls import path
from django.urls import re_path

from .views import dialog_view
from .views import dialogs_view
from .views import main_page_view


urlpatterns = [
    path(r"", main_page_view),
    path(r"dialogs/", dialogs_view, name="dialogs"),
    re_path(
        r"^dialogs/u(?P<interlocutor_id>[1-9]\d*)/$",
        dialog_view,
        name="dialog"
    ),
]
