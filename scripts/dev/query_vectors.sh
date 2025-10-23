#!/bin/bash
####################################################
# Script Helper para Query de Vectores en Cloud SQL
####################################################

# Cargar variables de entorno
if [ -f "../../.env" ]; then
    source ../../.env
elif [ -f "../.env" ]; then
    source ../.env
fi

# Credenciales (se toman del .env o se configuran aquí)
export PGPASSWORD="${CLOUD_SQL_PASSWORD}"
HOST="${CLOUD_SQL_HOST}"
USER="postgres"
DB="chatbot_db"

# Verificar que las variables estén configuradas
if [ -z "$CLOUD_SQL_PASSWORD" ] || [ -z "$CLOUD_SQL_HOST" ]; then
    echo "❌ Error: Variables CLOUD_SQL_PASSWORD y CLOUD_SQL_HOST no están configuradas"
    echo "   Asegúrate de tener un archivo .env con estas variables"
    exit 1
fi

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
echo "🏢 Empresas en Proyectos:"
query "SELECT DISTINCT cmetadata->>'company_ref' as empresa 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'project' 
AND cmetadata->>'company_ref' IS NOT NULL;"

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
WHERE cmetadata->>'type' = 'skills_category';"

echo ""
echo "💼 Skills Showcase:"
query "SELECT DISTINCT cmetadata->>'skill_name' as skill 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'skill_showcase' 
AND cmetadata->>'skill_name' IS NOT NULL;"

echo ""
echo "🛠️ Tecnologías Principales:"
query "SELECT DISTINCT cmetadata->>'technology' as tecnologia 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'technology' 
AND cmetadata->>'technology' IS NOT NULL 
LIMIT 10;"

echo ""
echo "📋 Proyectos Principales:"
query "SELECT DISTINCT cmetadata->>'project_name' as proyecto 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'project' 
AND cmetadata->>'project_name' IS NOT NULL;"

echo ""
echo "💡 Información Personal:"
query "SELECT cmetadata->>'name' as nombre, cmetadata->>'location' as ubicacion 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'personal_info';"

echo ""
echo "💡 Filosofía y Motivación:"
query "SELECT cmetadata->>'title' as titulo 
FROM langchain_pg_embedding 
WHERE cmetadata->>'type' = 'philosophy';"

echo ""
echo "💡 Dimensión de los Vectores:"
query "SELECT vector_dims(embedding) as dimensiones 
FROM langchain_pg_embedding 
LIMIT 1;"

echo ""
echo "✅ Query completado!"

