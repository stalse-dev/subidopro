# Usa uma imagem oficial do Python como base
FROM python:3.10-slim

# Evita prompts interativos durante builds
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Cria diretório de trabalho
WORKDIR /subidopro

# Instala dependências do sistema (pillow, psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Garante a existência da pasta de arquivos estáticos
RUN mkdir -p /subidopro/staticfiles

# Expõe a porta que o Cloud Run usará
EXPOSE $PORT

# Comando que roda o collectstatic e inicia o servidor Gunicorn
# CMD sh -c "python manage.py collectstatic --noinput && gunicorn subidopro.wsgi:application --bind 0.0.0.0:$PORT"
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
