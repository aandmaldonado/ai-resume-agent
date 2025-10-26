#!/usr/bin/env python3
"""
🔍 DEBUG ESPECÍFICO - Verificar recuperación de chunks
Script para debuggear por qué no se recuperan chunks en el testing
"""

import asyncio
import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno desde archivo .env
from dotenv import load_dotenv
load_dotenv()

from app.services.rag_service import RAGService
from app.core.config import settings

async def debug_chunk_retrieval():
    """Debuggear la recuperación de chunks"""
    print("🔍 DEBUG ESPECÍFICO - RECUPERACIÓN DE CHUNKS")
    print("=" * 60)
    
    try:
        # Inicializar RAG Service
        print("🔄 Inicializando RAG Service...")
        rag_service = RAGService()
        print("✅ RAG Service inicializado")
        
        # Pregunta específica que sabemos que tiene chunks
        question = "¿Cuál fue el logro más significativo en AcuaMattic?"
        
        print(f"\n📋 Pregunta: '{question}'")
        
        # Paso 1: Verificar configuración
        print(f"\n🔧 CONFIGURACIÓN:")
        print(f"   VECTOR_SEARCH_K: {settings.VECTOR_SEARCH_K}")
        print(f"   VECTOR_COLLECTION_NAME: {settings.VECTOR_COLLECTION_NAME}")
        
        # Paso 2: Recuperación directa
        print(f"\n🔍 RECUPERACIÓN DIRECTA:")
        retriever = rag_service.vector_store.as_retriever(
            search_kwargs={"k": settings.VECTOR_SEARCH_K}
        )
        
        docs = retriever.get_relevant_documents(question)
        print(f"   Chunks encontrados: {len(docs)}")
        
        if docs:
            print(f"   ✅ Chunks recuperados correctamente")
            for i, doc in enumerate(docs[:3]):
                source = doc.metadata.get("source", "unknown")
                doc_id = doc.metadata.get("id", "unknown")
                preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                print(f"   {i+1}. Source: {source}, ID: {doc_id}")
                print(f"      Preview: {preview}")
        else:
            print(f"   ❌ No se encontraron chunks")
        
        # Paso 3: Verificar el método generate_response
        print(f"\n🧪 PROBANDO generate_response:")
        
        # Simular exactamente lo que hace generate_response
        expanded_question = question  # Sin expansión
        
        # Obtener contexto relevante del vector store
        docs_internal = retriever.get_relevant_documents(expanded_question)
        
        # Formatear contexto
        context = "\n\n".join([doc.page_content for doc in docs_internal])
        
        print(f"   Chunks internos: {len(docs_internal)}")
        print(f"   Contexto formateado: {len(context)} caracteres")
        
        if len(context) > 0:
            print(f"   ✅ Contexto disponible")
            print(f"   Preview contexto: {context[:200]}...")
        else:
            print(f"   ❌ Contexto vacío")
        
        # Paso 4: Verificar si hay problema con la memoria
        print(f"\n🧠 VERIFICANDO MEMORIA:")
        memory = rag_service._get_or_create_memory("test-debug")
        chat_history = memory.chat_memory.messages
        print(f"   Mensajes en memoria: {len(chat_history)}")
        
        # Paso 5: Probar generación completa
        print(f"\n🎯 PROBANDO GENERACIÓN COMPLETA:")
        try:
            result = await rag_service.generate_response(
                question=question,
                session_id="test-debug",
                user_type="IT"
            )
            
            response = result.get("response", "")
            sources_count = len(result.get("sources", []))
            
            print(f"   ✅ Generación exitosa")
            print(f"   Respuesta: {response[:100]}...")
            print(f"   Fuentes: {sources_count}")
            
        except Exception as e:
            print(f"   ❌ Error en generación: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ Debug completado")
        
    except Exception as e:
        print(f"❌ Error en debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_chunk_retrieval())
