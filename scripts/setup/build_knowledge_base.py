# Guarda esto como 'build_knowledge_base.py'
# --------------------------------------------------

import yaml
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import sys
import os

# --- 1. FUNCIONES DE ENRIQUECIMIENTO (EL ARREGLO FINAL) ---

# Configurar text splitter para dividir chunks grandes
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,  # Tamaño ideal del chunk (en caracteres)
    chunk_overlap=50,  # Solapamiento para mantener contexto entre chunks
    length_function=len,
    is_separator_regex=False,
    separators=["\n\n", "\n", ". ", ", ", " ", ""],  # Prioridad de separadores
)

def create_personal_info_chunk(data):
    """Crea chunks fusionando FAQs y contenido para mejor recuperación semántica."""
    print("Creando chunk: personal_info...")
    personal_data = data.get("personal_info", {})
    
    # FAQs específicas para personal_info
    faqs = [
        "¿Quién eres?",
        "¿Puedes presentarte?",
        "¿Dónde vives?",
        "¿Cuál es tu email?"
    ]
    
    # Contenido de información personal
    personal_prose = f"""
    Mi nombre es {personal_data.get('name')}.
    Mi ubicación actual es {personal_data.get('location')}.
    Nacionalidad: {personal_data.get('nationality')}.
    Email: {personal_data.get('email')}
    Sitio web: {personal_data.get('website')}
    LinkedIn: {personal_data.get('linkedin')}
    
    [Preguntas que responden este contenido: {', '.join(faqs)}]
    """
    
    chunks = []
    chunks.append(
        Document(
            page_content=personal_prose,
            metadata={
                "source": "personal_info", 
                "id": "personal_info_0",
                "chunk_type": "qa_fused"
            }
        )
    )
    
    print(f"   ✅ Generado 1 chunk fusionado para personal_info")
    return chunks

def create_professional_summary_chunk(data):
    """Crea chunks fusionando FAQs y contenido para mejor recuperación semántica."""
    print("Creando chunk: professional_summary...")
    summary_data = data.get("professional_summary", {})
    
    # Obtener FAQs del YAML (si existen) o usar FAQs de respaldo
    faqs = summary_data.get('faqs', [])
    if not faqs:
        # FAQs de respaldo si no están en el YAML
        faqs = [
            "¿Quién eres?",
            "¿Cómo te describirías profesionalmente?", 
            "Describe tu perfil profesional.",
            "¿Quién eres profesionalmente?",
            "¿Háblame de ti profesionalmente?"
        ]
    
    # Fusionar contenido y FAQs en un solo texto
    summary_prose = f"""
    {summary_data.get('short', '')}
    
    {summary_data.get('detailed', '')}
    
    [Preguntas que responden este contenido: {', '.join(faqs)}]
    """
    
    chunks = []
    chunks.append(
        Document(
            page_content=summary_prose,
            metadata={
                "source": "professional_summary", 
                "id": "professional_summary_0",
                "chunk_type": "qa_fused"
            }
        )
    )
    
    print(f"   ✅ Generado 1 chunk fusionado para professional_summary")
    return chunks


