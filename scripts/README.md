# Scripts del Proyecto AI Resume Agent

Este directorio contiene los scripts esenciales del proyecto organizados por categoría.

## 📁 Estructura

```
scripts/
├── test/           # Scripts de testing
├── setup/          # Scripts de configuración y vectorización
```

## 🧪 Testing (`scripts/test/`)

Scripts para probar el sistema:

- **`test_comprehensive.py`**: Testing completo con 30 preguntas distribuidas en múltiples categorías (identidad, experiencia, comportamiento, educación, condiciones profesionales, off-topic, seguridad, multilingüe). Genera reporte detallado en markdown con contexto recuperado, vectores y veredicto por cada test.

**Uso:**
```bash
# Ejecutar desde la raíz del proyecto
python scripts/test/test_comprehensive.py
# Genera reporte en: output/test_results_YYYYMMDD_HHMMSS.md
```

## ⚙️ Setup (`scripts/setup/`)

Scripts para configuración inicial y vectorización:

- **`build_knowledge_base.py`**: Procesa `data/portfolio.yaml` y genera chunks semánticos ricos con estrategia "Q&A Fused Chunking". Incluye FAQs relevantes en cada chunk.
- **`initialize_vector_store.py`**: Inicializa el vector store (PGVector) con los chunks generados. Elimina vectores antiguos antes de añadir nuevos.
- **`setup-gcp.sh`**: Script de configuración inicial de GCP (opcional).
- **`start-local.sh`**: Inicia el servidor FastAPI local para desarrollo.

**Uso:**
```bash
# 1. Construir knowledge base (procesa portfolio.yaml)
python scripts/setup/build_knowledge_base.py

# 2. Inicializar vector store (guarda chunks en PGVector)
python scripts/setup/initialize_vector_store.py

# 3. Iniciar servidor local (opcional)
bash scripts/setup/start-local.sh

# 4. Setup GCP (solo primera vez)
bash scripts/setup/setup-gcp.sh
```

## 📝 Flujo de Trabajo

1. **Modificar knowledge base**: Edita `data/portfolio.yaml`
2. **Regenerar chunks**: `python scripts/setup/build_knowledge_base.py`
3. **Actualizar vector store**: `python scripts/setup/initialize_vector_store.py`
4. **Probar cambios**: `python scripts/test/test_comprehensive.py`
5. **Desplegar**: Push a `main` triggera Cloud Build automático

## 🔧 Notas

- Todos los scripts deben ejecutarse desde la raíz del proyecto.
- Las variables de entorno se cargan automáticamente desde `.env`.
- El deployment en Cloud Run es automático via Cloud Build (ver `cloudbuild.yaml`).
- Los tests de producción se deben ejecutar manualmente contra la URL desplegada.

