from django.apps import AppConfig


class SitesettingConfig(AppConfig):
    name = 'sitesetting'
    def ready(self):
        from . import signals
