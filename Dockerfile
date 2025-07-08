# Usa uma imagem oficial do Python como base
FROM python:3.10

# Define o diretório de trabalho dentro do container
WORKDIR /subidopro

# Copia apenas os arquivos essenciais primeiro (para otimizar o cache)
COPY requirements.txt /subidopro/

# Instala as dependências antes de copiar o restante do código
RUN pip install --no-cache-dir -r requirements.txt

# Agora copia o restante do projeto
COPY . /subidopro/

# Garante que a pasta de arquivos estáticos exista
RUN mkdir -p /subidopro/staticfiles



# Expõe a porta padrão do Django
EXPOSE $PORT

# Comando de entrada do container
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:$PORT subidopro.wsgi:application"]