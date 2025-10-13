# 🔐 Configuración de Variables de Entorno

## Archivo `.env`

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```bash
# === GCP Configuration ===
GCP_PROJECT_ID=tu-proyecto-gcp
CLOUD_SQL_CONNECTION_NAME=proyecto:region:instancia
CLOUD_SQL_HOST=tu.ip.cloud.sql
CLOUD_SQL_PASSWORD=tu_password_segura_aqui

# === Groq API ===
# Obtén tu API key gratis en: https://console.groq.com/keys
GROQ_API_KEY=gsk_...tu_api_key_aqui...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=500

# === Database ===
DATABASE_NAME=chatbot_db
DATABASE_USER=postgres
VECTOR_COLLECTION_NAME=resume_vectors

# === Application ===
ENVIRONMENT=development
LOG_LEVEL=INFO

# === CORS (para desarrollo local) ===
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Cómo Obtener los Valores:

### 1. GCP_PROJECT_ID
```bash
gcloud config get-value project
```

### 2. CLOUD_SQL_HOST
```bash
gcloud sql instances describe NOMBRE_INSTANCIA \
  --format="value(ipAddresses[0].ipAddress)"
```

### 3. CLOUD_SQL_PASSWORD
Configúrala al crear la instancia o cámbiala:
```bash
gcloud sql users set-password postgres \
  --instance=NOMBRE_INSTANCIA \
  --password=TU_PASSWORD_SEGURA
```

### 4. GROQ_API_KEY
1. Ve a: https://console.groq.com/keys
2. Crea una cuenta gratis
3. Genera una API key

---

**⚠️ IMPORTANTE**: Nunca commitees el archivo `.env` a git. Ya está en `.gitignore`.
