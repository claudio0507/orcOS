# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências de sistema (curl para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências do Python
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copia o código da aplicação
COPY . .

# Expõe a porta do FastAPI
EXPOSE 8000

# Comando para rodar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
