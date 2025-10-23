# 🤖 AI Resume Agent

Chatbot RAG (Retrieval Augmented Generation) para portfolio profesional. Responde preguntas sobre experiencia, habilidades y proyectos usando tecnologías **100% gratuitas** en la nube.

## 🎯 Características

- ✅ **100% Cloud**: Desplegado en Google Cloud Run (europe-west1)
- ✅ **100% Gratis**: Usa free tiers de Gemini, HuggingFace y GCP
- ✅ **Ultra Rápido**: Gemini 2.5 Flash con respuestas optimizadas
- ✅ **RAG Avanzado**: Retrieval con pgvector + embeddings locales
- ✅ **Sin Dependencias Pagas**: HuggingFace embeddings locales (no requiere APIs)
- ✅ **Seguro**: CORS, validación de inputs, usuario no-root
- ✅ **Documentación Completa**: 860+ líneas de guías y troubleshooting

## 🏗️ Arquitectura

```
Cliente (Browser/App)
    ↓ HTTP/REST
Backend API (FastAPI/Cloud Run)
    ↓
RAG Pipeline:
  1. Query Embedding → HuggingFace (local, sentence-transformers)
  2. Semantic Search → pgvector (Cloud SQL)
  3. Context Retrieval → Top-K chunks
  4. Response Generation → Gemini 2.5 Flash
    ↓
Knowledge Base (portfolio.yaml → 70 vectores indexados)
```

## 💰 Costos (Free Tier)

| Servicio | Límite Gratuito | Uso Actual | Costo |
|----------|-----------------|------------|-------|
| Gemini API | 15 requests/min | ~500 tokens/query | $0/mes |
| HuggingFace | Ilimitado (local) | Embeddings 384-dim | $0/mes |
| Cloud SQL (f1-micro) | Included | PostgreSQL + pgvector | $0/mes |
| Cloud Run | 2M requests/mes | ~1K requests/mes | $0/mes |
| Artifact Registry | 0.5GB gratis | ~1.2GB (1 imagen) | $0/mes |
| **TOTAL** | - | - | **$0/mes** ✅ |

## 🚀 Quick Start

### Prerrequisitos

- **Python 3.11** (requerido - ver `.python-version`)
- Cuenta de Google Cloud Platform (con billing habilitado para free tier)
- Cuenta de Google con Gemini API habilitada (gratis con Google Workspace)

## 🔧 Desarrollo con Pre-commit Hooks

Este proyecto incluye **pre-commit hooks** para garantizar calidad de código enterprise-level:

### Instalación de Pre-commit

```bash
# 1. Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar pre-commit hooks
pre-commit install
```

### Hooks Automáticos

Cada commit ejecuta automáticamente:

| Hook | Función | Cobertura |
|------|---------|-----------|
| 🧪 **Tests** | 59 tests unitarios con pytest | 94% cobertura |
| 🔒 **Security Scan** | Bandit para vulnerabilidades | 0 vulnerabilidades |
| 🎨 **Code Formatting** | Black para código limpio | 100% archivos |
| 📦 **Import Organization** | isort para imports ordenados | 100% archivos |
| 🛡️ **Dependency Scan** | Safety para dependencias vulnerables | 0 vulnerabilidades |

### Comandos de Desarrollo

```bash
# Ejecutar todos los hooks manualmente
pre-commit run --all-files

# Ejecutar hooks específicos
pre-commit run pytest --all-files
pre-commit run bandit --all-files
pre-commit run black --all-files

# Commit con hooks automáticos
git add .
git commit -m "feat: nueva funcionalidad"
# ↑ Los hooks se ejecutan automáticamente
```

### Estructura de Tests

```
tests/
├── test_api_endpoints.py    # 20 tests - Endpoints API
├── test_main.py            # 16 tests - Aplicación principal  
├── test_rag_service.py     # 7 tests - Servicio RAG
├── test_secrets.py         # 15 tests - Gestión de secretos
└── test_memory.py          # 1 test - Memoria conversacional
```

**Total: 59 tests con 94% cobertura de código**

### 1. Setup de Infraestructura GCP

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/ai-resume-agent.git
cd ai-resume-agent

# Autenticar en GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Ejecutar setup automático
chmod +x scripts/setup/setup-gcp.sh
./scripts/setup/setup-gcp.sh
```

**Esto creará automáticamente**:
- ✅ Cloud SQL instance (PostgreSQL 15 + pgvector)
- ✅ Base de datos `chatbot_db`
- ✅ Artifact Registry repository
- ✅ Habilitará APIs necesarias
- ✅ Generará archivo `.env` con valores

### 2. Configurar Variables de Entorno

El script de setup genera `.env` automáticamente. Solo necesitas agregar tu **Gemini API Key**:

```bash
# Editar .env
nano .env

