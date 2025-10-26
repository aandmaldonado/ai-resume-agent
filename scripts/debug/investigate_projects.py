#!/usr/bin/env python3
"""
🔍 INVESTIGACIÓN ESPECÍFICA - Chunks de Proyectos
Script para investigar por qué los chunks de proyectos no se recuperan
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

async def investigate_projects():
    """Investigar específicamente los chunks de proyectos"""
    print("🔍 INVESTIGACIÓN ESPECÍFICA - CHUNKS DE PROYECTOS")
    print("=" * 60)
    
    try:
        # Inicializar RAG Service
        print("🔄 Inicializando RAG Service...")
        rag_service = RAGService()
        print("✅ RAG Service inicializado")
        
        # Preguntas específicas sobre proyectos
        project_questions = [
            "¿Qué proyectos de IA has liderado?",
            "AcuaMattic",
            "proyectos de inteligencia artificial",
            "¿Cuál fue el logro más significativo en AcuaMattic?",
            "proyectos",
            "IA",
            "machine learning",
            "TensorFlow",
            "PyTorch",
        ]
        
        print(f"\n🧪 Probando {len(project_questions)} consultas sobre proyectos...")
        
        for question in project_questions:
            print(f"\n📋 Consulta: '{question}'")
            
            # Obtener contexto relevante
            retriever = rag_service.vector_store.as_retriever(
                search_kwargs={"k": 10}  # Aumentar k para ver más resultados
            )
            docs = retriever.get_relevant_documents(question)
            
            print(f"📚 Chunks encontrados: {len(docs)}")
            
            # Contar por source
            sources = {}
            for doc in docs:
                source = doc.metadata.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            print(f"📊 Distribución por source: {sources}")
            
            # Mostrar chunks de proyectos si los hay
            project_docs = [doc for doc in docs if doc.metadata.get("source") == "project"]
            if project_docs:
                print(f"✅ Encontrados {len(project_docs)} chunks de proyectos:")
                for i, doc in enumerate(project_docs[:2]):  # Mostrar solo los primeros 2
                    project_id = doc.metadata.get("id", "unknown")
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    print(f"   {i+1}. Project ID: {project_id}")
                    print(f"      Preview: {preview}")
            else:
                print("   ❌ No se encontraron chunks de proyectos")
            
            print("-" * 40)
        
        # Verificar directamente en la base de datos
        print(f"\n🔍 Verificación directa en la base de datos...")
        
        # Consulta directa para contar chunks por source
        from app.core.config import settings
        import psycopg2
        
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        # Contar chunks por source
        cursor.execute("""
            SELECT cmetadata->>'source' as source, COUNT(*) as count
            FROM langchain_pg_embedding 
            WHERE collection_id = (
                SELECT uuid FROM langchain_pg_collection WHERE name = %s
            )
            GROUP BY cmetadata->>'source'
            ORDER BY count DESC
        """, (settings.VECTOR_COLLECTION_NAME,))
        
        results = cursor.fetchall()
        print("📊 Chunks por source en la base de datos:")
        for source, count in results:
            print(f"   {source}: {count} chunks")
        
        # Verificar específicamente chunks de proyectos
        cursor.execute("""
            SELECT cmetadata->>'id' as project_id, 
                   LEFT(document, 100) as preview
            FROM langchain_pg_embedding 
            WHERE collection_id = (
                SELECT uuid FROM langchain_pg_collection WHERE name = %s
            )
            AND cmetadata->>'source' = 'project'
            LIMIT 5
        """, (settings.VECTOR_COLLECTION_NAME,))
        
        project_results = cursor.fetchall()
        print(f"\n📋 Chunks de proyectos en la base de datos ({len(project_results)} encontrados):")
        for project_id, preview in project_results:
            print(f"   Project ID: {project_id}")
            print(f"   Preview: {preview}...")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Investigación completada")
        
    except Exception as e:
        print(f"❌ Error en investigación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_projects())
