from django.conf import settings

from dev.py.utils import CustomTestCase


class TestSettings(CustomTestCase):
    def test_base_settings(self):
        self.assertEqual(settings.FS_MAX_MESSAGE_LENGTH, 400)
        self.assertEqual(settings.FS_DIALOG_INTEGRITY_TIMEOUT, 20*60)
        self.assertEqual(settings.FS_DIALOGS_INTEGRITY_TIMEOUT, 20*60)
        self.assertEqual(settings.FS_UNREAD_DIALOGS_TIMEOUT, 20*60)
        self.assertEqual(settings.FS_NEW_MESSAGES_PERIOD, 60*60)
        self.assertEqual(settings.FS_REDIS_DB, 1)
        self.assertEqual(settings.FS_TIME_FORMAT, "%Y.%m.%d %H:%M:%S")
