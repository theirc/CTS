from django.apps import AppConfig


class ReportConfig(AppConfig):
    name = "reports"

    def ready(self):
        from . import signals  # noqa
