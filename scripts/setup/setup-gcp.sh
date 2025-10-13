#!/bin/bash

#################################################
# Script de setup inicial de infraestructura GCP
# Configura Cloud SQL, Cloud Storage y APIs
#################################################

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup de Infraestructura GCP${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Variables
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-"europe-west1"}  # Misma región que el portfolio
DB_INSTANCE_NAME="almapi-chatbot-db"
DB_NAME="chatbot_db"
BUCKET_NAME="almapi-portfolio-data"

echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"

# 1. Habilitar APIs necesarias
echo -e "\n${YELLOW}[1/5] Habilitando APIs de GCP...${NC}"
gcloud services enable aiplatform.googleapis.com \
  sqladmin.googleapis.com \
  run.googleapis.com \
  storage-api.googleapis.com \
  cloudbuild.googleapis.com \
  --project ${PROJECT_ID}

echo -e "${GREEN}✓ APIs habilitadas${NC}"

# 2. Crear Cloud SQL instance
echo -e "\n${YELLOW}[2/5] Creando Cloud SQL instance...${NC}"
if gcloud sql instances describe ${DB_INSTANCE_NAME} --project ${PROJECT_ID} &> /dev/null; then
  echo -e "${YELLOW}Cloud SQL instance ya existe${NC}"
  
  # Verificar si está detenida e iniciarla
  INSTANCE_STATE=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --project ${PROJECT_ID} --format="value(state)")
  if [ "$INSTANCE_STATE" != "RUNNABLE" ]; then
    echo -e "${YELLOW}La instancia está detenida. Iniciando...${NC}"
    gcloud sql instances patch ${DB_INSTANCE_NAME} \
      --activation-policy=ALWAYS \
      --project ${PROJECT_ID}
    
    echo -e "${GREEN}✓ Instancia iniciada${NC}"
    echo -e "${YELLOW}Esperando a que esté lista (puede tardar 1-2 minutos)...${NC}"
    sleep 30
  else
    echo -e "${GREEN}✓ Instancia ya está corriendo${NC}"
  fi
else
  gcloud sql instances create ${DB_INSTANCE_NAME} \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=${REGION} \
    --no-backup \
    --activation-policy=ALWAYS \
    --project ${PROJECT_ID}
  
  echo -e "${GREEN}✓ Cloud SQL instance creada${NC}"
  echo -e "${YELLOW}Esperando a que esté lista (puede tardar 2-3 minutos)...${NC}"
  sleep 60
fi

# 3. Crear database
echo -e "\n${YELLOW}[3/5] Creando database...${NC}"
if gcloud sql databases describe ${DB_NAME} --instance=${DB_INSTANCE_NAME} --project ${PROJECT_ID} &> /dev/null; then
  echo -e "${YELLOW}Database ya existe${NC}"
else
  gcloud sql databases create ${DB_NAME} \
    --instance=${DB_INSTANCE_NAME} \
    --project ${PROJECT_ID}
  
  echo -e "${GREEN}✓ Database creada${NC}"
fi

# 4. Instalar extensión pgvector
echo -e "\n${YELLOW}[4/5] Instalando extensión pgvector...${NC}"
echo -e "${YELLOW}Necesitas conectarte manualmente y ejecutar:${NC}"
echo -e "  gcloud sql connect ${DB_INSTANCE_NAME} --user=postgres"
echo -e "  CREATE EXTENSION IF NOT EXISTS vector;"
echo -e "\nPresiona Enter cuando hayas completado esto..."
read

# 5. Crear bucket de Cloud Storage
echo -e "\n${YELLOW}[5/5] Creando bucket de Cloud Storage...${NC}"
if gsutil ls -b gs://${BUCKET_NAME} &> /dev/null; then
  echo -e "${YELLOW}Bucket ya existe${NC}"
else
  gsutil mb -l ${REGION} gs://${BUCKET_NAME}
  echo -e "${GREEN}✓ Bucket creado${NC}"
fi

# 6. Subir portfolio.yaml
echo -e "\n${YELLOW}Subiendo portfolio.yaml al bucket...${NC}"
if [ -f "data/portfolio.yaml" ]; then
  gsutil cp data/portfolio.yaml gs://${BUCKET_NAME}/
  echo -e "${GREEN}✓ portfolio.yaml subido${NC}"
else
  echo -e "${RED}⚠ Advertencia: data/portfolio.yaml no encontrado${NC}"
fi

# Resumen
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Setup completado!${NC}"
echo -e "${GREEN}========================================${NC}\n"
echo -e "Cloud SQL Instance: ${GREEN}${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}${NC}"
echo -e "Database: ${GREEN}${DB_NAME}${NC}"
echo -e "Bucket: ${GREEN}gs://${BUCKET_NAME}${NC}"

echo -e "\n${YELLOW}Próximos pasos:${NC}"
echo "1. Obtener API key de Groq: https://console.groq.com"
echo "2. Configurar variables de entorno en .env"
echo "3. Ejecutar: python scripts/initialize_vector_store.py"
echo "4. Deploy: ./deploy-cloud-run.sh"

echo ""

