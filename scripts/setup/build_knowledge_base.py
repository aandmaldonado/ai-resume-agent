# Guarda esto como 'build_knowledge_base.py'
# --------------------------------------------------

import yaml
from langchain.docstore.document import Document
import sys
import os

# --- 1. FUNCIONES DE ENRIQUECIMIENTO (EL ARREGLO) ---

def create_personal_info_chunk(data):
    """Crea un chunk de prosa semánticamente rico para la información personal."""
    print("Creando chunk: personal_info...")
    personal_data = data.get("personal_info", {})
    
    # Prosa enriquecida para que el RAG la encuentre
    personal_prose = f"""
    Información personal y de contacto de Álvaro Maldonado.
    Mi nombre es {personal_data.get('name')}.
    Mi ubicación actual y ciudad de residencia es: {personal_data.get('location')}.
    Mi nacionalidad es: {personal_data.get('nationality')}.
    Información de contacto: mi email es {personal_data.get('email')} y mi sitio web es {personal_data.get('website')}.
    Mi LinkedIn es {personal_data.get('linkedin')}.
    """
    return [Document(page_content=personal_prose, metadata={"source": "personal_info", "id": "personal_info"})]

def create_professional_conditions_chunk(data):
    """Crea un chunk de prosa semánticamente rico para las condiciones profesionales."""
    print("Creando chunk: professional_conditions...")
    conditions_data = data.get("professional_conditions", {})
    
    # Prosa enriquecida
    conditions_prose = f"""
    Información sobre mis condiciones profesionales, disponibilidad y expectativas salariales.
    Mi disponibilidad o pre-aviso (notice period) es de: {conditions_data.get('availability', {}).get('notice_period')}.
    Busco trabajo 100% remoto en {conditions_data.get('work_permit', {}).get('target_country')}.
    Respecto a mis expectativas salariales: {conditions_data.get('salary_expectations', {}).get('notes')}.
    Sobre mi permiso de trabajo o visado: {conditions_data.get('work_permit', {}).get('status')}.
    """
    return [Document(page_content=conditions_prose, metadata={"source": "professional_conditions", "id": "professional_conditions"})]

def create_philosophy_chunks(data):
    """Crea chunks enriquecidos para filosofía y motivación."""
    print("Creando chunks: philosophy...")
    chunks = []
    philosophy_data = data.get("philosophy_and_interests", [])
    
    philosophy_prose = "Filosofía de trabajo, intereses y motivación profesional de Álvaro Maldonado.\n"
    motivation_prose = "Mi motivación para aceptar un nuevo reto profesional.\n"
    
    for item in philosophy_data:
        title = item.get('title', '').lower()
        description = item.get('description', '')
        philosophy_prose += f"Título: {item.get('title')}. Descripción: {description}\n"
        
        # Chunk específico para la pregunta de motivación
        if "motiv" in title or "resolución" in title or "pasión" in title:
            motivation_prose += f"- {description}\n"
            
    # Chunk de Motivación (para Q10)
    chunks.append(Document(page_content=motivation_prose, metadata={"source": "philosophy_and_interests", "id": "motivation"}))
    # Chunk General
    chunks.append(Document(page_content=philosophy_prose, metadata={"source": "philosophy_and_interests", "id": "philosophy_general"}))
    return chunks

def create_projects_chunks(data):
    """Crea chunks con Hyper-Enrichment v2 (Preguntas FAQ) para proyectos."""
    print("Creando chunks: projects (con Hyper-Enrichment v2)...")
    chunks = []
    projects_data = data.get("projects", {})

    for project_id, project_data in projects_data.items():
        try:
            project_prose = f"Proyecto: {project_data.get('name')}. Mi rol fue: {project_data.get('role')}.\n"
            project_prose += f"Descripción del proyecto: {project_data.get('description')}.\n"
            
            # --- INICIO DE HYPER-ENRICHMENT V2 (FAQ) ---
            faq_prose = "\n--- Preguntas Frecuentes Relevantes ---\n"
            has_faq = False

            # Pista para Pregunta 3 (AcuaMattic)
            if project_id == 'proj_acuamattic':
                faq_prose += "¿Cuáles fueron los mayores desafíos técnicos al construir el dataset para AcuaMattic y cómo los superaste?\n"
                faq_prose += "¿Dame un ejemplo de un desafío técnico en un proyecto de IA?\n"
                has_faq = True

            # Pista para Pregunta 4 (Bridge/Puente)
            if project_id == 'proj_andes' or project_id == 'proj_spr':
                faq_prose += "¿Describe una situación donde actuaste como puente entre un equipo técnico y stakeholders no técnicos?\n"
                faq_prose += "¿Cómo manejaste la comunicación con stakeholders no técnicos?\n"
                has_faq = True
                
            if project_id == 'proj_taa': # Para la pregunta de ejemplo de Falabella
                faq_prose += "¿Cuáles fueron los desafíos técnicos al migrar el sistema de tiempo y asistencia en Falabella?\n"
                has_faq = True

            if has_faq:
                project_prose += faq_prose
            # --- FIN DE HYPER-ENRICHMENT V2 ---

            project_prose += "\n--- Logros Clave ---\n"
            for achievement in project_data.get('achievements', []):
                project_prose += f"- {achievement}\n"

            chunks.append(
                Document(
                    page_content=project_prose,
                    metadata={"source": "project", "id": project_id}
                )
            )
        except Exception as e:
            print(f"Error procesando el proyecto {project_id}: {e}")
            pass
            
    return chunks

