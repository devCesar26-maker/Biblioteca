from django.apps import AppConfig
from django.conf import settings

class AcervoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ACERVO'

    def ready(self):
        # 1. Mantém seus signals normais
        import ACERVO.signals

        # 2. Inicializador do APScheduler com proteção para migrações
        import os
        if os.environ.get('RUN_MAIN') == 'true' or not settings.DEBUG:
            from django.db.utils import ProgrammingError, OperationalError
            try:
                from . import updater
                updater.start()
            except (ProgrammingError, OperationalError):
                # Se as tabelas do APScheduler ainda não existirem no banco,
                # ele ignora o erro de forma segura para permitir que o 'migrate' termine.
                print("APScheduler: Tabelas não encontradas no banco de dados. Pulando inicialização provisoriamente.")