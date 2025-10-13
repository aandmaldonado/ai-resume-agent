# 🧪 Guía de Testing - AI Resume Agent

## 📋 Estructura de Testing Organizada

Hemos reorganizado el framework de testing en una estructura clara y escalable:

```
tests/
├── conftest.py              # Configuración global de pytest
├── unit/                    # Tests unitarios
│   ├── test_health.py      # Tests de health checks
│   ├── test_chat.py        # Tests de endpoints de chat
│   └── test_basic_logic.py # Tests de lógica básica
├── integration/             # Tests de integración (futuro)
└── security/               # Tests de seguridad
    └── test_security.py    # Tests de seguridad OWASP LLM

scripts/
├── validate_basic.py       # Validación de estructura
├── run_tests.py           # Script completo de testing
└── setup.py               # Script de configuración inicial

test.py                    # Script principal de testing
```

## 🎯 **Cómo Ejecutar los Tests**

### **Opción 1: Script Principal (Recomendado)**

```bash
# Validación básica
python3 scripts/test.py validation

# Tests de lógica básica
python3 scripts/test.py logic

# Tests unitarios
python3 scripts/test.py unit

# Tests de seguridad
python3 scripts/test.py security

# Tests de integración
python3 scripts/test.py integration

# Todos los tests
python3 scripts/test.py all
```

### **Opción 2: Validación Rápida Manual**

```bash
# Validar estructura básica
python3 scripts/validate_basic.py

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