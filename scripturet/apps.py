from django.apps import AppConfig


class ScripturetConfig(AppConfig):
    name = 'scripturet'

    def ready(self):
        from . import signals
        assert(signals)