def create_professional_conditions_chunk(data):
    """Crea chunks atómicos Q&A por cada clave de professional_conditions."""
    print("Creando chunks: professional_conditions...")
    chunks = []
    conditions_data = data.get("professional_conditions", {})
    
    # 1. Chunks granulares para availability (4 chunks separados)
    if 'availability' in conditions_data:
        availability_data = conditions_data['availability']
        
        # Chunk 1: Status + Notice Period (combinados porque se preguntan juntos)
        status_faqs = [
            "¿Cuál es tu disponibilidad?",
            "¿Estás buscando trabajo?",
            "¿Estás disponible?",
            "¿Cuándo podrías empezar?"
        ]
        status_content = f"""
        Disponibilidad: {availability_data.get('status', '')}
        Periodo de pre-aviso: {availability_data.get('notice_period', '')}
        
        [Preguntas que responden este contenido: {', '.join(status_faqs)}]
        """
        chunks.append(
            Document(
                page_content=status_content,
                metadata={
                    "source": "professional_conditions",
                    "id": "availability_status",
                    "chunk_type": "qa_fused"
                }
            )
        )
        
        # Chunk 2: Remote Work (Chunk 2 porque notice está en Chunk 1)
        remote_faqs = [
            "¿Buscas trabajo remoto?",
            "¿Trabajas remotamente?",
            "¿Prefieres trabajo remoto?"
        ]
        remote_content = f"""
        Trabajo remoto: {availability_data.get('remote_work', '')}
        
        [Preguntas que responden este contenido: {', '.join(remote_faqs)}]
        """
        chunks.append(
            Document(
                page_content=remote_content,
                metadata={
                    "source": "professional_conditions",
                    "id": "availability_remote",
                    "chunk_type": "qa_fused"
                }
            )
        )
        
        # Chunk 3: Interview Scheduling
        interview_faqs = [
            "¿Cómo coordinamos una entrevista?",
            "¿Tienes flexibilidad para entrevistas?",
            "¿Cuándo podemos hacer la entrevista?"
        ]
        interview_content = f"""
        Flexibilidad para entrevistas: {availability_data.get('interview_scheduling', '')}
        
        [Preguntas que responden este contenido: {', '.join(interview_faqs)}]
        """
        chunks.append(
            Document(
                page_content=interview_content,
                metadata={
                    "source": "professional_conditions",
                    "id": "availability_interview",
                    "chunk_type": "qa_fused"
                }
            )
        )
    
    # 2. Chunks granulares para work_permit (2 chunks separados)
    if 'work_permit' in conditions_data:
        work_permit_data = conditions_data['work_permit']
        
        # Chunk 1: Status del permiso
        permit_status_faqs = work_permit_data.get('faqs', [
            "¿Necesitas visado?",
            "¿Tienes permiso de trabajo?",
            "¿Necesitas sponsorship?"
        ])
        
        permit_status_content = f"""
        Permiso de trabajo: {work_permit_data.get('status', '')}
        
        [Preguntas que responden este contenido: {', '.join(permit_status_faqs)}]
        """
        
        chunks.append(
            Document(
                page_content=permit_status_content,
                metadata={
                    "source": "professional_conditions",
                    "id": "work_permit_status",
                    "chunk_type": "qa_fused"
                }
            )
        )
        
        # Chunk 2: País objetivo
        country_faqs = [
            "¿En qué país buscas trabajar?",
            "¿Cuál es tu país objetivo?",
            "¿Dónde quieres trabajar?"
        ]
        
        country_content = f"""
        País objetivo: {work_permit_data.get('target_country', '')}
        
        [Preguntas que responden este contenido: {', '.join(country_faqs)}]
        """
        
        chunks.append(
            Document(
                page_content=country_content,
                metadata={
                    "source": "professional_conditions",
                    "id": "work_permit_country",
                    "chunk_type": "qa_fused"
                }
            )
        )
    
    # 3. Chunk para salary_expectations
    if 'salary_expectations' in conditions_data:
        salary_data = conditions_data['salary_expectations']
        salary_faqs = salary_data.get('faqs', [
            "¿Cuáles son tus expectativas salariales?",
            "¿Qué salario buscas?",
            "¿Cuál es tu rango salarial?"
        ])
        
        salary_content = f"""
        Expectativas salariales: {salary_data.get('notes', '')}
        
        [Preguntas que responden este contenido: {', '.join(salary_faqs)}]
        """
        
        chunks.append(
            Document(
                page_content=salary_content,
                metadata={
                    "source": "professional_conditions",
                    "id": "salary_expectations",
                    "chunk_type": "qa_fused"
                }
            )
        )
    
    # 4. Chunk para motivation_for_change (si existe)
    if 'motivation_for_change' in conditions_data:
        motivation_faqs = [
            "¿Cuál es tu motivación para un nuevo reto profesional?",
            "¿Por qué buscas un nuevo reto?",
            "¿Qué te motiva profesionalmente?"
        ]
        
        motivation_content = f"""
        Motivación para un nuevo reto profesional: {conditions_data.get('motivation_for_change', '')}
        
        [Preguntas que responden este contenido: {', '.join(motivation_faqs)}]
        """
        
        chunks.append(
            Document(
                page_content=motivation_content,
                metadata={
                    "source": "professional_conditions",
                    "id": "motivation_for_change",
                    "chunk_type": "qa_fused"
                }
            )
        )
    
    print(f"   ✅ Generados {len(chunks)} chunks atómicos para professional_conditions")
    return chunks

