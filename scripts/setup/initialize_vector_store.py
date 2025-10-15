"""
Script para inicializar el vector store en pgvector con los chunks del portfolio.
Ejecutar una sola vez para cargar la base de conocimientos.
"""
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_community.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from prepare_knowledge_base import process_portfolio_to_chunks


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


def initialize_vector_store(portfolio_path: str = "data/portfolio.yaml"):
    """
    Inicializa el vector store en pgvector con los chunks del portfolio.

    Args:
        portfolio_path: Ruta al archivo portfolio.yaml
    """
    print("🚀 Inicializando vector store...\n")

    # 1. Verificar que existe el archivo portfolio
    if not Path(portfolio_path).exists():
        print(f"❌ Error: No se encontró {portfolio_path}")
        return False

    print(f"📄 Procesando {portfolio_path}...")

    # 2. Procesar portfolio en chunks
    try:
        chunks = process_portfolio_to_chunks(portfolio_path)
        print(f"✓ {len(chunks)} chunks generados\n")
    except Exception as e:
        print(f"❌ Error procesando portfolio: {e}")
        return False

    # 3. Inicializar embeddings locales (100% gratis, sin APIs)
    print("🔧 Configurando HuggingFace Embeddings (local)...")
    try:
        # Usar modelo local de HuggingFace - no requiere API ni internet
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
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
        vector_store = PGVector.from_documents(
            documents=chunks,
            embedding=embeddings,
            connection_string=connection_string,
            collection_name="portfolio_knowledge",
            pre_delete_collection=True,  # Limpia colección existente
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
            model_name="sentence-transformers/all-MiniLM-L6-v2",
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
    required_vars = [
        "GCP_PROJECT_ID",
        "CLOUD_SQL_DB",
        "CLOUD_SQL_USER",
        "CLOUD_SQL_PASSWORD",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Faltan variables de entorno:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nConfigura las variables en .env o como variables de entorno")
        sys.exit(1)

    print("=" * 80)
    print("INICIALIZACIÓN DEL VECTOR STORE")
    print("=" * 80 + "\n")

    # Inicializar
    success = initialize_vector_store()

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
