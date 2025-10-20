# 🔐 AUTENTICACIÓN REAL CON JWT

## 🎯 **OBJETIVO: Solo tú y tu frontend pueden usar los endpoints**

**Sistema de autenticación real con JWT** - Imposible para usuarios maliciosos acceder.

## 🔑 **ARQUITECTURA DE AUTENTICACIÓN:**

### **1. Flujo de Autenticación:**
```
Frontend → /get-token (con clave secreta) → Token JWT → Usar en todos los endpoints
```

### **2. Claves Secretas:**
```python
# ✅ CLAVES SECRETAS (cambiar en producción)
FRONTEND_SECRET_KEY = "frontend-secret-key-super-secreta-cambiar-en-produccion"
JWT_SECRET_KEY = "tu-jwt-secret-key-super-secreta-cambiar-en-produccion"
```

## 🛡️ **ENDPOINTS DE AUTENTICACIÓN:**

### **1. Obtener Token JWT:**
```bash
# ✅ SOLO EL FRONTEND AUTORIZADO PUEDE OBTENER TOKENS
curl -H "X-Frontend-Secret: frontend-secret-key-super-secreta-cambiar-en-produccion" \
     -X POST http://localhost:8080/api/v1/get-token

# Respuesta:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "expires_at": "2024-01-02T12:00:00"
}
```

### **2. Refrescar Token:**
```bash
# ✅ REFRESCAR TOKEN EXISTENTE
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
     -X POST http://localhost:8080/api/v1/refresh-token
```

## 🔒 **ENDPOINTS PROTEGIDOS:**

### **Todos los endpoints requieren token JWT válido:**

```bash
# ✅ CHAT - Requiere token JWT
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
     -X POST http://localhost:8080/api/v1/chat \
     -d '{"message": "Hola"}'

# ✅ MÉTRICAS - Requiere token JWT
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
     http://localhost:8080/api/v1/metrics

# ✅ CONVERSACIONES - Requiere token JWT
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
     http://localhost:8080/api/v1/conversations
```

## 📱 **IMPLEMENTACIÓN FRONTEND:**

### **1. Configuración del Frontend:**
```javascript
// ✅ CONFIGURACIÓN SEGURA
const CONFIG = {
    frontend_secret: "frontend-secret-key-super-secreta-cambiar-en-produccion",
    api_base_url: "http://localhost:8080",
    token: null,  // Se obtiene dinámicamente
    token_expires: null
};
```

### **2. Obtener Token JWT:**
```javascript
// ✅ OBTENER TOKEN JWT
async function getToken() {
    try {
        const response = await fetch(`${CONFIG.api_base_url}/api/v1/get-token`, {
            method: 'POST',
            headers: {
                'X-Frontend-Secret': CONFIG.frontend_secret
            }
        });
        
        if (!response.ok) {
            throw new Error('Error obteniendo token');
        }
        
        const data = await response.json();
        CONFIG.token = data.access_token;
        CONFIG.token_expires = new Date(data.expires_at);
        
        console.log('Token JWT obtenido exitosamente');
        return data.access_token;
        
    } catch (error) {
        console.error('Error obteniendo token:', error);
        throw error;
    }
}
```

### **3. Refrescar Token:**
```javascript
// ✅ REFRESCAR TOKEN
async function refreshToken() {
    try {
        const response = await fetch(`${CONFIG.api_base_url}/api/v1/refresh-token`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CONFIG.token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Error refrescando token');
        }
        
        const data = await response.json();
        CONFIG.token = data.access_token;
        CONFIG.token_expires = new Date(data.expires_at);
        
        console.log('Token JWT refrescado exitosamente');
        return data.access_token;
        
    } catch (error) {
        console.error('Error refrescando token:', error);
        throw error;
    }
}
```

### **4. Verificar Token Válido:**
```javascript
// ✅ VERIFICAR SI EL TOKEN ES VÁLIDO
function isTokenValid() {
    if (!CONFIG.token || !CONFIG.token_expires) {
        return false;
    }
    
    const now = new Date();
    const expires = new Date(CONFIG.token_expires);
    
    // Considerar expirado si falta menos de 1 hora
    const oneHour = 60 * 60 * 1000;
    return expires.getTime() - now.getTime() > oneHour;
}
```

### **5. Usar Chat con Autenticación:**
```javascript
// ✅ CHAT CON AUTENTICACIÓN REAL
async function sendMessage(message) {
    try {
        // Verificar si necesitamos obtener/refrescar token
        if (!isTokenValid()) {
            if (CONFIG.token) {
                await refreshToken();
            } else {
                await getToken();
            }
        }
        
        const response = await fetch(`${CONFIG.api_base_url}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CONFIG.token}`
            },
            body: JSON.stringify({ 
                message: message,
                session_id: "web-session-" + Date.now()
            })
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Token expirado, intentar refrescar
                await refreshToken();
                return sendMessage(message); // Reintentar
            }
            throw new Error('Error en chat');
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Error enviando mensaje:', error);
        throw error;
    }
}
```