def create_philosophy_chunks(data):
    """Crea chunks atómicos Q&A por cada ítem de philosophy_and_interests."""
    print("Creando chunks: philosophy...")
    chunks = []
    philosophy_data = data.get("philosophy_and_interests", [])
    
    # Crear un chunk atómico por cada ítem
    for i, item in enumerate(philosophy_data):
        title = item.get('title', '')
        description = item.get('description', '')
        
        # Obtener FAQs del YAML o usar fallback
        faqs = item.get('faqs', [])
        if not faqs:
            # Fallback según el tipo de ítem
            title_lower = title.lower()
            if "motiv" in title_lower or "resolución" in title_lower or "pasión" in title_lower:
                faqs = [
                    "¿Cuál es tu motivación para un nuevo reto profesional?",
                    "¿Por qué buscas un nuevo reto?",
                    "¿Qué te motiva profesionalmente?"
                ]
            elif "filosofía" in title_lower:
                faqs = [
                    "¿Cuál es tu filosofía de trabajo?",
                    "¿Qué valores guían tu trabajo?",
                    "¿Cuál es tu enfoque profesional?"
                ]
            elif "intereses" in title_lower or "personales" in title_lower:
                faqs = [
                    "¿Cuáles son tus intereses personales?",
                    "¿Qué haces en tu tiempo libre?",
                    "¿Cómo equilibrias vida personal y profesional?"
                ]
            else:
                faqs = [
                    f"¿Qué es {title.lower()}?",
                    f"¿Puedes hablarme de {title.lower()}?",
                    f"¿Cómo influye {title.lower()} en tu trabajo?"
                ]
        
        # Generar ID único basado en el título
        cleaned_title = title.replace(' ', '_').replace('(', '').replace(')', '').replace("'", '').lower()
        item_id = f"philosophy_{i}_{cleaned_title}"
        
        # Crear chunk fusionado para este ítem
        item_prose = f"""
        {title}: {description}

        [Preguntas que responden este contenido: {', '.join(faqs)}]
        """
        
        chunks.append(
            Document(
                page_content=item_prose,
                metadata={
                    "source": "philosophy_and_interests",
                    "id": item_id,
                    "chunk_type": "qa_fused"
                }
            )
        )
    
    print(f"   ✅ Generados {len(chunks)} chunks atómicos para philosophy_and_interests")
    return chunks

