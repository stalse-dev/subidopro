# Usa uma imagem oficial do Python como base
FROM python:3.10-slim

# Evita prompts interativos durante builds e garante logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define a porta que o Cloud Run usará
ENV PORT=8080

# Cria e define o diretório de trabalho para a aplicação
WORKDIR /subidopro

# Instala dependências do sistema necessárias para pacotes Python como Pillow e Psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências Python para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
# **Certifique-se de que seus arquivos estáticos (pastas 'static' dentro dos apps ou STATICFILES_DIRS)
# estejam incluídos aqui e não excluídos por um .dockerignore**
COPY . .

# Garante que a pasta STATIC_ROOT exista para o collectstatic
RUN mkdir -p /subidopro/staticfiles

# Expõe a porta para o Cloud Run
EXPOSE $PORT

# Comando principal para rodar o collectstatic e iniciar o Gunicorn
# **Atenção: A chave para o sucesso está na configuração correta do STATIC_ROOT no seu settings.py**
CMD sh -c "python manage.py collectstatic --noinput && gunicorn subidopro.wsgi:application --bind 0.0.0.0:$PORT"