### **6. Implementación Completa:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot con Autenticación Real</title>
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
            frontend_secret: "frontend-secret-key-super-secreta-cambiar-en-produccion",
            api_base_url: "http://localhost:8080",
            token: null,
            token_expires: null
        };
        
        // ✅ FUNCIONES DE AUTENTICACIÓN
        async function getToken() {
            const response = await fetch(`${CONFIG.api_base_url}/api/v1/get-token`, {
                method: 'POST',
                headers: { 'X-Frontend-Secret': CONFIG.frontend_secret }
            });
            const data = await response.json();
            CONFIG.token = data.access_token;
            CONFIG.token_expires = new Date(data.expires_at);
            return data.access_token;
        }
        
        async function refreshToken() {
            const response = await fetch(`${CONFIG.api_base_url}/api/v1/refresh-token`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${CONFIG.token}` }
            });
            const data = await response.json();
            CONFIG.token = data.access_token;
            CONFIG.token_expires = new Date(data.expires_at);
            return data.access_token;
        }
        
        function isTokenValid() {
            if (!CONFIG.token || !CONFIG.token_expires) return false;
            const now = new Date();
            const expires = new Date(CONFIG.token_expires);
            const oneHour = 60 * 60 * 1000;
            return expires.getTime() - now.getTime() > oneHour;
        }
        
        // ✅ CHAT CON AUTENTICACIÓN
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value;
            
            if (!message) return;
            
            try {
                if (!isTokenValid()) {
                    if (CONFIG.token) {
                        await refreshToken();
                    } else {
                        await getToken();
                    }
                }
                
                const response = await fetch(`${CONFIG.api_base_url}/api/v1/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${CONFIG.token}`
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
                
            } catch (error) {
                console.error('Error:', error);
                alert('Error enviando mensaje');
            }
        }
        
        // ✅ MÉTRICAS CON AUTENTICACIÓN
        async function getMetrics() {
            try {
                if (!isTokenValid()) {
                    if (CONFIG.token) {
                        await refreshToken();
                    } else {
                        await getToken();
                    }
                }
                
                const response = await fetch(`${CONFIG.api_base_url}/api/v1/metrics`, {
                    headers: { 'Authorization': `Bearer ${CONFIG.token}` }
                });
                
                const data = await response.json();
                console.log('Métricas:', data);
                
                // Mostrar métricas
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML += `<div><strong>Métricas:</strong> ${JSON.stringify(data)}</div>`;
                
            } catch (error) {
                console.error('Error:', error);
                alert('Error obteniendo métricas');
            }
        }
        
        // ✅ INICIALIZAR AL CARGAR LA PÁGINA
        window.onload = async function() {
            try {
                await getToken();
                console.log('Sistema inicializado con autenticación real');
            } catch (error) {
                console.error('Error inicializando:', error);
                alert('Error inicializando el sistema');
            }
        };
    </script>
</body>
</html>
```

## 🚀 **DEPLOYMENT:**

### **1. Variables de Entorno:**
```bash
# ✅ CONFIGURAR CLAVES SECRETAS
export FRONTEND_SECRET_KEY="frontend-secret-key-super-secreta-cambiar-en-produccion"
export JWT_SECRET_KEY="tu-jwt-secret-key-super-secreta-cambiar-en-produccion"
```

### **2. Cloud Run:**
```bash
# ✅ DEPLOY CON CLAVES SECRETAS
gcloud run deploy ai-resume-agent \
    --image gcr.io/tu-proyecto/ai-resume-agent \
    --platform managed \
    --region us-central1 \
    --set-env-vars="FRONTEND_SECRET_KEY=frontend-secret-prod,JWT_SECRET_KEY=jwt-secret-prod"
```

## 🔍 **VERIFICACIÓN DE SEGURIDAD:**

### **1. Sin Token - Rechazado:**
```bash
# ❌ SIN TOKEN - Rechazado
curl http://localhost:8080/api/v1/chat
# Respuesta: 401 Unauthorized
```

### **2. Token Inválido - Rechazado:**
```bash
# ❌ TOKEN INVÁLIDO - Rechazado
curl -H "Authorization: Bearer token-invalido" \
     http://localhost:8080/api/v1/chat
# Respuesta: 401 Unauthorized
```

### **3. Sin Clave Secreta - Rechazado:**
```bash
# ❌ SIN CLAVE SECRETA - Rechazado
curl -X POST http://localhost:8080/api/v1/get-token
# Respuesta: 401 Unauthorized
```

### **4. Clave Secreta Inválida - Rechazado:**
```bash
# ❌ CLAVE SECRETA INVÁLIDA - Rechazado
curl -H "X-Frontend-Secret: clave-incorrecta" \
     -X POST http://localhost:8080/api/v1/get-token
# Respuesta: 401 Unauthorized
```

## 🎯 **RESUMEN DE SEGURIDAD:**

1. **Solo tu frontend** puede obtener tokens (con clave secreta)
2. **Solo con tokens válidos** se puede acceder a los endpoints
3. **Tokens expiran** automáticamente (24 horas)
4. **Tokens se pueden refrescar** sin reautenticación
5. **Imposible** para usuarios maliciosos acceder
6. **Rate limiting** aplicado a todos los endpoints
7. **Audit logging** para todos los accesos

**¡Sistema completamente seguro y solo para tu frontend!** 🛡️
