#!/bin/bash
# health-check.sh: Verifica se o serviço está online

URL=${1:-"http://localhost:8000/health"}
MAX_RETRIES=${2:-12}
SLEEP_INTERVAL=${3:-5}

echo "Iniciando health check em $URL..."

for ((i=1; i<=MAX_RETRIES; i++)); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
    
    if [ "$STATUS" -eq 200 ]; then
        echo "SUCESSO: Serviço online (Status 200) após $i tentativas."
        exit 0
    fi
    
    echo "Tentativa $i/$MAX_RETRIES: Status $STATUS. Aguardando ${SLEEP_INTERVAL}s..."
    sleep $SLEEP_INTERVAL
done

echo "ERRO: Serviço não respondeu com 200 após $MAX_RETRIES tentativas."
exit 1
