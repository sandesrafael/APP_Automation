# Dockerfile para APP_Automation API
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (se necessário para xlrd, openpyxl, etc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (melhor cache de build)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretório de logs
RUN mkdir -p /app/logs

# Expõe porta da API
EXPOSE 8080

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Comando para iniciar a aplicação
CMD ["python", "run.py"]
