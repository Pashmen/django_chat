from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        user_a = get_user_model().objects.create(
            id=1, username="a", email="a@email.com"
        )
        user_a.set_password("Ie25xSbcasc")
        user_a.save()
        user_b = get_user_model().objects.create(
            id=2, username="b", email="b@email.com",
        )
        user_b.set_password("Ie25xSbcasc")
        user_b.save()
        user_c = get_user_model().objects.create(
            id=3, username="c", email="c@email.com",
        )
        user_c.set_password("Ie25xSbcasc")
        user_c.save()

        get_user_model().objects.create_superuser(
            "admin", "admin@email.com", "Ie25xSbcasc"
        )
