#!/usr/bin/env python3
"""
🔍 INVESTIGACIÓN NO INVASIVA - Contexto Específico
Script para investigar qué contexto se está pasando al LLM sin modificar nada
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

async def investigate_context():
    """Investigar el contexto específico que se pasa al LLM"""
    print("🔍 INVESTIGACIÓN NO INVASIVA - CONTEXTO ESPECÍFICO")
    print("=" * 60)
    print("⚠️ SOLO LECTURA - NO SE MODIFICA NADA")
    print("=" * 60)
    
    try:
        # Inicializar RAG Service
        print("🔄 Inicializando RAG Service...")
        rag_service = RAGService()
        print("✅ RAG Service inicializado")
        
        # Preguntas problemáticas que sabemos que fallan
        problem_questions = [
            "¿Qué proyectos de IA has liderado?",
            "¿Cuál fue el logro más significativo en AcuaMattic?",
            "¿Cuál es tu motivación para un nuevo reto profesional?",
            "¿Tienes certificación en AWS?",
        ]
        
        print(f"\n🧪 Investigando {len(problem_questions)} preguntas problemáticas...")
        
        for i, question in enumerate(problem_questions, 1):
            print(f"\n{'='*20} PREGUNTA {i}/{len(problem_questions)} {'='*20}")
            print(f"📋 Pregunta: '{question}'")
            
            # Obtener contexto relevante (igual que en el código real)
            retriever = rag_service.vector_store.as_retriever(
                search_kwargs={"k": settings.VECTOR_SEARCH_K}
            )
            docs = retriever.get_relevant_documents(question)
            
            # Formatear contexto (igual que en el código real)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            print(f"📚 Chunks encontrados: {len(docs)}")
            print(f"📝 Longitud del contexto: {len(context)} caracteres")
            
            # Mostrar distribución por source
            sources = {}
            for doc in docs:
                source = doc.metadata.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            print(f"📊 Distribución por source: {sources}")
            
            # Mostrar los primeros chunks para entender el contenido
            print(f"\n📄 CONTENIDO DEL CONTEXTO:")
            print("-" * 40)
            
            for j, doc in enumerate(docs[:3]):  # Mostrar solo los primeros 3
                source = doc.metadata.get("source", "unknown")
                doc_id = doc.metadata.get("id", "unknown")
                content = doc.page_content
                
                print(f"\nChunk {j+1}:")
                print(f"  Source: {source}")
                print(f"  ID: {doc_id}")
                print(f"  Longitud: {len(content)} caracteres")
                print(f"  Preview: {content[:200]}...")
                print("-" * 30)
            
            # Mostrar el contexto completo si es corto
            if len(context) < 1000:
                print(f"\n📄 CONTEXTO COMPLETO:")
                print("-" * 40)
                print(context)
                print("-" * 40)
            else:
                print(f"\n📄 CONTEXTO COMPLETO (primeros 500 caracteres):")
                print("-" * 40)
                print(context[:500] + "...")
                print("-" * 40)
            
            print(f"\n🔍 ANÁLISIS:")
            if len(docs) == 0:
                print("   ❌ PROBLEMA: No se encontraron chunks")
            elif len(context) < 100:
                print("   ⚠️ PROBLEMA: Contexto muy corto")
            else:
                print("   ✅ Contexto disponible - El problema puede estar en el prompt")
            
            print("\n" + "="*80)
        
        print("\n🎯 CONCLUSIONES:")
        print("1. Si hay chunks disponibles pero el LLM usa fallback → Problema en el prompt")
        print("2. Si no hay chunks disponibles → Problema en la recuperación")
        print("3. Si el contexto es muy corto → Problema en el tamaño de chunks")
        
        print("\n✅ Investigación completada - NO SE MODIFICÓ NADA")
        
    except Exception as e:
        print(f"❌ Error en investigación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_context())
