# Guarda esto como 'build_knowledge_base.py'
# --------------------------------------------------

import yaml
from langchain.docstore.document import Document
import sys
import os

# --- 1. FUNCIONES DE ENRIQUECIMIENTO (EL ARREGLO FINAL) ---

def create_personal_info_chunk(data):
    """Crea un chunk de prosa semánticamente rico para la información personal."""
    print("Creando chunk: personal_info...")
    personal_data = data.get("personal_info", {})
    personal_prose = f"""
    Información personal y de contacto de Álvaro Maldonado.
    Mi nombre es {personal_data.get('name')}.
    Mi ubicación actual y ciudad de residencia es: {personal_data.get('location')}.
    Mi nacionalidad es: {personal_data.get('nationality')}.
    Información de contacto: mi email es {personal_data.get('email')} y mi sitio web es {personal_data.get('website')}.
    Mi LinkedIn es {personal_data.get('linkedin')}.
    """
    # FAQ Hint para "¿Quién eres?" (complementario al summary)
    personal_prose += "\n--- Preguntas Frecuentes Relevantes ---\n"
    personal_prose += "¿Quién eres?\n"
    personal_prose += "¿Puedes presentarte?\n"

    return [Document(page_content=personal_prose, metadata={"source": "personal_info", "id": "personal_info"})]

def create_professional_summary_chunk(data):
    """Crea un chunk de prosa semánticamente rico para el resumen profesional."""
    print("Creando chunk: professional_summary...")
    summary_data = data.get("professional_summary", {})
    summary_prose = f"""
    Resumen profesional de Álvaro Maldonado.
    Descripción corta: {summary_data.get('short')}
    Descripción detallada: {summary_data.get('detailed')}

    --- Preguntas Frecuentes Relevantes ---
    ¿Cómo te describirías profesionalmente?
    Describe tu perfil profesional.
    ¿Quién eres profesionalmente?
    ¿Háblame de ti profesionalmente?
    """
    return [Document(page_content=summary_prose, metadata={"source": "professional_summary", "id": "professional_summary"})]


