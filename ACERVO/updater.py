from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.core.management import call_command
import logging

logger=logging.getLogger(__name__)


def tarefa_avisar_prazos():


    print("APScheduler: Iniciando a varredura automática dos prazos")

    try:

        call_command('avisar_prazos')
        print("APScheduler: Varredura concluída com sucesso")

    except Exception as e:
        print(f"APScheduler Erro: Não foi possível executar a tarefa: {e}")

def start():
    scheduler=BackgroundScheduler()

    #Usa o banco de dados do Django para sincronizar as execuções
    scheduler.add_jobstore(DjangoJobStore(), "default")

    #Agenda para rodar todos os dias às 15:30

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
    print("APScheduler: O relógio de prazos foi iniciado às 15:30!")


