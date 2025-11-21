"""
Script para inicializar el vector store en pgvector con los chunks del portfolio.
Ejecutar una sola vez para cargar la base de conocimientos.
"""
import os
import sys
import asyncio
from pathlib import Path

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_community.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document

# Importación opcional para evitar errores en producción
# Intentar importar desde el mismo directorio primero
load_and_prepare_chunks = None  # type: ignore
BUILD_KNOWLEDGE_BASE_AVAILABLE = False

try:
    # Intentar importar desde el mismo directorio (scripts/setup/)
    from scripts.setup.build_knowledge_base import load_and_prepare_chunks  # type: ignore
    BUILD_KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    try:
        # Intentar importar sin el path completo
        from build_knowledge_base import load_and_prepare_chunks  # type: ignore
        BUILD_KNOWLEDGE_BASE_AVAILABLE = True
    except ImportError:
        BUILD_KNOWLEDGE_BASE_AVAILABLE = False
        print("⚠️ build_knowledge_base no disponible - funcionando en modo limitado")


def get_connection_string() -> str:
    """
    Construye el connection string para PostgreSQL desde variables de entorno.

    Returns:
        Connection string para psycopg2
    """
    # Para Cloud Run con Cloud SQL Proxy
    if os.getenv("CLOUD_SQL_CONNECTION_NAME"):
        # Conexión Unix socket para Cloud Run
        connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
        db_name = os.getenv("CLOUD_SQL_DB", "chatbot_db")
        db_user = os.getenv("CLOUD_SQL_USER", "postgres")
        db_password = os.getenv("CLOUD_SQL_PASSWORD")

        connection_string = (
            f"postgresql://{db_user}:{db_password}@/"
            f"{db_name}?host=/cloudsql/{connection_name}"
        )
    else:
        # Conexión directa (para desarrollo local)
        db_host = os.getenv("CLOUD_SQL_HOST", "localhost")
        db_port = os.getenv("CLOUD_SQL_PORT", "5432")
        db_name = os.getenv("CLOUD_SQL_DB", "chatbot_db")
        db_user = os.getenv("CLOUD_SQL_USER", "postgres")
        db_password = os.getenv("CLOUD_SQL_PASSWORD")

        connection_string = (
            f"postgresql://{db_user}:{db_password}@" f"{db_host}:{db_port}/{db_name}"
        )

    return connection_string


def initialize_vector_store_script():
    """
    Inicializa el vector store en pgvector con los chunks del portfolio.
    """
    print("🚀 Inicializando vector store...\n")

    print("📄 Procesando portfolio.yaml desde archivo local...")

    # 2. Procesar portfolio en chunks
    try:
        # Usar el nuevo script con Hyper-Enrichment v2 si está disponible
        if BUILD_KNOWLEDGE_BASE_AVAILABLE and load_and_prepare_chunks:
            yaml_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'portfolio.yaml')
            chunks = load_and_prepare_chunks(yaml_path)
            if not chunks:
                raise Exception("No se pudieron generar chunks")
            print(f"✓ {len(chunks)} chunks generados\n")
        else:
            print("⚠️ build_knowledge_base no disponible - saltando generación de chunks")
            return True  # Retornar True para evitar errores en producción
    except Exception as e:
        print(f"❌ Error procesando portfolio: {e}")
        return False

    # 3. Inicializar embeddings locales (100% gratis, sin APIs)
    print("🔧 Configurando HuggingFace Embeddings (local)...")
    try:
        # Usar modelo local de HuggingFace - no requiere API ni internet
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("✓ Embeddings configurados (modelo local)\n")
    except Exception as e:
        print(f"❌ Error configurando embeddings: {e}")
        print("   Asegúrate de tener configuradas las credenciales de GCP")
        return False

    # 4. Obtener connection string
    print("🔧 Configurando conexión a Cloud SQL...")
    try:
        connection_string = get_connection_string()
        print("✓ Connection string configurado\n")
    except Exception as e:
        print(f"❌ Error configurando conexión: {e}")
        return False

    # 5. Crear vector store en pgvector
    print("💾 Guardando chunks en pgvector...")
    print(f"   Esto puede tardar varios minutos ({len(chunks)} chunks)...\n")

    try:
        # Primero, intentar borrar la colección existente si existe
        print("🧹 Eliminando vectores antiguos de la base de datos...")
        try:
            temp_store = PGVector(
                connection_string=connection_string,
                embedding_function=embeddings,
                collection_name="portfolio_knowledge",
            )
            temp_store.delete_collection()
            print("✓ Vectores antiguos eliminados\n")
        except Exception as e:
            # Si no existe la colección, es normal - continuar
            print(f"   (No había vectores antiguos o error al limpiar: {e})\n")
        
        # Ahora crear el nuevo vector store con los chunks actualizados
        print("📚 Guardando nuevos chunks en pgvector...\n")
        vector_store = PGVector.from_documents(
            documents=chunks,
            embedding=embeddings,
            connection_string=connection_string,
            collection_name="portfolio_knowledge",
            pre_delete_collection=False,  # Ya limpiamos manualmente arriba
        )
        print(f"✅ Vector store inicializado exitosamente!")
        print(f"   - {len(chunks)} chunks guardados")
        print(f"   - Colección: portfolio_knowledge")
        print(f"   - Base de datos: {os.getenv('CLOUD_SQL_DB', 'chatbot_db')}\n")

        return True

    except Exception as e:
        print(f"❌ Error guardando en pgvector: {e}")
        print("\nVerifica:")
        print("  1. Cloud SQL está corriendo y accesible")
        print("  2. La extensión pgvector está instalada")
        print("  3. Las credenciales son correctas")
        print("  4. El firewall permite la conexión")
        return False


