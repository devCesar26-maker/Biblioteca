# Imagem base com Python 3.11
FROM python:3.11-slim

# Evita gerar arquivos .pyc e mantém a saída do Python sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependências primeiro (aproveita o cache de camadas do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Diretórios de arquivos estáticos e uploads
RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000

# Aplica as migrações e coleta os estáticos automaticamente antes do Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn BIBLIOTECA_DJANGO.wsgi --bind 0.0.0.0:8000"]