def create_projects_chunks(data):
    """Crea chunks fusionando FAQs y contenido de proyectos."""
    print("Creando chunks: projects (con Q&A fusionado)...")
    chunks = []
    projects_data = data.get("projects", {})

    for project_id, project_data in projects_data.items():
        try:
            # Obtener FAQs del YAML o usar fallback
            faqs = project_data.get('faqs', [])
            if not faqs:
                # Fallback para preguntas comunes de comportamiento
                if project_id == 'proj_acuamattic':
                    faqs = [
                        "¿Cuál fue el logro más significativo en AcuaMattic?",
                        "¿Qué logros conseguiste en AcuaMattic?"
                    ]
                elif project_id == 'proj_andes' or project_id == 'proj_spr':
                    faqs = [
                        "¿Describe una situación donde actuaste como puente entre negocio y tecnología?",
                        "¿Cómo manejaste la comunicación con stakeholders no técnicos?"
                    ]
                elif project_id == 'proj_taa' or project_id == 'proj_migracion_tbk':
                    faqs = [
                        "¿Cuáles fueron los desafíos técnicos en este proyecto?",
                        "¿Qué logros conseguiste en este proyecto?"
                    ]
                else:
                    faqs = [
                        f"¿Qué logros conseguiste en {project_data.get('name')}?",
                        f"¿Cuál fue tu rol en {project_data.get('name')}?"
                    ]
            
            # Construir contenido con ORDEN ÓPTIMO: FAQs PRIMERO, luego Identidad, luego Detalles
            project_prose_parts = []
            
            # 1. FAQs AL PRINCIPIO (máxima prioridad semántica)
            project_prose_parts.append(f"[Preguntas que responden este contenido: {', '.join(faqs)}]")
            project_prose_parts.append("")  # Línea en blanco
            
            # 2. Identidad del proyecto (Nombre, Rol, Descripción)
            project_prose_parts.append(f"{project_data.get('name')}")
            project_prose_parts.append(f"Mi rol fue: {project_data.get('role')}")
            if project_data.get('description'):
                project_prose_parts.append(f"\nDescripción: {project_data.get('description')}")
            project_prose_parts.append("")  # Línea en blanco
            
            # 3. Logros (detalles importantes pero después de FAQs e Identidad)
            achievements = project_data.get('achievements', [])
            if achievements:
                project_prose_parts.append("")  # Línea en blanco adicional
                project_prose_parts.append("Logros y resultados clave del proyecto:")
                project_prose_parts.append("══════ LOGROS CLAVE ══════")
                for achievement in achievements:
                    project_prose_parts.append(f"• {achievement}")
                project_prose_parts.append("")  # Línea en blanco después de logros
            
            # 4. Tecnologías e Impacto
            if project_data.get('technologies'):
                techs = ', '.join(project_data.get('technologies', []))
                project_prose_parts.append(f"\nTecnologías utilizadas: {techs}")
            
            if project_data.get('business_impact'):
                project_prose_parts.append(f"\nImpacto de negocio: {project_data.get('business_impact')}")
            
            # Juntar todo
            project_prose = "\n".join(project_prose_parts)
            
            # Aplicar text_splitter con chunk_size AUMENTADO para proyectos (más riqueza, menos splitting)
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            large_text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,  # Aumentado desde 400 para proyectos más ricos
                chunk_overlap=200,  # Aumentado desde 50 para mantener más contexto
                length_function=len,
                is_separator_regex=False,
                separators=["\n\n", "\n", ". ", ", ", " ", ""],
            )
            project_sub_chunks = large_text_splitter.split_text(project_prose)
            
            for i, sub_content in enumerate(project_sub_chunks):
                chunks.append(
                    Document(
                        page_content=sub_content,
                        metadata={
                            "source": "project", 
                            "id": f"{project_id}_{i}",
                            "original_id": project_id,
                            "chunk_index": i,
                            "total_chunks": len(project_sub_chunks),
                            "chunk_type": "qa_fused"
                        }
                    )
                )
                
        except Exception as e:
            print(f"Error procesando el proyecto {project_id}: {e}")
            pass
    
    print(f"   ✅ Generados {len(chunks)} chunks de proyectos")
    return chunks

