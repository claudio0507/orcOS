#!/bin/bash
# deploy-staging.sh: Build, Push e Deploy no cluster de Staging (K8s)

set -e

# Configurações (Placeholders para o ambiente real)
IMAGE_NAME="registry.company.com/orcos-backend"
TAG=$(git rev-parse --short HEAD)
NAMESPACE="orcos-staging"

echo ">>> Iniciando Deploy para STAGING (Tag: $TAG)..."

# 1. Build da imagem
echo ">>> Building Docker Image..."
docker build -t "$IMAGE_NAME:$TAG" -f backend/Dockerfile backend/

# 2. Login e Push (Placeholder)
# echo ">>> Pushing to Registry..."
# docker push "$IMAGE_NAME:$TAG"

# 3. Update K8s Deployment (Placeholder)
echo ">>> Atualizando Kubernetes Deployment..."
# kubectl set image deployment/orcos-api api="$IMAGE_NAME:$TAG" -n "$NAMESPACE"

# 4. Aguardar Rollout
# kubectl rollout status deployment/orcos-api -n "$NAMESPACE"

# 5. Executar Migrations em Staging (via Job efêmero)
echo ">>> Rodando migrations em Staging..."
# kubectl apply -f infra/k8s/staging/migration-job.yaml -n "$NAMESPACE"

echo ">>> Deploy para Staging finalizado!"
