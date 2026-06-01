from django.dispatch import receiver
from allauth.account.signals import user_signed_up


@receiver(user_signed_up)

def enviar_email_boas_vindas_allauth(request, user, **kwargs):
    from .views import enviar_email
    destinatario = user.email
    
    # Valida se o usuário preencheu o campo de e-mail no formulário do allauth
    if destinatario:
        assunto = f"[Biblioteca] Bem-vindo(a) à plataforma, {user.username}!"
        mensagem = (
            f"Olá, {user.username}!\n\n"
            "Seu cadastro foi realizado com sucesso em nosso sistema da Biblioteca através do portal de acesso.\n"
            "A partir de agora, suas permissões de leitura e consulta estão ativas.\n\n"
            "Esta é uma notificação automática do sistema de gerenciamento. Não é necessário responder.\n\n"
            "Atenciosamente,\n"
            "Equipe de Suporte Técnico da Biblioteca"
        )
        
        # Executa a função do seu arquivo views.py
        enviar_email(destinatario, assunto, mensagem)