def create_skills_showcase_chunks(data):
    """Crea chunks para cada habilidad en el showcase."""
    print("Creando chunks: skills_showcase...")
    chunks = []
    skills_data = data.get("skills_showcase", {})
    
    for skill_id, skill_data in skills_data.items():
        # Prosa enriquecida para Q2 (IA)
        skill_prose = f"Información sobre mi habilidad y experiencia en {skill_id}.\n"
        skill_prose += f"Descripción: {skill_data.get('description')}\n"
        skill_prose += f"Proyectos relacionados: {', '.join(skill_data.get('projects', []))}\n"
        skill_prose += f"Tecnologías clave: {', '.join(skill_data.get('key_technologies', []))}\n"
        
        # Pista para Q2 (IA)
        if skill_id == 'ai_ml':
            skill_prose += "\n--- Preguntas Frecuentes Relevantes ---\n"
            skill_prose += "Could you elaborate on your experience with Artificial Intelligence, especially the practical projects you have led?\n"
            skill_prose += "¿Puedes dar más detalles sobre tu experiencia con Inteligencia Artificial?\n"

        chunks.append(
            Document(
                page_content=skill_prose,
                metadata={"source": "skill_showcase", "id": skill_id}
            )
        )
    return chunks

# --- 2. FUNCIÓN PRINCIPAL ---

def load_and_prepare_chunks(yaml_file_path):
    """Carga el YAML y genera todos los chunks enriquecidos."""
    
    if not os.path.exists(yaml_file_path):
        print(f"Error: No se encuentra el archivo YAML en {yaml_file_path}")
        return None

    print(f"Cargando archivo YAML desde {yaml_file_path}...")
    with open(yaml_file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    all_chunks = []
    
    # Ejecutar todas las funciones de chunking
    all_chunks.extend(create_personal_info_chunk(data))
    all_chunks.extend(create_professional_conditions_chunk(data))
    all_chunks.extend(create_philosophy_chunks(data))
    all_chunks.extend(create_projects_chunks(data))
    all_chunks.extend(create_skills_showcase_chunks(data))
    
    # (Puedes añadir 'education', 'companies', etc. si también los necesitas)

    print(f"\n--- Preparación de Chunks Completa ---")
    print(f"Total de chunks generados: {len(all_chunks)}")
    
    return all_chunks

# --- 3. EJECUCIÓN (SI SE LLAMA COMO SCRIPT) ---
if __name__ == "__main__":
    # Esto permite que tu script 'initialize_vector_store.py' importe 
    # la función 'load_and_prepare_chunks' sin ejecutar esto.
    # Pero si ejecutas este archivo directamente, intentará cargar.
    
    # Asume que 'portfolio.yaml' está en el directorio data/
    script_dir = os.path.dirname(__file__)
    yaml_path = os.path.join(script_dir, '..', '..', 'data', 'portfolio.yaml') # Ruta correcta
    
    if not os.path.exists(yaml_path):
        yaml_path = os.path.join(script_dir, '..', 'portfolio.yaml') # Prueba alternativa

    chunks = load_and_prepare_chunks(yaml_path)
    
    if chunks:
        print("\n--- Ejemplo de Chunk (personal_info) ---")
        print(chunks[0].page_content)
        print("\n--- Ejemplo de Chunk (AcuaMattic) ---")
        for chunk in chunks:
            if chunk.metadata.get("id") == "proj_acuamattic":
                print(chunk.page_content)
                break
