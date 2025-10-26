#!/bin/bash
# 🧪 TESTING SERVIDOR LOCAL - AI Resume Agent v5.1
# Script para probar el servidor local con curl

echo "🧪 Testing Servidor Local - Prompt v5.1 Anti-Alucinación"
echo "=" * 60

# Verificar que el servidor esté corriendo
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ El servidor no está corriendo en localhost:8000"
    echo "💡 Ejecuta primero: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Servidor local detectado"

# Función para probar una pregunta
test_question() {
    local question="$1"
    local expected="$2"
    
    echo ""
    echo "🧪 Probando: '$question'"
    echo "📋 Esperado: $expected"
    
    response=$(curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d "{
            \"message\": \"$question\",
            \"session_id\": \"test-local-v51\",
            \"user_type\": \"IT\",
            \"data_capture_enabled\": false,
            \"gdpr_consent\": false
        }")
    
    if [ $? -eq 0 ]; then
        message=$(echo "$response" | jq -r '.message // .response // "Error parsing response"')
        fidelity=$(echo "$response" | jq -r '.fidelity_check // "unknown"')
        sources=$(echo "$response" | jq -r '.sources | length // 0')
        
        echo "✅ Respuesta: $message"
        echo "🔍 Fidelidad: $fidelity"
        echo "📚 Fuentes: $sources"
    else
        echo "❌ Error en la petición"
    fi
    
    sleep 1  # Pausa para evitar rate limiting
}

# Suite de tests
echo "🚀 Iniciando suite de tests..."

# Tests básicos
test_question "¿Quién eres?" "identidad"
test_question "¿Cuál es tu formación académica?" "educación"
test_question "¿Qué idiomas manejas?" "idiomas"

# Tests de experiencia
test_question "¿Cuál es tu experiencia con Java?" "experiencia"
test_question "¿Qué proyectos de IA has liderado?" "proyectos"

# Tests de comportamiento
test_question "Describe una situación donde actuaste como puente entre negocio y tecnología" "comportamiento"
test_question "¿Cuál fue el logro más significativo en AcuaMattic?" "comportamiento"

# Tests de motivación
test_question "¿Cuál es tu motivación para un nuevo reto profesional?" "motivación"

# Tests de condiciones laborales
test_question "¿Cuáles son tus expectativas salariales?" "condiciones"
test_question "¿Buscas trabajo remoto?" "condiciones"

# Tests de tecnologías ausentes
test_question "¿Tienes certificación en AWS?" "tecnología_ausente"
test_question "¿Conoces React?" "tecnología_ausente"

# Tests off-topic
test_question "¿Cuál es tu comida favorita?" "off_topic"

# Tests complejos
test_question "¿Cuál es tu experiencia con Python en proyectos de IA?" "compleja"

echo ""
echo "🎉 Testing completado!"
echo "💡 Revisa los resultados antes de hacer cualquier deploy a GCP"
