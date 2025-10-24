#!/bin/bash

# Script para actualizar el vector store en producción
# Ejecutar después de hacer cambios en build_knowledge_base.py

echo "🚀 Actualizando Vector Store en Producción"
echo "=========================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "scripts/setup/initialize_vector_store.py" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar que gcloud está configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI no está instalado"
    exit 1
fi

# Verificar autenticación
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: No estás autenticado con gcloud"
    echo "Ejecuta: gcloud auth login"
    exit 1
fi

echo "✅ Verificaciones completadas"
echo ""

# Ejecutar el script de inicialización
echo "📚 Ejecutando inicialización del vector store..."
python scripts/setup/initialize_vector_store.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Vector store actualizado exitosamente"
    echo "🔄 Reinicia el servicio Cloud Run para aplicar los cambios:"
    echo "   gcloud run services update chatbot-api --region=europe-west1"
else
    echo ""
    echo "❌ Error actualizando vector store"
    exit 1
fi
