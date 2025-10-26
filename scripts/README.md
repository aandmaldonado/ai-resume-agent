# Scripts del Proyecto AI Resume Agent

Este directorio contiene todos los scripts organizados por categoría.

## 📁 Estructura

```
scripts/
├── test/           # Scripts de testing
├── debug/          # Scripts de debugging e investigación
├── monitoring/      # Scripts de monitoreo (por implementar)
├── deploy/         # Scripts de despliegue
├── dev/            # Scripts de desarrollo
└── setup/          # Scripts de configuración inicial
```

## 🧪 Testing (`scripts/test/`)

Scripts para probar el sistema localmente:

- **`test_comprehensive.py`**: Testing completo con 21 preguntas. Genera reporte en markdown con contexto, vectores y veredicto por cada test.
- **`test_config.py`**: Verificación de configuración y variables de entorno.
- **`test_server_local.sh`**: Test del servidor FastAPI local.
- **`setup_local_testing.sh`**: Configuración de variables de entorno para testing local.

**Uso:**
```bash
# Testing completo (genera reporte en output/test_results_YYYYMMDD.md)
python scripts/test/test_comprehensive.py

# Verificar configuración
python scripts/test/test_config.py

# Test servidor local
bash scripts/test/test_server_local.sh

# Configurar entorno local
bash scripts/test/setup_local_testing.sh
```

## 🐛 Debugging (`scripts/debug/`)

Scripts para investigar y debuggear el sistema:

- **`debug_chunks.py`**: Debug de chunks específicos.
- **`verify_chunks.py`**: Verificación de chunks en vector store.
- **`investigate_context.py`**: Investigación del contexto recuperado.
- **`investigate_projects.py`**: Investigación de chunks de proyectos.

**Uso:**
```bash
# Verificar chunks
python scripts/debug/verify_chunks.py

# Debug de chunks específicos
python scripts/debug/debug_chunks.py

# Investigar contexto
python scripts/debug/investigate_context.py
```

## 🚀 Deploy (`scripts/deploy/`)

Scripts para desplegar el sistema:

- **`update_vector_store.sh`**: Actualizar vector store en producción.

**Uso:**
```bash
bash scripts/deploy/update_vector_store.sh
```

## 👨‍💻 Dev (`scripts/dev/`)

Scripts para desarrollo:

- **`query_vectors.sh`**: Queryar vectores directamente.

**Uso:**
```bash
bash scripts/dev/query_vectors.sh
```

## ⚙️ Setup (`scripts/setup/`)

Scripts de configuración inicial:

- **`build_knowledge_base.py`**: Construir chunks del knowledge base.
- **`initialize_vector_store.py`**: Inicializar el vector store.
- **`setup-gcp.sh`**: Setup de GCP.
- **`start-local.sh`**: Iniciar entorno local.

**Uso:**
```bash
# Construir knowledge base
python scripts/setup/build_knowledge_base.py

# Inicializar vector store
python scripts/setup/initialize_vector_store.py

# Setup GCP
bash scripts/setup/setup-gcp.sh
```

## 📝 Notas

- Todos los scripts deben ejecutarse desde la raíz del proyecto.
- Los scripts de testing usan variables de entorno del archivo `.env`.
- Los scripts de deploy requieren autenticación con GCP.

