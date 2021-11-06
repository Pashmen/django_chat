from channels.testing import WebsocketCommunicator

from config.asgi import application as pre_app
from dev.py.utils import CustomTestCase


application = pre_app.application_mapping["websocket"]


class TestUrls(CustomTestCase):
    async def test_dialogs(self):
        communicator = WebsocketCommunicator(application, "/ws/dialogs/")
        connected, _ = await communicator.connect()

        self.assertTrue(connected)
        self.assertEqual(communicator.application, application)

        await communicator.disconnect()

    async def test_dialog(self):
        communicator = WebsocketCommunicator(application, "/ws/dialogs/u12")
        connected, _ = await communicator.connect()

        self.assertTrue(connected)
        self.assertEqual(communicator.application, application)

        await communicator.disconnect()
