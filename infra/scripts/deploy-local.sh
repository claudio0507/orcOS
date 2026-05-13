#!/bin/bash
# deploy-local.sh: Sobe ambiente de desenvolvimento local via Docker Compose

set -e

echo ">>> Iniciando deploy local do orcOS..."

# 1. Carregar variáveis de ambiente se existir .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 2. Build e Up
docker-compose -f infra/docker-compose.yml up -d --build

# 3. Aguardar DB estar pronto
echo ">>> Aguardando banco de dados..."
sleep 5

# 4. Rodar Migrations (Alembic)
echo ">>> Rodando migrations..."
docker-compose -f infra/docker-compose.yml exec -T app alembic upgrade head

# 5. Health Check
./infra/scripts/health-check.sh http://localhost:8000/health

echo ">>> Deploy local finalizado com sucesso!"
