from unittest.mock import Mock

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import render
from django.test import RequestFactory
from django.test import TestCase as DjangoTestCase
from django.utils import timezone


class ProjectError(Exception):
    pass


class CustomTestCase(DjangoTestCase):
    factory = RequestFactory()
    TIME_FORMAT = settings.FS_TIME_FORMAT

    def create_user(cls):
        cls.PASSWORD = "Fwer2356scdvf"
        cls.EMAIL = "user@email.com"
        cls.user = get_user_model().objects.create(
            id=1,
            email=cls.EMAIL,
            password=cls.PASSWORD
        )

    def create_p_user(cls):
        cls.EMAIL = "user@email.com"
        cls.INFO = "Info about me"
        cls.AVATAR_PATH = "/media/avatars/standart_avatar.png"
        cls.LAST_SEEN = "2020.20.20 10:10"
        cls.user = Mock(**{
            "id": 1,
            "email": cls.EMAIL,
            "info": cls.INFO,
            "avatar.url": cls.AVATAR_PATH,
            "last_seen": cls.LAST_SEEN
        })

    def convert_str_to_time(self, time_str):
        return timezone.make_aware(
            timezone.datetime.strptime(
                time_str,
                self.TIME_FORMAT
            ),
            timezone=pytz.timezone("Etc/UTC")
        )

    def seen_in_cache_set(self, user_id, moment):
        self.redis_cache.set(
            "seen_{}".format(user_id),
            moment.strftime(self.TIME_FORMAT)
        )

    def render(
        self, template_path, data={},
        is_authorised=False, request_user_attrs=None
    ):
        request = self.factory.get("/")
        if not is_authorised:
            request.user = AnonymousUser()
        else:
            request.user = User()

        if request_user_attrs != None:
            for attr_name, attr_value in request_user_attrs.items():
                setattr(request.user, attr_name, attr_value)

        return render(
            request, template_path, data
        ).content.decode("utf-8")

    def assertTimeAlmostEqual(
        self, time1, time2, eps=60
    ):
        self.assertTrue(
            abs((time1 - time2).total_seconds()) <= eps
        )

    def assertCustomSequenceEqual(
        self, seq1, seq2
    ):
        return super().assertSequenceEqual(
            tuple(seq1), tuple(seq2)
        )

    def assertStatusCode(self, url, status_code):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status_code)

    def assertCustomRedirects(
        self, url, redirect_url, status_code,
        target_status_code, request_method="get", data={}
    ):
        if request_method == "get":
            response = self.client.get(url, data)
        elif request_method == "post":
            response = self.client.post(url, data)
        else:
            raise ProjectError(
                "This request method doesn't exist or isn't supported"
            )

        self.assertRedirects(
            response, redirect_url,
            status_code, target_status_code
        )

    def assertCascadeDelete(self, model, field_name):
        self.assertEquals(
            model._meta.get_field(field_name).remote_field.on_delete,
            models.CASCADE
        )
