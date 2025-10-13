#!/bin/bash
################################
# Script para iniciar el chatbot localmente
################################

set -e

echo "🚀 Iniciando AI Resume Agent Localmente"
echo "======================================="
echo ""

# Verificar venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment no encontrado"
    echo "   Ejecuta: python3.11 -m venv venv"
    exit 1
fi

# Verificar .env
if [ ! -f ".env" ]; then
    echo "❌ Archivo .env no encontrado"
    echo "   Copia ENV_TEMPLATE.md y crea tu .env"
    exit 1
fi

echo "✓ Virtual environment encontrado"
echo "✓ Archivo .env encontrado"
echo ""

# Activar venv y verificar Python
source venv/bin/activate
PYTHON_VERSION=$(python --version)
echo "✓ Python: $PYTHON_VERSION"
echo ""

# Verificar conexión a Cloud SQL (usa variables de .env)
echo "🔍 Verificando conexión a Cloud SQL..."
source .env 2>/dev/null || true
PGPASSWORD="${CLOUD_SQL_PASSWORD}" psql \
  -h "${CLOUD_SQL_HOST}" \
  -U postgres \
  -d chatbot_db \
  -c "SELECT COUNT(*) as vectores FROM langchain_pg_embedding;" \
  2>/dev/null || {
    echo "⚠️  No se puede conectar a Cloud SQL"
    echo "   El backend iniciará pero puede fallar al procesar queries"
    echo ""
}

echo "✓ Verificación completada"
echo ""

# Iniciar backend
echo "🚀 Iniciando backend FastAPI..."
echo "   URL: http://localhost:8080"
echo "   Docs: http://localhost:8080/docs"
echo ""
echo "💡 Para probar el frontend, en otra terminal ejecuta:"
echo "   python3 -m http.server 3000"
echo "   Luego abre: http://localhost:3000/test-local.html"
echo ""
echo "📝 Logs del servidor:"
echo "===================="
echo ""

# Ejecutar uvicorn (esto bloquea hasta Ctrl+C)
uvicorn app.main:app --reload --port 8080 --host 0.0.0.0

