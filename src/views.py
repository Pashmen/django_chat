from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .forms import MessagesForm
from .models import Message


@login_required
def dialogs_view(request):
    return TemplateResponse(
        request,
        "messages/dialogs.html",
    )


@login_required
def dialog_view(request, interlocutor_id):
    current_user = request.user
    interlocutor_id = int(interlocutor_id)

    if current_user.id == interlocutor_id:
        return redirect("dialogs")

    try:
        interlocutor = get_user_model().objects.get(id=interlocutor_id)

        return TemplateResponse(
            request,
            "messages/dialog.html",
            {
                "form": MessagesForm(),
                "interlocutor": interlocutor
            }
        )
    except get_user_model().DoesNotExist:
        messages = Message.objects.get_dialog_messages(
            current_user.id,
            interlocutor_id
        )

        if not messages:
            return redirect("dialogs")

        return TemplateResponse(
            request,
            "messages/dialog_with_deleted_interlocutor.html"
        )
