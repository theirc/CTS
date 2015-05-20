from django.apps import AppConfig


class ShipmentsConfig(AppConfig):
    name = "shipments"

    def ready(self):
        from . import signals  # noqa
