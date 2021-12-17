from common.templatetags.settings import settings
from dev.py.utils import CustomTestCase


class TestSettings(CustomTestCase):
    def test(self):
        with self.settings(T="TT"):
            self.assertEqual(settings("T"), "TT")

        with self.settings(G="GG"):
            self.assertEqual(settings("G"), "GG")
