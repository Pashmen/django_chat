import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import messages.routing


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.development"
)

application = ProtocolTypeRouter({
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                messages.routing.websocket_urlpatterns
            )
        ),
    )
})
