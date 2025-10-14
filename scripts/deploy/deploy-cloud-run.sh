#!/bin/bash

#################################################
# Script de deploy a Google Cloud Run
# Despliega el backend del chatbot RAG
#################################################

set -e  # Exit on error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploy AI Resume Agent a Cloud Run${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Verificar que estamos autenticados en gcloud
echo -e "${YELLOW}Verificando autenticación GCP...${NC}"
gcloud auth list

# Leer variables de entorno (o usar valores por defecto)
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-"europe-west1"}  # Misma región que el portfolio
SERVICE_NAME="chatbot-api"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/chatbot-repo/${SERVICE_NAME}"

echo -e "\n${YELLOW}Configuración:${NC}"
echo "  Project ID: ${PROJECT_ID}"
echo "  Region: ${REGION}"
echo "  Service Name: ${SERVICE_NAME}"
echo "  Image: ${IMAGE_NAME}"

# Confirmar deploy
read -p "¿Continuar con el deploy? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}Deploy cancelado${NC}"
    exit 1
fi

# 1. Build de la imagen con Cloud Build
echo -e "\n${YELLOW}[1/4] Building Docker image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

# 2. Verificar que existe Cloud SQL instance
echo -e "\n${YELLOW}[2/4] Verificando Cloud SQL instance...${NC}"
CLOUD_SQL_INSTANCE=${CLOUD_SQL_CONNECTION_NAME:-"${PROJECT_ID}:${REGION}:almapi-chatbot-db"}
echo "  Cloud SQL: ${CLOUD_SQL_INSTANCE}"

# 3. Deploy a Cloud Run
echo -e "\n${YELLOW}[3/4] Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-env-vars "GCP_REGION=${REGION}" \
  --set-env-vars "GROQ_API_KEY=${GROQ_API_KEY}" \
  --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_INSTANCE}" \
  --set-env-vars "CLOUD_SQL_DB=${CLOUD_SQL_DB:-chatbot_db}" \
  --set-env-vars "CLOUD_SQL_USER=${CLOUD_SQL_USER:-postgres}" \
  --set-env-vars "CLOUD_SQL_PASSWORD=${CLOUD_SQL_PASSWORD}" \
  --set-env-vars "PORTFOLIO_BUCKET=${PORTFOLIO_BUCKET:-almapi-portfolio-data}" \
  --add-cloudsql-instances ${CLOUD_SQL_INSTANCE} \
  --project ${PROJECT_ID}

# 4. Obtener URL del servicio
echo -e "\n${YELLOW}[4/4] Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)' \
  --project ${PROJECT_ID})

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deploy completado exitosamente!${NC}"
echo -e "${GREEN}========================================${NC}\n"
echo -e "Service URL: ${GREEN}${SERVICE_URL}${NC}"
echo -e "Health Check: ${GREEN}${SERVICE_URL}/api/v1/health${NC}"
echo -e "API Docs: ${GREEN}${SERVICE_URL}/docs${NC}"

# Test del health endpoint
echo -e "\n${YELLOW}Testing health endpoint...${NC}"
curl -s "${SERVICE_URL}/api/v1/health" | python3 -m json.tool

echo -e "\n${GREEN}✓ Todo listo!${NC}\n"

