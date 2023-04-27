import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class TestAppConfig(AppConfig):
    name = "test_app"

    def ready(self):
        if settings.DEBUGPY in ["listen", "wait"]:
            import debugpy  # pylint: disable=import-outside-toplevel

            logger.info(f"Starting python debugger on port {settings.DEBUGPY_PORT}")
            debugpy.listen(settings.DEBUGPY_PORT)
        if settings.DEBUGPY == "wait":
            logger.info(
                "*** Waiting for the client to connect to the debug session ***"
            )
            debugpy.wait_for_client()
