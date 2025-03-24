# Usa uma imagem oficial do Python como base
FROM python:3.10

# Define o diretório de trabalho dentro do container
WORKDIR /subidopro

# Copia os arquivos do projeto para o container
COPY . /subidopro/

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Executa o comando collectstatic para coletar os arquivos estáticos
RUN python manage.py collectstatic --noinput

# Expõe a porta padrão do Django
EXPOSE 8080

# Comando para rodar o Django no Cloud Run
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "subidopro.wsgi:application"]
