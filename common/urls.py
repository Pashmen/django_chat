from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.urls import include
from django.urls import path

from .views import account_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("account/", account_view, name="account"),
    path("", include("messages.urls"))
]
