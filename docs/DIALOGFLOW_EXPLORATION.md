# 🤖 Exploración de Dialogflow ES

## 📋 Resumen

Este documento describe cómo explorar y configurar Dialogflow ES para el proyecto AI Resume Agent. Incluye scripts de prueba, configuración de agentes, y ejemplos de intents.

## 🎯 Objetivos

1. **Probar conexión** con Dialogflow ES
2. **Crear agente básico** para portfolio profesional
3. **Configurar intents** principales (welcome, experience, skills, contact, availability)
4. **Integrar datos** del portfolio en formato YAML
5. **Preparar integración** con el backend FastAPI

## 🚀 Inicio Rápido

### 1. Instalar Dependencias
```bash
# Opción 1: Usar el script
python scripts/install_dialogflow_deps.py

# Opción 2: Manual
pip install google-cloud-dialogflow google-cloud-aiplatform pyyaml python-dotenv
```

### 2. Configurar GCP
```bash
# Configurar proyecto
export GCP_PROJECT_ID="tu-proyecto-id"

# Autenticar (opción 1: para desarrollo)
gcloud auth application-default login

# O usar service account (opción 2: para producción)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### 3. Habilitar APIs
```bash
gcloud services enable dialogflow.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 4. Ejecutar Test
```bash
# Test simple de conexión
python scripts/test_dialogflow_simple.py

# Test avanzado con menú interactivo
python scripts/explore_dialogflow.py
```

## 📁 Estructura de Archivos

```
scripts/
├── explore_dialogflow.py          # Script avanzado con menú interactivo
├── test_dialogflow_simple.py      # Test básico de conexión
├── install_dialogflow_deps.py     # Instalador de dependencias
└── dialogflow_setup.md            # Guía de configuración

data/
└── portfolio.yaml                 # Datos del portfolio estructurados

docs/
└── DIALOGFLOW_EXPLORATION.md      # Este documento
```

## 🎭 Intents del Portfolio

### 1. **welcome** - Saludo inicial
**Frases de entrenamiento:**
- "Hola"
- "Buenos días"
- "¿Cómo estás?"
- "Saludos"
- "Hi"
- "Hello"

**Respuestas:**
- "¡Hola! Soy el asistente virtual de Alberto Maldonado. ¿En qué puedo ayudarte?"
- "¡Buenos días! Bienvenido a mi portfolio profesional. ¿Te gustaría conocer más sobre mi experiencia?"

### 2. **experience** - Experiencia laboral
**Frases de entrenamiento:**
- "¿Cuál es tu experiencia?"
- "¿Dónde has trabajado?"
- "Cuéntame sobre tu experiencia laboral"
- "¿Qué empresas has trabajado?"
- "¿Cuántos años de experiencia tienes?"

**Respuestas:**
- "Tengo más de 5 años de experiencia como AI/ML Engineer y Full-Stack Developer. He trabajado en TechCorp Solutions, DataFlow Inc, y StartupXYZ."
- "Mi experiencia incluye desarrollo de sistemas de IA, chatbots inteligentes, y arquitecturas escalables en la nube."

### 3. **skills** - Habilidades técnicas
**Frases de entrenamiento:**
- "¿Cuáles son tus habilidades?"
- "¿Qué tecnologías manejas?"
- "¿Qué lenguajes de programación conoces?"
- "¿Cuáles son tus skills principales?"
- "¿Qué frameworks usas?"

**Respuestas:**
- "Mis habilidades principales incluyen Python (Expert), JavaScript/TypeScript (Advanced), FastAPI, React, TensorFlow, y Google Cloud Platform."
- "Soy experto en desarrollo de APIs, sistemas de ML, y arquitecturas cloud. También tengo experiencia con Docker, Kubernetes, y bases de datos como PostgreSQL y Redis."

### 4. **contact** - Información de contacto
**Frases de entrenamiento:**
- "¿Cómo puedo contactarte?"
- "¿Cuál es tu email?"
- "¿Dónde te puedes encontrar?"
- "¿Cómo te contacto?"
- "¿Tienes LinkedIn?"

**Respuestas:**
- "Puedes contactarme en alberto@almapi.dev o a través de LinkedIn: https://linkedin.com/in/albertomaldonado"
- "Mi teléfono es +52 55 1234 5678. También puedes visitar mi sitio web: https://almapi.dev"

### 5. **availability** - Disponibilidad laboral
**Frases de entrenamiento:**
- "¿Estás disponible para trabajar?"
- "¿Estás buscando trabajo?"
- "¿Tienes disponibilidad?"
- "¿Estás abierto a proyectos?"
- "¿Trabajas remoto?"

**Respuestas:**
- "Sí, estoy disponible para proyectos y trabajo remoto. Mi periodo de aviso es de 2 semanas."
- "Estoy abierto a oportunidades de largo plazo, consultoría técnica, y desarrollo de productos. Trabajo completamente remoto."

## 📊 Datos del Portfolio

El archivo `data/portfolio.yaml` contiene toda la información profesional estructurada:

- **Información personal**: Nombre, título, contacto
- **Experiencia laboral**: Empresas, posiciones, logros
- **Educación**: Grados, certificaciones
- **Habilidades**: Lenguajes, frameworks, herramientas
- **Proyectos**: Descripción, tecnologías, enlaces
- **Disponibilidad**: Estado, preferencias, timezone

## 🔧 Scripts Disponibles

### `test_dialogflow_simple.py`
- **Propósito**: Test básico de conexión
- **Requisitos**: Solo `GCP_PROJECT_ID`
- **Funciones**: Verificar conexión, listar agentes, probar detección

### `explore_dialogflow.py`
- **Propósito**: Exploración completa con menú interactivo
- **Requisitos**: Configuración completa de credenciales
- **Funciones**: Crear agentes, intents, probar detección, cargar datos

### `install_dialogflow_deps.py`
- **Propósito**: Instalar dependencias necesarias
- **Requisitos**: Python y pip
- **Funciones**: Instalar paquetes de Google Cloud

## 🚨 Troubleshooting

### Error: "Project not found"
```bash
# Verificar proyectos disponibles
gcloud projects list

# Configurar proyecto
gcloud config set project YOUR_PROJECT_ID
export GCP_PROJECT_ID="YOUR_PROJECT_ID"
```

### Error: "API not enabled"
```bash
# Habilitar APIs necesarias
gcloud services enable dialogflow.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### Error: "Permission denied"
```bash
# Verificar permisos
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Asignar rol necesario
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:tu-email@gmail.com" \
    --role="roles/dialogflow.admin"
```

### Error: "Authentication failed"
```bash
# Opción 1: Application Default Credentials
gcloud auth application-default login

# Opción 2: Service Account
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
```

## 🔄 Próximos Pasos

1. **✅ Probar conexión básica**
2. **✅ Crear agente en consola de Dialogflow**
3. **✅ Configurar intents básicos**
4. **🔄 Integrar con backend FastAPI**
5. **🔄 Implementar Smart Context Filtering**
6. **🔄 Configurar Vertex AI para casos complejos**
7. **🔄 Desplegar a producción**

## 📚 Recursos Adicionales

- [Documentación de Dialogflow ES](https://cloud.google.com/dialogflow/es/docs)
- [Consola de Dialogflow](https://console.cloud.google.com/dialogflow)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [API Reference](https://cloud.google.com/dialogflow/es/docs/reference/rest)
