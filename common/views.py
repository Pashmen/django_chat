from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse


@login_required
def account_view(request):
    return TemplateResponse(
        request, "common/account.html"
    )
