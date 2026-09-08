# 📚 Sistema de Biblioteca

Sistema web de gestão de acervo e empréstimos de uma biblioteca, construído com **Django 5**, **PostgreSQL** e **Bootstrap 5**.

Os alunos se cadastram (com conta local ou Google), pesquisam o acervo, solicitam empréstimos, renovam prazos e leem as obras digitalizadas (PDF) enquanto o empréstimo estiver ativo. Administradores gerenciam autores, editoras, categorias, livros e vínculos livro-autor, além de acompanhar estatísticas no painel.

---

## ✨ Funcionalidades

- **Autenticação completa** com [django-allauth](https://django-allauth.readthedocs.io/): cadastro com e-mail, login e login via Google.
- **Acervo**: cadastro de livros, autores, editoras e categorias, com capa e PDF opcionais.
- **Busca textual** no acervo (nome, autor, editora e categoria) usando full-text search do PostgreSQL.
- **Empréstimos**: retirada por 7 dias, renovação (máx. 3, com intervalo mínimo de 5 dias entre movimentações) e controle de devolução.
- **Leitura digital**: o PDF do livro é liberado apenas para quem possui um empréstimo ativo e dentro do prazo (validação feita no servidor).
- **Alertas por e-mail** (via Brevo/Anymail): boas-vindas no cadastro, confirmação de empréstimo/renovação e lembretes de devolução (2 dias, 1 dia e no dia do vencimento).
- **Agendador de tarefas** com [django-apscheduler](https://pypi.org/project/django-apscheduler/) para disparar os lembretes diariamente.
- **Painel administrativo** moderno com [django-unfold](https://unfoldadmin.com/) e **dashboard de estatísticas** com Chart.js.
- **Segurança**: HTTPS/HSTS, Content-Security-Policy, cookies `HttpOnly`/`Secure`/`SameSite` e WhiteNoise para arquivos estáticos.

---

## 🧱 Tecnologias

| Camada      | Tecnologia                                   |
|-------------|----------------------------------------------|
| Backend     | Django 5.1, Python 3.11                      |
| Banco       | PostgreSQL (com `django.contrib.postgres`)   |
| Frontend    | Bootstrap 5, Bootstrap Icons, Chart.js, PDF.js |
| Auth        | django-allauth (local + Google)              |
| E-mails     | django-anymail + Brevo API                   |
| Agendamento | django-apscheduler                           |
| Admin       | django-unfold                               |
| Deploy      | Gunicorn + WhiteNoise (Railway)             |

---

## 🐳 Rodando com Docker (recomendado)

A forma mais rápida: o **PostgreSQL já vem junto** no compose e o `migrate` roda automaticamente a cada subida do container.

### Pré-requisitos

- [Docker](https://docs.docker.com/engine/install/) com o plugin `docker compose`

### Passo a passo

```bash
# 1. (Opcional) Configure as variáveis no ambiente — sem isso, valores padrão seguros são usados
#    O compose lê o .env da pasta do projeto automaticamente para CHAVE_SECRETA, DEBUG, BREVO_API_KEY...
# cp .env.example .env

# 2. Suba a aplicação (primeira vez: baixa as imagens e faz o build)
docker compose up --build
```

Acesse: <http://localhost:8000>

Crie o superusuário do admin (em outro terminal):

```bash
docker compose exec web python manage.py createsuperuser
```

Gerar novas migrações depois de alterar os modelos (o `migrate` automático aplica o que for novo):

```bash
docker compose exec web python manage.py makemigrations
```

Parar os containers (os dados do banco e uploads são preservados em volumes):

```bash
docker compose down
```

> Os arquivos de upload (`media/`) e o PostgreSQL ficam em volumes Docker nomeados (`media_files`, `postgres_data`), então sobrevivem ao `down`.

---

## 🚀 Configuração local (sem Docker)

### Pré-requisitos

- Python 3.11+
- PostgreSQL rodando localmente (a busca textual depende dele)

### Passo a passo

```bash
# 1. Clone o repositório e entre na pasta
git clone <url-do-repositorio> BIBLIOTECA_DJANGO
cd BIBLIOTECA_DJANGO

# 2. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o ambiente
cp .env.example .env
# Edite o .env preenchendo CHAVE_SECRETA, DATABASE_URL e BREVO_API_KEY

# 5. Crie o banco e o superusuário
python manage.py migrate
python manage.py createsuperuser

# 6. Rode o servidor de desenvolvimento
python manage.py runserver
```

Acesse:
- Site: <http://127.0.0.1:8000>
- Admin: <http://127.0.0.1:8000/admin/>

### Variáveis de ambiente

Todas as variáveis estão documentadas no [`.env.example`](.env.example). As principais:

| Variável             | Obrigatória | Descrição                                       |
|----------------------|-------------|-------------------------------------------------|
| `CHAVE_SECRETA`      | ✅           | Secret key do Django                            |
| `DATABASE_URL`       | ✅           | URL do PostgreSQL (formato dj-database-url)     |
| `DEBUG`              | ❌           | `True` para desenvolvimento (padrão: `False`)   |
| `ALLOWED_HOSTS`      | ❌           | Hosts permitidos, separados por vírgula         |
| `CSRF_TRUSTED_ORIGINS` | ❌         | Origens confiáveis HTTPS                        |
| `BREVO_API_KEY`      | ❌           | Chave da Brevo para envio de e-mails            |
| `DEFAULT_FROM_EMAIL` | ❌           | Remetente dos e-mails                           |
| `EMAIL_REPLY_TO`     | ❌           | E-mail de resposta                              |

---

## 🧪 Testes

Os testes usam o banco configurado em `DATABASE_URL`. Para rodar:

```bash
python manage.py test
```

> Dica: para testar localmente sem tocar no banco de produção, aponte para um banco de teste, por exemplo:
> `DATABASE_URL=postgres://usuario:senha@localhost:5432/biblioteca_teste python manage.py test`

---

## 🗓️ Tarefas agendadas

O agendador é iniciado automaticamente com o Django (em produção) e roda **todos os dias às 16:18** o comando:

```bash
python manage.py avisar_prazos
```

Esse comando envia lembretes de devolução para empréstimos que vencem **hoje**, **amanhã** ou **em 2 dias**.

Para executar manualmente:

```bash
python manage.py avisar_prazos
```

> O horário da varredura é definido em [`ACERVO/updater.py`](ACERVO/updater.py).

---

## 📁 Estrutura do projeto

```
BIBLIOTECA_DJANGO/
├── ACERVO/                    # App principal
│   ├── management/commands/   # Comandos customizados (avisar_prazos)
│   ├── migrations/            # Migrações do banco
│   ├── static/                # Capas de livros e imagens de fundo
│   ├── templates/ACERVO/      # Templates do app
│   ├── admin.py               # Registro no admin (django-unfold)
│   ├── apps.py                # Config do app + inicialização do agendador
│   ├── forms.py               # Formulários (incl. cadastro customizado)
│   ├── models.py              # Aluno, Autor, Categoria, Editora, Livro, Empréstimo
│   ├── signals.py             # E-mail de boas-vindas no cadastro
│   ├── updater.py             # Agendador APScheduler
│   ├── urls.py                # Rotas do app
│   └── views.py               # Views (acervo, empréstimos, busca, dashboard)
├── BIBLIOTECA_DJANGO/         # Configurações do projeto
│   └── settings.py            # Settings (env, segurança, CSP, e-mail, banco)
├── media/                     # Uploads (PDFs) — não versionado
├── templates/account/         # Template de cadastro customizado
├── manage.py
├── Procfile                   # Comando do deploy na Railway
├── requirements.txt
└── .env.example               # Modelo de variáveis de ambiente
```

---

## 🌐 Deploy (Railway)

O projeto inclui um `Procfile` com o comando usado na Railway:

```text
web: python manage.py migrate && gunicorn BIBLIOTECA_DJANGO.wsgi --bind 0.0.0.0:$PORT
```

No painel da Railway, defina as variáveis de ambiente do [`.env.example`](.env.example) e vincule um PostgreSQL. Os arquivos estáticos são servidos pelo WhiteNoise após o `collectstatic`.

---

## 🔒 Regras de negócio dos empréstimos

- Empréstimo dura **7 dias** a partir da retirada.
- Renovação: máximo de **3 renovações** por empréstimo.
- Entre duas movimentações (retirada/renovação) é necessário aguardar **5 dias**.
- Livros **atrasados não podem ser renovados**.
- A leitura do PDF **só é liberada com empréstimo ativo dentro do prazo** — o link direto ao arquivo não funciona sem a checagem da licença.

---

## 📄 Licença

Veja o arquivo [LICENSE](LICENSE).