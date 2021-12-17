from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        user1 = get_user_model().objects.create(
            id=1, username="1", email="1@email.com"
        )
        user1.set_password("Ie25xSbcasc")
        user1.save()
        user2 = get_user_model().objects.create(
            id=2, username="2", email="2@email.com",
        )
        user2.set_password("Ie25xSbcasc")
        user2.save()
        user3 = get_user_model().objects.create(
            id=3, username="3", email="3@email.com",
        )
        user3.set_password("Ie25xSbcasc")
        user3.save()

        get_user_model().objects.create_superuser(
            "admin", "admin@email.com", "Ie25xSbcasc"
        )