def create_skills_showcase_chunks(data):
    """Crea chunks fusionando FAQs y contenido de skills_showcase."""
    print("Creando chunks: skills_showcase (con Q&A fusionado)...")
    chunks = []
    skills_data = data.get("skills_showcase", {})
    projects_data = data.get("projects", {})
    
    for skill_id, skill_data in skills_data.items():
        # Obtener FAQs del YAML o usar fallback
        faqs = skill_data.get('faqs', [])
        if not faqs:
            # Fallback según el tipo de skill
            if skill_id == 'ai_ml':
                faqs = [
                    "¿Cuál es tu experiencia con IA?",
                    "¿Qué proyectos de IA has liderado?",
                    "What is your experience with Artificial Intelligence?",
                    "How do you use Python in AI projects?"
                ]
            elif skill_id == 'java_backend':
                faqs = [
                    "¿Cuál es tu experiencia con Java?",
                    "What is your Java experience?",
                    "¿Qué frameworks Java has utilizado?"
                ]
            elif skill_id == 'microservices':
                faqs = [
                    "¿Cuál es tu experiencia con microservicios?",
                    "What is your experience with microservices?",
                    "¿Has trabajado con arquitecturas de microservicios?"
                ]
            else:
                faqs = [
                    f"¿Cuál es tu experiencia con {skill_id}?",
                    f"What is your experience with {skill_id}?"
                ]
        
        # Construir contenido con ORDEN ÓPTIMO: FAQs PRIMERO, luego Identidad, luego Detalles
        skill_prose_parts = []
        
        # 1. FAQs AL PRINCIPIO (máxima prioridad semántica)
        skill_prose_parts.append(f"[Preguntas que responden este contenido: {', '.join(faqs)}]")
        skill_prose_parts.append("")  # Línea en blanco
        
        # 2. Identidad del skill (ID y Descripción)
        skill_prose_parts.append(f"Habilidad: {skill_id}")
        if skill_data.get('description'):
            skill_prose_parts.append(f"Descripción: {skill_data.get('description')}")
        skill_prose_parts.append("")  # Línea en blanco
        
        # 3. Proyectos (convertir IDs a nombres reales)
        project_ids = skill_data.get('projects', [])
        project_names = []
        for proj_id in project_ids:
            if proj_id in projects_data:
                project_names.append(projects_data[proj_id].get('name', proj_id))
            else:
                project_names.append(proj_id)
        
        if project_names:
            skill_prose_parts.append(f"Proyectos donde aplico esta habilidad: {', '.join(project_names)}")
        
        # 4. Tecnologías y Skills adicionales
        if skill_data.get('key_technologies'):
            techs = ', '.join(skill_data.get('key_technologies', []))
            skill_prose_parts.append(f"\nTecnologías clave: {techs}")
        
        if skill_data.get('key_skills'):
            skills_list = ', '.join(skill_data.get('key_skills', []))
            skill_prose_parts.append(f"Habilidades adicionales: {skills_list}")
        
        # Juntar todo
        skill_prose = "\n".join(skill_prose_parts)
        
        # Aplicar text_splitter con chunk_size AUMENTADO para skills (más riqueza, menos splitting)
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        large_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Aumentado desde 400 para skills más ricos
            chunk_overlap=200,  # Aumentado desde 50 para mantener más contexto
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
        )
        skill_sub_chunks = large_text_splitter.split_text(skill_prose)
        for i, sub_content in enumerate(skill_sub_chunks):
            chunks.append(
                Document(
                    page_content=sub_content,
                    metadata={
                        "source": "skill_showcase", 
                        "id": f"{skill_id}_{i}",
                        "original_id": skill_id,
                        "chunk_index": i,
                        "total_chunks": len(skill_sub_chunks),
                        "chunk_type": "qa_fused"
                    }
                )
            )
    
    print(f"   ✅ Generados {len(chunks)} chunks de skills_showcase")
    return chunks