# Agregar/verificar:
GEMINI_API_KEY=AI...  # Obtener en aistudio.google.com/app/apikey
```

Ver `ENV_TEMPLATE.md` para referencia completa de variables.

### 3. Inicializar Vector Store

```bash
# Crear virtual environment con Python 3.11
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Procesar portfolio y cargar a pgvector
python scripts/setup/initialize_vector_store.py
```

**Este script**:
1. ✅ Lee `data/portfolio.yaml` (o `portfolio-es.yaml`)
2. ✅ Divide en ~70 chunks semánticos
3. ✅ Genera embeddings con HuggingFace (local, 384-dim)
4. ✅ Guarda en Cloud SQL (pgvector)

**Output esperado**: 
```
✓ Portfolio cargado: 70 chunks
✓ Embeddings generados (dimensión: 384)
✓ Guardado en pgvector
✅ Vector store inicializado correctamente
```

### 4. Deploy del Backend

```bash
# Deploy a Cloud Run
chmod +x scripts/deploy/deploy-cloud-run.sh
./scripts/deploy/deploy-cloud-run.sh
```

**Esto**:
1. ✅ Construye imagen Docker (~1.2GB)
2. ✅ Sube a Artifact Registry (europe-west1)
3. ✅ Despliega en Cloud Run (2GB RAM, 2 vCPUs)
4. ✅ Configura Cloud SQL connection
5. ✅ Retorna URL del servicio

**Tiempo estimado**: 8-12 minutos

### 5. Probar el Chatbot

#### Opción A: Test Local (Sin Auth)

```bash
# Terminal 1: Iniciar backend
./start-local.sh

# Terminal 2: Iniciar servidor HTTP para frontend
python3 -m http.server 3000

# Navegador: Abrir
http://localhost:3000/test-local.html
```

#### Opción B: Test en Cloud Run (Con Auth)

```bash
# Obtener token de autenticación
TOKEN=$(gcloud auth print-identity-token)

# Test health check
curl -H "Authorization: Bearer $TOKEN" \
  https://chatbot-api-[YOUR-HASH].europe-west1.run.app/api/v1/health

# Test chat
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"¿Cuál es tu experiencia profesional?"}' \
  https://chatbot-api-[YOUR-HASH].europe-west1.run.app/api/v1/chat
```

#### Opción C: Swagger UI

Abrir en navegador: `https://[YOUR-URL]/docs` (requiere auth)

### 6. Integrar a Tu Portfolio

Ver **instrucciones detalladas** en: `docs/INTEGRACION_FRONTEND.md`

**Código mínimo (React)**:
```jsx
import React from 'react';

const ChatBot = () => {
  const API_URL = 'https://your-cloud-run-url/api/v1';
  
  const sendMessage = async (message) => {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    return await response.json();
  };
  
  // ... UI implementation
};
```

## 📁 Estructura del Proyecto

```
ai-resume-agent/
├── app/                          # Backend FastAPI
│   ├── main.py                  # Aplicación principal
│   ├── core/
│   │   └── config.py            # Configuración centralizada
│   ├── services/
│   │   └── rag_service.py       # Servicio RAG (Gemini + HuggingFace + pgvector)
│   ├── api/v1/endpoints/
│   │   └── chat.py              # Endpoints /chat y /health
│   └── schemas/
│       └── chat.py              # Modelos Pydantic
│
├── scripts/                      # Scripts organizados por propósito
│   ├── setup/                   # 🔧 Configuración inicial (usar 1 vez)
│   │   ├── setup-gcp.sh         # Setup completo de GCP
│   │   ├── initialize_vector_store.py  # Indexar portfolio
│   │   ├── prepare_knowledge_base.py   # Procesar YAML
│   │   └── README.md            # Guía de scripts de setup
│   ├── deploy/                  # 🚀 Despliegue a producción
│   │   ├── deploy-cloud-run.sh  # Deploy completo
│   │   └── README.md            # Guía de deploy
│   ├── dev/                     # 🛠️ Desarrollo y debugging
│   │   ├── query_vectors.sh     # Explorar vector store
│   │   └── README.md            # Guía de dev
│   └── README.md                # Índice general de scripts
│
├── data/
│   ├── portfolio.yaml           # Knowledge base principal
│   ├── portfolio-es.yaml        # Versión en español
│   └── portfolio-en.yaml        # Versión en inglés
│
├── docs/                        # 📚 Documentación completa
│   ├── design.md               # Diseño del sistema
│   ├── tech-solution.md        # Solución técnica
│   └── ...
│
├── tests/                       # Tests unitarios e integración
│   ├── unit/
│   ├── integration/
│   └── security/
│
├── Dockerfile                   # Imagen Docker optimizada (1.2GB)
├── requirements.txt             # Dependencias Python (LangChain, FastAPI, etc.)
├── .python-version              # Python 3.11 (para pyenv)
├── start-local.sh               # Script para desarrollo local
├── test-local.html              # UI de prueba sin framework
├── ENV_TEMPLATE.md              # Template de variables de entorno
└── README.md                    # Este archivo
```

