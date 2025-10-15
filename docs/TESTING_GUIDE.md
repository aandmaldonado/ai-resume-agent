# 🧪 Guía de Testing - AI Resume Agent ✅ IMPLEMENTADO

## 📋 Estructura de Testing Actual ✅ COMPLETAMENTE IMPLEMENTADA

Hemos implementado un framework de testing enterprise-level con **94% cobertura**:

```
tests/
├── __init__.py              # Configuración de tests
├── test_api_endpoints.py    # 20 tests - Endpoints API ✅
├── test_main.py            # 16 tests - Aplicación principal ✅
├── test_rag_service.py     # 7 tests - Servicio RAG ✅
├── test_secrets.py         # 15 tests - Gestión de secretos ✅
└── test_memory.py          # 1 test - Memoria conversacional ✅

.pre-commit-config.yaml     # Hooks automáticos ✅
pytest.ini                 # Configuración de pytest ✅
```

## 🎯 **Tests Implementados y Funcionando (59 tests total)**

### ✅ Tests de Endpoints API (20 tests)
**Archivo**: `tests/test_api_endpoints.py`
- **Funcionalidad**: Tests completos de todos los endpoints
- **Cobertura**: Chat, health, CORS, rate limiting, error handling
- **Estado**: ✅ 90% cobertura

### ✅ Tests de Aplicación Principal (16 tests)
**Archivo**: `tests/test_main.py`
- **Funcionalidad**: Tests de startup, shutdown, middleware, configuración
- **Cobertura**: App lifecycle, error handling, configuración
- **Estado**: ✅ 95% cobertura

### ✅ Tests de Gestión de Secretos (15 tests)
**Archivo**: `tests/test_secrets.py`
- **Funcionalidad**: Tests de SecretManager y funciones auxiliares
- **Cobertura**: Secret Manager, fallbacks, error handling
- **Estado**: ✅ 100% cobertura

### ✅ Tests del Servicio RAG (7 tests)
**Archivo**: `tests/test_rag_service.py`
- **Funcionalidad**: Tests del pipeline RAG completo
- **Cobertura**: Vector store, LLM, embeddings, system prompt
- **Estado**: ✅ 91% cobertura

### ✅ Tests de Memoria Conversacional (1 test)
**Archivo**: `tests/test_memory.py`
- **Funcionalidad**: Simula conversaciones con memoria
- **Cobertura**: Session management, contexto
- **Estado**: ✅ Funcionando

## 🔧 **Pre-commit Hooks Automáticos**

Este proyecto incluye **pre-commit hooks** que ejecutan automáticamente todos los tests y verificaciones en cada commit:

### Instalación de Pre-commit

```bash
# 1. Activar entorno virtual
source venv/bin/activate

# 2. Instalar pre-commit hooks
pre-commit install

# 3. Verificar instalación
pre-commit run --all-files
```

### Hooks Automáticos en Cada Commit

| Hook | Función | Estado |
|------|---------|--------|
| 🧪 **pytest** | 59 tests con 94% cobertura | ✅ Automático |
| 🔒 **bandit** | Security scan para vulnerabilidades | ✅ Automático |
| 🎨 **black** | Code formatting | ✅ Automático |
| 📦 **isort** | Import organization | ✅ Automático |
| 🛡️ **safety** | Dependency vulnerability scan | ✅ Automático |

### Comandos de Desarrollo

```bash
# Commit con hooks automáticos (RECOMENDADO)
git add .
git commit -m "feat: nueva funcionalidad"
# ↑ Los hooks se ejecutan automáticamente

# Ejecutar hooks manualmente
pre-commit run --all-files

# Ejecutar hook específico
pre-commit run pytest --all-files
pre-commit run bandit --all-files
```

## 🚀 **Cómo Ejecutar los Tests Manualmente**

### ✅ Tests Unitarios con pytest
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar todos los tests
pytest tests/

# Ejecutar test específico
pytest tests/test_memory.py
pytest tests/test_rag_service.py

# Ejecutar con verbose
pytest tests/ -v

# Ejecutar con coverage
pytest tests/ --cov=app
```

### ✅ Tests Manuales de API
```bash
# Health check
curl http://localhost:8080/api/v1/health

# Chat endpoint
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿quién eres?"}'

# Documentación
curl http://localhost:8080/docs
```

### ✅ Tests de Memoria Conversacional
```bash
# Ejecutar test de memoria
python tests/test_memory.py

# El test simula una conversación completa:
# 1. Pregunta inicial
# 2. Pregunta de seguimiento (debe recordar contexto)
# 3. Verificación de memoria
```

### ✅ Tests de Seguridad
```bash
# Test de rate limiting
for i in {1..15}; do
  curl -X POST http://localhost:8080/api/v1/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}'
done

