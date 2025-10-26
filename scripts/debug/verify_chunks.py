#!/usr/bin/env python3
"""
🔍 VERIFICACIÓN DE CHUNKS - Vector Store
Script para verificar qué chunks están disponibles en el vector store
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

async def verify_chunks():
    """Verificar qué chunks están disponibles"""
    print("🔍 VERIFICACIÓN DE CHUNKS EN VECTOR STORE")
    print("=" * 60)
    
    try:
        # Inicializar RAG Service
        print("🔄 Inicializando RAG Service...")
        rag_service = RAGService()
        print("✅ RAG Service inicializado")
        
        # Lista de preguntas para verificar diferentes categorías
        test_questions = [
            ("¿Cuál es tu formación académica?", "education"),
            ("¿Qué idiomas manejas?", "languages"),
            ("¿Cuál es tu motivación profesional?", "philosophy_and_interests"),
            ("¿Qué proyectos de IA has liderado?", "projects"),
            ("¿Cuáles son tus expectativas salariales?", "professional_conditions"),
            ("¿Cuál es tu experiencia con Java?", "skills_showcase"),
            ("¿Quién eres?", "personal_info"),
        ]
        
        print(f"\n🧪 Verificando {len(test_questions)} categorías...")
        
        for question, expected_category in test_questions:
            print(f"\n📋 Pregunta: '{question}'")
            print(f"🎯 Categoría esperada: {expected_category}")
            
            # Obtener contexto relevante
            retriever = rag_service.vector_store.as_retriever(
                search_kwargs={"k": 5}
            )
            docs = retriever.get_relevant_documents(question)
            
            print(f"📚 Chunks encontrados: {len(docs)}")
            
            if docs:
                for i, doc in enumerate(docs[:3]):  # Mostrar solo los primeros 3
                    source = doc.metadata.get("source", "unknown")
                    preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    print(f"   {i+1}. Source: {source}")
                    print(f"      Preview: {preview}")
            else:
                print("   ❌ No se encontraron chunks")
            
            print("-" * 40)
        
        print("\n✅ Verificación completada")
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_chunks())