**Scripts Rápidos**:
```bash
./scripts/setup/setup-gcp.sh              # Primera vez
python scripts/setup/initialize_vector_store.py  # Indexar datos
./scripts/deploy/deploy-cloud-run.sh      # Deploy a producción
./scripts/dev/query_vectors.sh            # Debug vectores
./start-local.sh                          # Desarrollo local
```

## 🔧 Desarrollo Local

### Método 1: Script Automatizado (Recomendado)

```bash
# Todo en uno: verifica deps, conecta BD, inicia backend
./start-local.sh
```

**Luego en otro terminal**:
```bash
# Servidor HTTP para test-local.html
python3 -m http.server 3000

# Abrir: http://localhost:3000/test-local.html
```

### Método 2: Manual

```bash
# 1. Crear virtual environment con Python 3.11
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Verificar versión
python --version  # Debe mostrar Python 3.11.x

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar .env configurado
cat .env | grep GEMINI_API_KEY

# 5. Ejecutar servidor con hot-reload
uvicorn app.main:app --reload --port 8080 --host 0.0.0.0
```

**URLs**:
- API: http://localhost:8080
- Docs: http://localhost:8080/docs  
- Health: http://localhost:8080/api/v1/health

### Test Manual con curl

```bash
# Health check
curl http://localhost:8080/api/v1/health

# Chat query
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"¿Cuál es tu experiencia profesional?"}'
```

### Debugging de Vectores

```bash
# Ver contenido del vector store
./scripts/dev/query_vectors.sh

# Conectar directamente a Cloud SQL
source .env
PGPASSWORD="${CLOUD_SQL_PASSWORD}" psql \
  -h "${CLOUD_SQL_HOST}" \
  -U postgres \
  -d chatbot_db
```

## 📝 Endpoints de la API

### POST /api/v1/chat
Enviar mensaje al chatbot

**Request:**
```json
{
  "message": "¿Cuál es tu experiencia con Python?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "message": "Tengo más de 10 años de experiencia con Python...",
  "sources": [
    {
      "type": "experience",
      "content_preview": "Empresa: InAdvance...",
      "metadata": {...}
    }
  ],
  "session_id": "...",
  "timestamp": "2025-01-15T10:30:00",
  "model": "llama-3.1-70b"
}
```

### GET /api/v1/health
Health check del servicio

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00"
}
```

## 🧪 Testing

```bash
# Backend tests
pytest tests/

# Test manual del RAG
python -c "
from app.services.rag_service import RAGService
import asyncio

async def test():
    service = RAGService()
    result = await service.generate_response('¿Cuál es tu experiencia?')
    print(result)

asyncio.run(test())
"
```

## 🔒 Seguridad

- ✅ CORS configurado para dominios específicos
- ✅ Rate limiting en endpoints
- ✅ Validación de inputs con Pydantic
- ✅ Environment variables para secrets
- ✅ Usuario no-root en Docker
- ✅ Health checks configurados

## 📊 Monitoreo

### Cloud Run Logs
```bash
gcloud run services logs read chatbot-api --region europe-west1
```

### Métricas
- Visitar Google Cloud Console → Cloud Run → chatbot-api
- Ver requests, latencia, errores

## 🐛 Troubleshooting

### Error: No se puede conectar a Cloud SQL
```bash
# Verificar que la instance existe
gcloud sql instances list

# Verificar que pgvector está instalado
gcloud sql connect almapi-chatbot-db --user=postgres
# Luego: SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Error: Gemini API Key inválida
- Verificar que la key está en `.env`
- Obtener nueva key en https://aistudio.google.com/app/apikey

### Error: Embeddings de HuggingFace fallan
```bash
# Los embeddings son locales, verificar que el modelo se descargó
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Si falla, reinstalar
pip install --force-reinstall sentence-transformers
```

### Error: Docker build falla en Cloud Run
```bash
# Verificar permisos de Cloud Build
PROJECT_ID=$(gcloud config get-value project)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_ID}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Aumentar timeout si es necesario
gcloud builds submit --timeout=25m ...
```