def create_education_chunks(data):
    """Crea chunks fusionando FAQs y contenido de educación."""
    print("Creando chunks: education...")
    chunks = []
    education_data = data.get("education", [])
    
    # Obtener FAQs del YAML o usar fallback
    education_summary_data = data.get("education_summary", {})
    general_faqs = education_summary_data.get('faqs', [])
    if not general_faqs:
        # Fallback
        general_faqs = [
            "¿Cuál es tu formación académica?",
            "¿Qué estudios tienes?",
            "Háblame de tu educación",
            "What is your academic background?",
            "Tell me about your education"
        ]
    
    # Construir resumen general de educación
    education_summary = []
    for edu_item in education_data:
        education_summary.append(f"- {edu_item.get('degree')} en {edu_item.get('institution')} ({edu_item.get('period')})")
    
    # Crear chunk general fusionado
    general_prose = f"""Formación académica de Álvaro Maldonado:

{chr(10).join(education_summary)}

[Preguntas que responden este contenido: {', '.join(general_faqs)}]"""
    
    chunks.append(
        Document(
            page_content=general_prose,
            metadata={
                "source": "education",
                "id": "education_summary",
                "chunk_type": "qa_fused"
            }
        )
    )
    
    # Crear chunks para cada ítem educativo con FAQs específicas
    for i, edu_item in enumerate(education_data):
        specific_faqs = [
            f"¿Dónde estudiaste {edu_item.get('degree')}?",
            f"¿Qué aprendiste en {edu_item.get('degree')}?",
            f"¿Cuándo estudiaste {edu_item.get('degree')}?",
            f"¿En qué institución estudiaste {edu_item.get('degree')}?"
        ]
        
        edu_prose = f"""{edu_item.get('degree')} en {edu_item.get('institution')}.
Periodo: {edu_item.get('period')}.
Detalles: {edu_item.get('details', 'N/A')}.
Conocimientos adquiridos: {', '.join(edu_item.get('knowledge_acquired', []))}

[Preguntas que responden este contenido: {', '.join(specific_faqs)}]"""
        
        chunks.append(
            Document(
                page_content=edu_prose,
                metadata={
                    "source": "education",
                    "id": f"edu_{i}",
                    "chunk_type": "qa_fused"
                }
            )
        )
    
    print(f"   ✅ Generados {len(chunks)} chunks fusionados para education")
    return chunks

def create_languages_chunks(data):
    """Crea chunks enriquecidos para idiomas."""
    print("Creando chunks: languages...")
    chunks = []
    languages_data = data.get("languages", [])
    
    if not languages_data:
        print("   ⚠️ No se encontraron datos de idiomas")
        return chunks
    
    languages_prose = "Información sobre los idiomas que manejo Álvaro Maldonado.\n"
    
    for i, lang_item in enumerate(languages_data):
        languages_prose += f"Idioma: {lang_item.get('name')}. Nivel: {lang_item.get('level')}.\n"
    
    # FAQ Hints para preguntas sobre idiomas
    languages_prose += "\n--- Preguntas Frecuentes Relevantes ---\n"
    languages_prose += "¿Qué idiomas manejas?\n"
    languages_prose += "¿Cuál es tu nivel de inglés?\n"
    languages_prose += "¿Hablas inglés?\n"
    languages_prose += "¿Qué nivel de inglés tienes?\n"
    languages_prose += "¿Manejas otros idiomas además del español?\n"
    
    # Dividir la prosa si es muy larga
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,  # Tamaño ideal del chunk (en caracteres)
        chunk_overlap=50,  # Solapamiento para mantener contexto entre chunks
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],  # Prioridad de separadores
    )
    
    sub_chunks_content = text_splitter.split_text(languages_prose)
    
    for i, sub_content in enumerate(sub_chunks_content):
        chunks.append(
            Document(
                page_content=sub_content,
                metadata={
                    "source": "languages", 
                    "id": f"languages_{i}",
                    "chunk_index": i,
                    "total_chunks": len(sub_chunks_content)
                }
            )
        )
    
    print(f"   ✅ Generados {len(chunks)} chunks de idiomas")
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
    all_chunks.extend(create_languages_chunks(data)) # <-- Añadido

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