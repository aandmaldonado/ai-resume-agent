# Dockerfile optimizado para Cloud Run
FROM python:3.11-slim

# Metadata
LABEL maintainer="readme.md@almapi.dev"
LABEL description="AI Resume Agent - RAG Chatbot"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .

# Instalar PyTorch CPU-only primero (mucho más ligero que CUDA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Instalar resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación y scripts
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# CRÍTICO: Descargar modelo como appuser (después de cambiar de usuario)
# Esto descarga el modelo en el cache del usuario correcto (~90MB)
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print(f'✓ Modelo descargado: {model}')"

# CRÍTICO: Inicializar vector store con chunks enriquecidos
# Esto asegura que el vector store esté actualizado con los nuevos chunks
RUN python scripts/setup/initialize_vector_store.py

# Cloud Run usa la variable PORT
ENV PORT=8080
EXPOSE 8080

# Comando para iniciar la aplicación
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1