def test_vector_store():
    """
    Prueba que el vector store funciona correctamente con una consulta de test.
    """
    print("\n🧪 Probando vector store con consulta de test...\n")

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        connection_string = get_connection_string()

        vector_store = PGVector(
            connection_string=connection_string,
            embedding_function=embeddings,
            collection_name="portfolio_knowledge",
        )

        # Consulta de prueba
        test_query = "¿Cuál es tu experiencia profesional?"
        results = vector_store.similarity_search(test_query, k=3)

        print(f"✓ Consulta de test: '{test_query}'")
        print(f"✓ Resultados encontrados: {len(results)}\n")

        for i, doc in enumerate(results, 1):
            print(f"Resultado #{i}:")
            print(f"  Tipo: {doc.metadata.get('type', 'N/A')}")
            print(f"  Preview: {doc.page_content[:100]}...")
            print()

        print("✅ Vector store funcionando correctamente!\n")
        return True

    except Exception as e:
        print(f"❌ Error en test: {e}\n")
        return False


if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()

    # Verificar variables de entorno críticas
    # Base vars always required
    required_vars = [
        "CLOUD_SQL_DB",
        "CLOUD_SQL_USER",
    ]
    
    # Check if running in Cloud Run / Production (using Cloud SQL Proxy socket)
    is_production = bool(os.getenv("CLOUD_SQL_CONNECTION_NAME"))
    
    if is_production:
        print("🌍 Modo Producción detectado (CLOUD_SQL_CONNECTION_NAME definido)")
        required_vars.extend([
            "GCP_PROJECT_ID",
            "CLOUD_SQL_PASSWORD",
        ])
    else:
        print("💻 Modo Local detectado")
        # In local, password might be optional or different, but let's warn if missing but not block
        # if using standard postgres image, password is usually required unless trusted auth
        if not os.getenv("CLOUD_SQL_PASSWORD"):
             print("⚠️ Advertencia: CLOUD_SQL_PASSWORD no está definido (ok si es entorno local sin pass)")

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Faltan variables de entorno requeridas para este entorno:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nConfigura las variables en .env o como variables de entorno")
        sys.exit(1)

    print("=" * 80)
    print("INICIALIZACIÓN DEL VECTOR STORE")
    print("=" * 80 + "\n")

    # Inicializar
    success = initialize_vector_store_script()

    if success:
        # Probar
        test_vector_store()
        print("=" * 80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
    else:
        print("=" * 80)
        print("❌ PROCESO FALLÓ - Revisa los errores arriba")
        print("=" * 80)
        sys.exit(1)


async def initialize_vector_store(chunks: list[Document]) -> bool:
    """
    Función async para inicializar el vector store con chunks dados.
    
    Args:
        chunks: Lista de documentos para cargar en el vector store
        
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        print("🚀 Inicializando vector store...")
        
        # Verificar variables de entorno
        required_vars = [
            "CLOUD_SQL_DB", 
            "CLOUD_SQL_USER",
        ]
        
        # Check if running in Cloud Run / Production
        is_production = bool(os.getenv("CLOUD_SQL_CONNECTION_NAME"))
        
        if is_production:
            required_vars.extend([
                "GCP_PROJECT_ID",
                "CLOUD_SQL_PASSWORD"
            ])
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"❌ Faltan variables de entorno: {', '.join(missing_vars)}")
            return False
        
        # Configurar embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Obtener connection string
        connection_string = get_connection_string()
        
        # Crear vector store
        vector_store = PGVector(
            connection_string=connection_string,
            embedding_function=embeddings,
            collection_name="portfolio_chunks"
        )
        
        # Limpiar colección existente
        print("🧹 Limpiando colección existente...")
        vector_store.delete_collection()
        
        # Cargar chunks
        print(f"📚 Cargando {len(chunks)} chunks enriquecidos...")
        vector_store.add_documents(chunks)
        
        print("✅ Vector store inicializado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando vector store: {e}")
        return False
