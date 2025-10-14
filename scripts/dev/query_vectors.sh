#!/bin/bash
####################################################
# Script Helper para Query de Vectores en Cloud SQL
####################################################

# Credenciales (se toman del .env o se configuran aquí)
export PGPASSWORD="${CLOUD_SQL_PASSWORD:-tu_password_aqui}"
HOST="${CLOUD_SQL_HOST:-tu_host_aqui}"
USER="postgres"
DB="chatbot_db"

# Función helper
query() {
    psql -h $HOST -U $USER -d $DB -c "$1"
}

echo "🗄️ Explorando Vector Store"
echo "=========================="
echo ""

# 1. Total de vectores
echo "📊 Total de Vectores:"
query "SELECT COUNT(*) as total FROM langchain_pg_embedding;"

echo ""
echo "📋 Distribución por Tipo:"
query "SELECT cmetadata->>'type' as tipo, COUNT(*) as cantidad 
FROM langchain_pg_embedding 
GROUP BY cmetadata->>'type' 
ORDER BY cantidad DESC;"

echo ""
echo "👔 Empresas en Experiencia:"
query "SELECT DISTINCT cmetadata->>'company' as empresa 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'experience' 
AND cmetadata->>'company' IS NOT NULL;"

echo ""
echo "🎓 Instituciones Educativas:"
query "SELECT DISTINCT cmetadata->>'institution' as institucion 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'education' 
AND cmetadata->>'institution' IS NOT NULL;"

echo ""
echo "🔧 Categorías de Skills:"
query "SELECT DISTINCT cmetadata->>'category' as categoria 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'skills';"

echo ""
echo "💡 Dimensión de los Vectores:"
query "SELECT vector_dims(embedding) as dimensiones 
FROM langchain_pg_embedding 
LIMIT 1;"

echo ""
echo "✅ Query completado!"

