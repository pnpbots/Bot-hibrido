#!/bin/bash
# PNP Bot - Deploy Script para Google Cloud Run

set -e  # Exit on error

PROJECT_ID="pnptelevision"
SERVICE_NAME="pnp-bot"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Iniciando deploy de PNP Bot..."

# 1. Verificar que estamos en el proyecto correcto
echo "📋 Verificando proyecto..."
gcloud config set project $PROJECT_ID

# 2. Construir imagen
echo "🔨 Construyendo imagen Docker..."
docker build -t $IMAGE_NAME:latest .

# 3. Subir imagen
echo "📤 Subiendo imagen a Google Container Registry..."
docker push $IMAGE_NAME:latest

# 4. Deploy a Cloud Run
echo "🚀 Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars BOT_TOKEN=7708250634:AAFEEXrY8lqAOOhp6B-EdnzXZuAP_sVQrYY \
  --set-env-vars ADMIN_USER_ID=7940478393 \
  --set-env-vars CHANNEL_NAME="PNP Television" \
  --set-env-vars LOG_LEVEL=INFO \
  --set-env-vars ENABLE_SCHEDULER=true \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 3 \
  --timeout 3600 \
  --concurrency 80 \
  --port 8080

# 5. Obtener URL del servicio
echo "✅ Deploy completado!"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo "🌐 Servicio disponible en: $SERVICE_URL"

echo "🤖 Bot desplegado exitosamente!"