import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from django_apscheduler.jobstores import DjangoJobStore, register_events

logger = logging.getLogger(__name__)


def tarefa_avisar_prazos():
    logger.info("APScheduler: Iniciando a varredura automática dos prazos")

    try:
        call_command('avisar_prazos')
        logger.info("APScheduler: Varredura concluída com sucesso")

    except Exception as e:
        logger.error(f"APScheduler: Não foi possível executar a tarefa: {e}")


def start():
    scheduler = BackgroundScheduler()

    # Usa o banco de dados do Django para sincronizar as execuções
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Agenda para rodar todos os dias às 16:18
    scheduler.add_job(
        tarefa_avisar_prazos,
        trigger="cron",
        hour=16,
        minute=18,
        id="avisar_prazos_diario",
        max_instances=1,
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()
    logger.info("APScheduler: O agendador de prazos foi iniciado (diariamente às 16:18).")