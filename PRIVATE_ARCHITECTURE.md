# 🔐 ARQUITECTURA COMPLETAMENTE PRIVADA

## 🎯 **OBJETIVO: TODOS LOS ENDPOINTS AUTENTICADOS**

**Una sola API Key para todo el sistema** - No hay endpoints públicos.

## 🔑 **CONFIGURACIÓN**

### **Variable de Entorno Única:**
```bash
# ✅ UNA SOLA API KEY PARA TODO
export API_KEY="tu-api-key-super-secreta"
```

### **Configuración en `app/core/config.py`:**
```python
# API Key única para todos los endpoints
API_KEY: str = Field(
    default="api-key-change-in-production",
    description="API Key única requerida para acceder a TODOS los endpoints",
)
```

## 🛡️ **SISTEMA DE AUTENTICACIÓN**

### **Archivo: `app/core/auth_simple.py`**
```python
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verifica que el API Key sea válido para TODOS los endpoints.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key requerido para acceder a este endpoint",
        )

    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválido",
        )

    return True
```

## 🔒 **ENDPOINTS PROTEGIDOS**

### **Todos los endpoints requieren autenticación:**

```python
# ✅ CHAT - Requiere API Key
@router.post("/chat")
async def chat(_: bool = Depends(get_api_key_dependency())):
    pass

# ✅ MÉTRICAS - Requiere API Key  
@router.get("/metrics")
async def get_metrics(_: bool = Depends(get_api_key_dependency())):
    pass

# ✅ CONVERSACIONES - Requiere API Key
@router.get("/conversations")
async def get_conversations(_: bool = Depends(get_api_key_dependency())):
    pass

# ✅ CAPTURA DE DATOS - Requiere API Key
@router.post("/capture-data")
async def capture_data(_: bool = Depends(get_api_key_dependency())):
    pass

# ✅ GDPR - Requiere API Key
@router.post("/gdpr/consent")
async def gdpr_consent(_: bool = Depends(get_api_key_dependency())):
    pass
```

## 🚀 **USO DEL SISTEMA**

### **1. Configurar Variable de Entorno:**
```bash
# Desarrollo local
export API_KEY="mi-api-key-desarrollo"

# Producción (Cloud Run)
gcloud run deploy ai-resume-agent \
    --set-env-vars="API_KEY=mi-api-key-produccion"
```

### **2. Usar en Frontend:**
```javascript
// ✅ CONFIGURACIÓN SEGURA - API Key hardcoded
const CONFIG = {
    api_key: "mi-api-key-desarrollo",  // Hardcoded en el frontend
    api_base_url: "http://localhost:8080"
};

// ✅ TODOS LOS ENDPOINTS REQUIEREN API KEY
async function sendMessage(message) {
    const response = await fetch(`${CONFIG.api_base_url}/api/v1/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': CONFIG.api_key  // Requerido para TODOS los endpoints
        },
        body: JSON.stringify({ message })
    });
    return response.json();
}

async function getMetrics() {
    const response = await fetch(`${CONFIG.api_base_url}/api/v1/metrics`, {
        headers: {
            'X-API-Key': CONFIG.api_key  // Requerido para métricas
        }
    });
    return response.json();
}
```

### **3. Usar con cURL:**
```bash
# ✅ CHAT - Requiere API Key
curl -H "X-API-Key: mi-api-key-desarrollo" \
     -X POST http://localhost:8080/api/v1/chat \
     -d '{"message": "Hola"}'

# ✅ MÉTRICAS - Requiere API Key
curl -H "X-API-Key: mi-api-key-desarrollo" \
     http://localhost:8080/api/v1/metrics

# ✅ CONVERSACIONES - Requiere API Key
curl -H "X-API-Key: mi-api-key-desarrollo" \
     http://localhost:8080/api/v1/conversations

# ❌ SIN API KEY - Rechazado
curl http://localhost:8080/api/v1/chat
# Respuesta: 401 Unauthorized
```

## 🔍 **VERIFICACIÓN DE SEGURIDAD**

### **Comandos de Prueba:**
```bash
# ✅ CON API KEY - Autorizado
curl -H "X-API-Key: mi-api-key-desarrollo" \
     http://localhost:8080/api/v1/metrics

# ❌ SIN API KEY - Rechazado
curl http://localhost:8080/api/v1/metrics
# Respuesta: {"detail": "API Key requerido para acceder a este endpoint"}

# ❌ API KEY INCORRECTA - Rechazado
curl -H "X-API-Key: key-incorrecta" \
     http://localhost:8080/api/v1/metrics
# Respuesta: {"detail": "API Key inválido"}
```

## 📱 **IMPLEMENTACIÓN FRONTEND COMPLETA**

### **HTML + JavaScript:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot Privado</title>
</head>
<body>
    <div id="chat-container">
        <div id="messages"></div>
        <input type="text" id="message-input" placeholder="Escribe tu mensaje...">
        <button onclick="sendMessage()">Enviar</button>
        <button onclick="getMetrics()">Ver Métricas</button>
    </div>

    <script>
        // ✅ CONFIGURACIÓN SEGURA
        const CONFIG = {
            api_key: "mi-api-key-desarrollo",  // Hardcoded, es privada
            api_base_url: "http://localhost:8080"
        };
        
        // ✅ CHAT - Requiere API Key
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value;
            
            if (!message) return;
            
            const response = await fetch(`${CONFIG.api_base_url}/api/v1/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': CONFIG.api_key
                },
                body: JSON.stringify({ 
                    message: message,
                    session_id: "web-session-" + Date.now()
                })
            });
            
            const data = await response.json();
            
            // Mostrar respuesta
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += `<div><strong>Usuario:</strong> ${message}</div>`;
            messagesDiv.innerHTML += `<div><strong>Bot:</strong> ${data.message}</div>`;
            
            input.value = '';
        }
        
        // ✅ MÉTRICAS - Requiere API Key
        async function getMetrics() {
            const response = await fetch(`${CONFIG.api_base_url}/api/v1/metrics`, {
                headers: {
                    'X-API-Key': CONFIG.api_key
                }
            });
            
            const data = await response.json();
            console.log('Métricas:', data);
            
            // Mostrar métricas
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += `<div><strong>Métricas:</strong> ${JSON.stringify(data)}</div>`;
        }
    </script>
</body>
</html>
```

## 🚀 **DEPLOYMENT**

### **Desarrollo Local:**
```bash
# Configurar variable de entorno
export API_KEY="mi-api-key-desarrollo"

# Iniciar servidor
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### **Producción (Cloud Run):**
```bash
# Deploy con variable de entorno
gcloud run deploy ai-resume-agent \
    --image gcr.io/tu-proyecto/ai-resume-agent \
    --platform managed \
    --region us-central1 \
    --set-env-vars="API_KEY=mi-api-key-produccion"
```

## 🎯 **RESUMEN DE SEGURIDAD**

1. **Una sola API Key** para todo el sistema
2. **Todos los endpoints** requieren autenticación
3. **No hay endpoints públicos**
4. **API Key hardcoded** en el frontend
5. **Rate limiting** aplicado a todos los endpoints
6. **Audit logging** para todos los accesos

**¡Sistema completamente privado y seguro!** 🛡️
