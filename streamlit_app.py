import streamlit as st
import asyncio
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar página
st.set_page_config(
    page_title="AI Resume Agent - Local Simulator",
    page_icon="🤖",
    layout="centered"
)

# Título y descripción
st.title("🤖 AI Resume Agent")
st.markdown("""
Simulador local del chatbot para portfolio profesional.
Este entorno conecta directamente con el servicio RAG usando la configuración local.
""")

# Sidebar con configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Mostrar configuración actual
    llm_provider = os.getenv("LLM_PROVIDER", "gemini")
    st.info(f"**LLM Provider:** {llm_provider}")
    
    if llm_provider == "ollama":
        st.text(f"Model: {os.getenv('OLLAMA_MODEL', 'llama3')}")
        st.text(f"URL: {os.getenv('OLLAMA_BASE_URL')}")
    else:
        st.text(f"Model: {os.getenv('GEMINI_MODEL')}")
    
    st.divider()
    
    # Botón para limpiar historial
    if st.button("Limpiar Conversación"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

# Inicializar estado de sesión
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = f"local-{uuid.uuid4()}"

# Inicializar servicio RAG (solo una vez)
@st.cache_resource
def get_rag_service():
    from app.services.rag_service import RAGService
    return RAGService()

try:
    rag_service = get_rag_service()
except Exception as e:
    st.error(f"Error inicializando RAG Service: {e}")
    st.stop()

# Mostrar historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Fuentes consultadas"):
                for source in message["sources"]:
                    st.markdown(f"**{source['type']}**: {source['content_preview']}")

# Input de usuario
if prompt := st.chat_input("Pregunta sobre mi experiencia..."):
    # Agregar mensaje de usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # Ejecutar asíncronamente
                response_data = asyncio.run(
                    rag_service.generate_response(
                        question=prompt,
                        session_id=st.session_state.session_id
                    )
                )
                
                response_text = response_data["response"]
                sources = response_data.get("sources", [])
                
                st.markdown(response_text)
                
                if sources:
                    with st.expander("📚 Fuentes consultadas"):
                        for source in sources:
                            st.markdown(f"**{source['type']}**: {source['content_preview']}")
                
                # Guardar en historial
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "sources": sources
                })
                
            except Exception as e:
                st.error(f"Error generando respuesta: {e}")