def create_professional_conditions_chunk(data):
    """Crea un chunk de prosa semánticamente rico para las condiciones profesionales."""
    print("Creando chunk: professional_conditions...")
    conditions_data = data.get("professional_conditions", {})
    conditions_prose = f"""
    Información sobre mis condiciones profesionales, disponibilidad y expectativas salariales.
    Mi disponibilidad o pre-aviso (notice period) es de: {conditions_data.get('availability', {}).get('notice_period')}.
    Busco trabajo 100% remoto en {conditions_data.get('work_permit', {}).get('target_country')}.
    Respecto a mis expectativas salariales: {conditions_data.get('salary_expectations', {}).get('notes')}.
    Sobre mi permiso de trabajo o visado: {conditions_data.get('work_permit', {}).get('status')}.

    --- Preguntas Frecuentes Relevantes ---
    ¿Cuáles son tus expectativas salariales?
    ¿Necesitas ayuda con el visado?
    ¿Buscas trabajo remoto?
    ¿Cuál es tu disponibilidad?
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
        if "motiv" in title or "resolución" in title or "pasión" in title or "product engineer" in title:
            motivation_prose += f"- {description}\n"

    # FAQ Hints
    motivation_prose += "\n--- Preguntas Frecuentes Relevantes ---\n"
    motivation_prose += "¿Cuál es tu motivación para un nuevo reto profesional?\n"
    motivation_prose += "How does your Product Engineer mindset influence your approach?\n"

    philosophy_prose += "\n--- Preguntas Frecuentes Relevantes ---\n"
    philosophy_prose += "¿Cuál es tu filosofía de trabajo?\n"
    philosophy_prose += "¿Cuáles son tus intereses personales?\n"


    chunks.append(Document(page_content=motivation_prose, metadata={"source": "philosophy_and_interests", "id": "motivation"}))
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

            faq_prose = "\n--- Preguntas Frecuentes Relevantes ---\n"
            has_faq = False

            if project_id == 'proj_acuamattic':
                faq_prose += "¿Cuáles fueron los mayores desafíos técnicos al construir el dataset para AcuaMattic y cómo los superaste?\n"
                faq_prose += "¿Dame un ejemplo de un desafío técnico en un proyecto de IA?\n"
                has_faq = True

            if project_id == 'proj_andes' or project_id == 'proj_spr':
                faq_prose += "¿Describe una situación donde actuaste como puente entre un equipo técnico y stakeholders no técnicos?\n"
                faq_prose += "¿Cómo manejaste la comunicación con stakeholders no técnicos?\n"
                has_faq = True

            if project_id == 'proj_taa':
                faq_prose += "¿Cuáles fueron los desafíos técnicos al migrar el sistema de tiempo y asistencia en Falabella?\n"
                faq_prose += "¿Dame un ejemplo de modernización de un sistema legacy?\n"
                has_faq = True

            if has_faq:
                project_prose += faq_prose

            project_prose += "\n--- Logros Clave ---\n"
            achievements = project_data.get('achievements', [])
            if achievements:
                for achievement in achievements:
                    project_prose += f"- {achievement}\n"
            else:
                project_prose += "- Logros no detallados.\n"

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
        skill_prose = f"Información sobre mi habilidad y experiencia en {skill_id}.\n"
        skill_prose += f"Descripción: {skill_data.get('description')}\n"
        skill_prose += f"Proyectos relacionados: {', '.join(skill_data.get('projects', []))}\n"
        skill_prose += f"Tecnologías clave: {', '.join(skill_data.get('key_technologies', []))}\n"

        # FAQ Hints (Ej: para Q2 IA en Inglés)
        skill_prose += "\n--- Preguntas Frecuentes Relevantes ---\n"
        if skill_id == 'ai_ml':
            skill_prose += "Could you elaborate on your experience with Artificial Intelligence, especially the practical projects you have led?\n"
            skill_prose += "¿Cuál es tu experiencia con IA?\n"
        if skill_id == 'java_backend':
            skill_prose += "¿Cuál es tu experiencia con Java?\n"
        # Añadir más hints si es necesario para otras skills

        chunks.append(
            Document(
                page_content=skill_prose,
                metadata={"source": "skill_showcase", "id": skill_id}
            )
        )
    return chunks

def create_education_chunks(data):
    """Crea chunks enriquecidos para la educación."""
    print("Creando chunks: education...")
    chunks = []
    education_data = data.get("education", [])
    general_education_prose = "Resumen de la formación académica de Álvaro Maldonado.\n"

    for i, edu_item in enumerate(education_data):
        edu_prose = f"""
        Formación académica: {edu_item.get('degree')} en {edu_item.get('institution')}.
        Periodo: {edu_item.get('period')}.
        Detalles: {edu_item.get('details', 'N/A')}.
        Conocimientos adquiridos: {edu_item.get('knowledge_acquired', [])}

        --- Preguntas Frecuentes Relevantes ---
        ¿Cuál es tu formación académica?
        ¿Qué estudios tienes?
        Háblame de tu educación.
        ¿Dónde estudiaste {edu_item.get('degree')}?
        """
        chunks.append(
            Document(
                page_content=edu_prose,
                metadata={"source": "education", "id": f"edu_{i}"}
            )
        )
        general_education_prose += f"- {edu_item.get('degree')} en {edu_item.get('institution')} ({edu_item.get('period')})\n"

    # Chunk General Adicional
    general_education_prose += "\n--- Preguntas Frecuentes Relevantes ---\n"
    general_education_prose += "¿Cuál es tu formación académica general?\n"
    general_education_prose += "Resume tus estudios.\n"
    chunks.append(
        Document(
            page_content=general_education_prose,
            metadata={"source": "education", "id": "education_summary"}
        )
    )
    return chunks


# --- 2. FUNCIÓN PRINCIPAL ---

def load_and_prepare_chunks(yaml_file_path):
    """Carga el YAML y genera todos los chunks enriquecidos."""
    if not os.path.exists(yaml_file_path):
        print(f"Error: No se encuentra el archivo YAML en {yaml_file_path}")
        sys.exit(1) # Salir si no se encuentra el archivo

    print(f"Cargando archivo YAML desde {yaml_file_path}...")
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error al cargar o parsear el archivo YAML: {e}")
        sys.exit(1)

    all_chunks = []
    all_chunks.extend(create_personal_info_chunk(data))
    all_chunks.extend(create_professional_summary_chunk(data)) # <-- Añadido
    all_chunks.extend(create_professional_conditions_chunk(data))
    all_chunks.extend(create_philosophy_chunks(data))
    all_chunks.extend(create_projects_chunks(data))
    all_chunks.extend(create_skills_showcase_chunks(data))
    all_chunks.extend(create_education_chunks(data)) # <-- Añadido

    print(f"\n--- Preparación de Chunks Completa ---")
    print(f"Total de chunks generados: {len(all_chunks)}")
    return all_chunks

# --- 3. EJECUCIÓN (SI SE LLAMA COMO SCRIPT) ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__)) # Ruta absoluta
    # Asume que portfolio.yaml está en el directorio data del proyecto
    yaml_path = os.path.join(script_dir, '..', '..', 'data', 'portfolio.yaml') 

    if not os.path.exists(yaml_path):
         # Si no está en data, prueba en el directorio raíz (menos probable)
        yaml_path = os.path.join(script_dir, '..', 'portfolio.yaml')

    chunks = load_and_prepare_chunks(yaml_path)
    if chunks:
        print("\n--- Verificación de Chunks Enriquecidos ---")
        # Imprime ejemplos para verificar
        for chunk in chunks:
            if chunk.metadata.get("id") == "professional_summary":
                print("\n**Chunk professional_summary:**")
                print(chunk.page_content[:300] + "...") # Muestra inicio
            elif chunk.metadata.get("id") == "education_summary":
                print("\n**Chunk education_summary:**")
                print(chunk.page_content[:300] + "...")
            elif chunk.metadata.get("id") == "personal_info":
                 print("\n**Chunk personal_info:**")
                 print(chunk.page_content[:300] + "...")