## 🎨 Personalización

### Modificar el System Prompt
Editar `app/services/rag_service.py`:
```python
def _create_system_prompt(self) -> PromptTemplate:
    template = """Tu prompt personalizado aquí..."""
    ...
```

### Ajustar parámetros del RAG
Editar `app/core/config.py`:
```python
VECTOR_SEARCH_K: int = 3  # Número de chunks a recuperar
GEMINI_TEMPERATURE: float = 0.1  # Creatividad del LLM
```

### Actualizar Portfolio

```bash
# 1. Editar tu portfolio
nano data/portfolio.yaml

# 2. Re-indexar vectores
source venv/bin/activate
python scripts/setup/initialize_vector_store.py

# 3. Verificar vectores actualizados
./scripts/dev/query_vectors.sh

# 4. Re-deploy (si es necesario)
./scripts/deploy/deploy-cloud-run.sh
```

**Nota**: Si solo cambias el portfolio, el backend local con `--reload` detecta cambios automáticamente después de re-indexar.

## 📚 Tech Stack

### Backend & AI
- **Framework**: FastAPI 0.115+ (Python 3.11)
- **LLM**: Gemini 2.5 Flash (~1-2s respuesta)
- **Embeddings**: HuggingFace sentence-transformers (all-MiniLM-L6-v2, 384-dim, local)
- **Vector DB**: pgvector 0.5+ en PostgreSQL 15 (Cloud SQL)
- **RAG Framework**: LangChain 0.3+

### Infrastructure (GCP)
- **Compute**: Cloud Run (2GB RAM, 2 vCPUs, europe-west1)
- **Database**: Cloud SQL (PostgreSQL + pgvector, f1-micro)
- **Registry**: Artifact Registry (europe-west1)
- **Build**: Cloud Build

### Development
- **Containerization**: Docker (multi-stage build)
- **Testing**: pytest, test-local.html
- **Linting**: Ruff (opcional)
- **Docs**: Markdown (860+ líneas)

## 🤝 Contribuir

Contributions are welcome! Por favor:
1. Fork el repositorio
2. Crea una branch (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la branch (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 👤 Autor

**Álvaro Maldonado**
- Website: https://almapi.dev
- LinkedIn: https://linkedin.com/in/almapidev
- Email: readme.md@almapi.dev

## 📖 Documentación Adicional

- **Setup completo**: `scripts/setup/README.md`
- **Deploy a producción**: `scripts/deploy/README.md`
- **Desarrollo local**: `scripts/dev/README.md`
- **Variables de entorno**: `ENV_TEMPLATE.md`
- **Integración frontend**: Ver repo de tu portfolio

## 🎓 Aprendizajes y Decisiones Técnicas

### ¿Por qué HuggingFace en lugar de Vertex AI?
- ✅ **100% gratis** (local, sin APIs)
- ✅ **Más rápido** (sin llamadas de red)
- ✅ **Sin cuotas** ni límites
- ✅ **Mismo quality** para RAG (384 dims suficiente)

### ¿Por qué Llama 3.3 70B?
- ✅ **Más reciente** que 3.1
- ✅ **Mejor performance** en tareas conversacionales
- ✅ **Igualmente gratis** con Gemini API
- ✅ **~1000 tokens/s** (ultra rápido)

### ¿Por qué europe-west1?
- ✅ **Latencia óptima** para Europa
- ✅ **Cumplimiento GDPR** (datos en EU)
- ✅ **Mismo precio** que otras regiones

## ⚡ Performance

```
Latencia típica: ~1.5-2 segundos (end-to-end)
  - Embedding query: ~50ms (local)
  - Vector search: ~20ms (pgvector)
  - LLM generation: ~1-2s (Gemini)
  - Total: ~1.5-2s ✅

Throughput: 30-50 requests/minuto
Vector store: 70 chunks, 384-dim embeddings
```

## 🙏 Agradecimientos

- [Gemini](https://aistudio.google.com) - LLM gratuito con Google Workspace
- [HuggingFace](https://huggingface.co) - Embeddings locales open-source
- [Google Cloud](https://cloud.google.com) - Free tiers generosos
- [LangChain](https://langchain.com) - Framework RAG moderno
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search en PostgreSQL

## 🔒 Seguridad

Este repositorio ha sido auditado y no contiene:
- ❌ API keys hardcodeadas
- ❌ Passwords expuestas
- ❌ IPs privadas
- ❌ Tokens de sesión
- ✅ Todas las credenciales en `.env` (gitignored)

---

**Made with ❤️ using AI, Open Source & 100% Free Tier**
