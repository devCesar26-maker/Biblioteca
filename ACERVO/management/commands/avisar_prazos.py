from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ACERVO.models import Emprestimo  # Substitua pelo app correto

# IMPORTANTE: Altere para o caminho real da sua função da Brevo
from ACERVO.views import enviar_email

class Command(BaseCommand):
    help = 'Envia alertas via Brevo faltando 2 dias, 1 dia e no dia do vencimento'

    def handle(self, *args, **kwargs):
        hoje = timezone.localdate()
        
        # 1. Mapeamos as 3 datas que disparam alertas em relação a hoje
        data_vencimento_hoje = hoje
        data_vencimento_amanha = hoje + timedelta(days=1)
        data_vencimento_daqui_2_dias = hoje + timedelta(days=2)
        
        # Lista com as 3 datas alvo para o filtro do banco de dados
        datas_alvo = [data_vencimento_hoje, data_vencimento_amanha, data_vencimento_daqui_2_dias]

        # 2. Buscamos todos os empréstimos ativos que caiam em QUALQUER uma dessas 3 datas
        emprestimos_pendentes = Emprestimo.objects.filter(
            data_devolucao__in=datas_alvo,
            devolvido=False
        )

        if not emprestimos_pendentes.exists():
            self.stdout.write(self.style.WARNING("Nenhum empréstimo exige alertas hoje."))
            return

        emails_enviados = 0

        # 3. Varremos os registros alterando a mensagem de acordo com a urgência
        for emprestimo in emprestimos_pendentes:
            try:
                email_aluno = emprestimo.aluno.user.email
                nome_aluno = emprestimo.aluno.user.first_name if emprestimo.aluno.user.first_name else emprestimo.aluno.user.username
                titulo_livro = emprestimo.livro.nome
                
                # Descobrimos qual é o gatilho deste empréstimo específico
                if emprestimo.data_devolucao == data_vencimento_hoje:
                    assunto = f"🚨 Vence HOJE: Devolução do livro '{titulo_livro}'"
                    texto_tempo = "O prazo termina HOJE. Por favor, compareça à biblioteca ou faça a renovação online para evitar multas."
                
                elif emprestimo.data_devolucao == data_vencimento_amanha:
                    assunto = f"⚠️ Falta 1 dia: Devolução do livro '{titulo_livro}'"
                    texto_tempo = "O prazo de devolução termina AMANHÃ. Fique atento para não perder o horário."
                
                else: # data_vencimento_daqui_2_dias
                    assunto = f"Aviso de Prazo: Falta pouco para a devolução do livro '{titulo_livro}'"
                    texto_tempo = f"Faltam apenas 2 dias para o término do prazo (Data limite: {emprestimo.data_devolucao.strftime('%d/%m/%Y')})."

                # Montamos o corpo do e-mail dinâmico
                mensagem = (
                    f"Olá, {nome_aluno}!\n\n"
                    f"Este é um lembrete automático do Sistema da Biblioteca.\n"
                    f"Sobre o seu empréstimo do livro '{titulo_livro}':\n"
                    f"{texto_tempo}\n\n"
                    f"Se você já devolveu ou renovou este livro recentemente, por favor desconsidere este aviso.\n\n"
                    f"Atenciosamente,\nEquipe da Biblioteca."
                )

                # Dispara o e-mail pela Brevo
                enviar_email(email_aluno, assunto, message=mensagem)
                
                emails_enviados += 1
                self.stdout.write(self.style.SUCCESS(f"Alerta enviado para {email_aluno} (Status: {emprestimo.data_devolucao})"))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro no empréstimo ID {emprestimo.id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Processo finalizado. {emails_enviados} e-mails disparados."))