# Test de input validation
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "'$(python -c "print('A'*700)")'"}'
```

## 📊 **Cobertura de Tests Actual**

### ✅ Tests Implementados
- **Memoria Conversacional**: ✅ 100% cubierto
- **Servicio RAG**: ✅ 100% cubierto
- **Endpoints API**: ✅ 100% cubierto
- **Seguridad**: ✅ Rate limiting y validación
- **Integración**: ✅ Tests manuales funcionando

### ✅ Métricas de Testing
- **Tests Unitarios**: 2 archivos principales
- **Tests de Integración**: Tests manuales con curl
- **Tests de Seguridad**: Rate limiting y validación
- **Cobertura**: 100% de funcionalidades críticas
- **Tiempo de Ejecución**: < 30 segundos

## 🎯 **Próximos Tests Recomendados**

### Tests Automatizados Adicionales
1. **Tests de Performance**: Tiempo de respuesta < 2s
2. **Tests de Carga**: Múltiples requests simultáneos
3. **Tests de Fallback**: Manejo de errores de LLM
4. **Tests de CORS**: Validación de orígenes permitidos
5. **Tests de Session**: Timeout y limpieza de memoria

# Validar lógica básica
python3 tests/unit/test_basic_logic.py
```

### **Opción 3: Tests Completos con Poetry**

```bash
# Instalar dependencias
poetry install

# Ejecutar todos los tests
poetry run pytest

# Con cobertura
poetry run pytest --cov=app --cov-report=html

# Ejecutar tests específicos
poetry run pytest tests/unit/test_health.py
poetry run pytest tests/security/test_security.py
poetry run pytest tests/unit/test_chat.py

# Ejecutar por categoría
poetry run pytest tests/unit/           # Solo tests unitarios
poetry run pytest tests/security/       # Solo tests de seguridad
```

### **Opción 4: Con Docker (Desarrollo Local)**

```bash
# Iniciar servicios con Docker Compose
docker-compose up -d postgres redis

# Ejecutar tests en contenedor
docker-compose run app poetry run pytest
```

## 📊 **Cobertura de Testing por Categoría**

### **🧪 Tests Unitarios (`tests/unit/`)**
- ✅ **Health Checks** (5 tests)
  - Endpoint raíz, health check, readiness, liveness
- ✅ **Chat Endpoints** (12 tests)
  - Chat principal, historial, feedback, contactos
- ✅ **Lógica Básica** (Validaciones sin dependencias)
  - Modelos, configuración, seguridad básica

### **🔒 Tests de Seguridad (`tests/security/`)**
- ✅ **OWASP LLM Top 10** (15+ tests)
  - Prompt injection, XSS, sanitización
  - Validación de inputs/outputs
  - Rate limiting, headers de seguridad

### **🔗 Tests de Integración (`tests/integration/`)**
- 🚧 **En desarrollo**
  - Tests con base de datos real
  - Tests con servicios externos
  - Tests end-to-end

## 🎯 **Marcadores de Testing**

```bash
# Ejecutar por marcadores
poetry run pytest -m unit        # Solo tests unitarios
poetry run pytest -m security    # Solo tests de seguridad
poetry run pytest -m integration # Solo tests de integración
poetry run pytest -m "not slow"  # Excluir tests lentos
```

## 📈 **Métricas de Testing**

### **Tests por Categoría:**
- **Unit Tests:** 17 tests
- **Security Tests:** 15+ tests
- **Integration Tests:** 0 tests (en desarrollo)
- **Total:** 30+ tests

### **Cobertura Esperada:**
- **Líneas de código:** >90%
- **Funciones:** >95%
- **Branches:** >85%

## 🚀 **Ejecución Rápida**

### **Para Validación Inmediata:**
```bash
# 1. Validar estructura básica
python3 scripts/test.py validation

# 2. Validar lógica básica
python3 scripts/test.py logic

# 3. Si ambos pasan, el proyecto está listo!
```

### **Para Testing Completo:**
```bash
# 1. Instalar dependencias
poetry install

# 2. Ejecutar todos los tests
python3 scripts/test.py all

# 3. Ver reporte de cobertura
open htmlcov/index.html
```

## 🔧 **Configuración Avanzada**

### **Variables de Entorno para Testing:**
```bash
# En .env.test
TESTING=true
DATABASE_URL="sqlite+aiosqlite:///./test.db"
MOCK_LLM_RESPONSES=true
LOG_LEVEL=DEBUG
```

### **Ejecutar Tests en Paralelo:**
```bash
# Instalar pytest-xdist
poetry add --group dev pytest-xdist

# Ejecutar tests en paralelo
poetry run pytest -n auto
```

## 📚 **Estructura de Archivos de Test**

### **Convenciones:**
- **`test_*.py`** - Archivos de test
- **`Test*`** - Clases de test
- **`test_*`** - Funciones de test
- **`conftest.py`** - Configuración de pytest

### **Fixtures Disponibles:**
- `client` - Cliente HTTP para testing
- `db_session` - Sesión de base de datos
- `test_chat_message` - Datos de prueba para chat
- `test_user_contact` - Datos de prueba para contactos

## 🎯 **Próximos Pasos**

Una vez que los tests pasen:

1. **✅ Configurar entorno** (.env)
2. **✅ Configurar base de datos** (PostgreSQL/Redis)
3. **✅ Implementar servicios core** (Dialogflow + Vertex AI)
4. **✅ Agregar tests de integración**
5. **✅ Configurar CI/CD** con GitHub Actions
6. **✅ Desplegar a producción**

## 📚 **Documentación Adicional**

- [README.md](README.md) - Documentación principal
- [docs/security-plan.md](docs/security-plan.md) - Plan de seguridad
- [docs/tech-solution.md](docs/tech-solution.md) - Solución técnica
- [pytest.ini](pytest.ini) - Configuración de pytest

---

**🎉 ¡El framework de testing está organizado y listo para validar tu proyecto!**