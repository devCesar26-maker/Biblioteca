from django.apps import AppConfig
from django.conf import settings

class AcervoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ACERVO'

    def ready(self):
        import ACERVO.signals


        #Inicializador do APScheduler
        import os

        if os.environ.get('RUN_MAIN')=='true' or not settings.DEBUG:
            from . import updater
            updater.start()



