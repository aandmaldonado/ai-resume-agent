#!/bin/bash
# 🔧 CONFIGURACIÓN LOCAL - AI Resume Agent v5.1
# Script para configurar variables de entorno desde archivo .env

echo "🔧 Configurando entorno local desde archivo .env..."

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "❌ No se encontró el archivo .env"
    echo "💡 Crea un archivo .env con las siguientes variables:"
    echo "   GEMINI_API_KEY=tu_api_key_aqui"
    echo "   CLOUD_SQL_PASSWORD=tu_password_aqui"
    echo "   CLOUD_SQL_HOST=34.76.123.45"
    exit 1
fi

echo "✅ Archivo .env encontrado"

# Cargar variables desde .env
export $(grep -v '^#' .env | xargs)

# Verificar que las variables necesarias estén definidas
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY no está definida en .env"
    exit 1
fi

if [ -z "$CLOUD_SQL_PASSWORD" ]; then
    echo "❌ CLOUD_SQL_PASSWORD no está definida en .env"
    exit 1
fi

if [ -z "$CLOUD_SQL_HOST" ]; then
    echo "⚠️ CLOUD_SQL_HOST no está definida en .env, usando valor por defecto"
    export CLOUD_SQL_HOST="34.76.123.45"
fi

# Configurar variables adicionales
export VECTOR_SEARCH_K="20"
export GEMINI_TEMPERATURE="0.7"
export GEMINI_TOP_P="0.8"
export GEMINI_MAX_TOKENS="1000"

echo "✅ Variables de entorno configuradas desde .env:"
echo "   GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "   CLOUD_SQL_PASSWORD: ${CLOUD_SQL_PASSWORD:0:5}..."
echo "   CLOUD_SQL_HOST: $CLOUD_SQL_HOST"
echo "   VECTOR_SEARCH_K: $VECTOR_SEARCH_K"

echo ""
echo "🚀 Ahora puedes ejecutar el testing local:"
echo "   python scripts/test/test_local_v51.py"
echo ""
echo "💡 O ejecutar el servidor local:"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
