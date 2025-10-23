#!/usr/bin/env python3
"""
Script para preparar la base de conocimiento desde portfolio.yaml
Compatible con la nueva estructura YAML v2.0
Mantiene funcionalidad de Cloud Storage y Cloud SQL
"""

import os
import sys
import yaml
import logging
from typing import List, Dict, Any
from langchain.docstore.document import Document
from google.cloud import storage

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_yaml_from_gcs(bucket_name: str, blob_name: str) -> Dict[str, Any]:
    """Carga el archivo YAML desde archivo local (v2.0)"""
    logger.info("Cargando portfolio.yaml desde archivo local...")
    with open("data/portfolio.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_personal_info_chunks(personal_info: Dict[str, Any]) -> List[Document]:
    """Crea chunks enriquecidos para información personal"""
    chunks = []
    
    # Chunk enriquecido con prosa semánticamente rica
    personal_prose = f"""
Información personal y de contacto de Álvaro Maldonado.
Mi nombre es {personal_info['name']}.
Mi ubicación actual, ciudad de residencia, es: {personal_info['location']}.
Nacionalidad: {personal_info['nationality']}.
Información de contacto: mi email es {personal_info['email']} y mi web es {personal_info['website']}.
LinkedIn: {personal_info['linkedin']}
GitHub: {personal_info['github']}
"""
    
    chunks.append(Document(
        page_content=personal_prose.strip(),
        metadata={
            "type": "personal_info",
            "name": personal_info['name'],
            "title": personal_info['title'],
            "email": personal_info['email'],
            "location": personal_info['location'],
            "nationality": personal_info['nationality'],
            "website": personal_info['website'],
            "linkedin": personal_info['linkedin'],
            "github": personal_info['github'],
            "source": "portfolio.yaml"
        }
    ))
    
    return chunks

def create_professional_summary_chunks(professional_summary: Dict[str, Any]) -> List[Document]:
    """Crea chunks para resumen profesional"""
    chunks = []
    
    summary_content = f"""
RESUMEN PROFESIONAL CORTO: {professional_summary['short']}

RESUMEN PROFESIONAL DETALLADO:
{professional_summary['detailed']}
"""
    
    chunks.append(Document(
        page_content=summary_content.strip(),
        metadata={
            "type": "professional_summary",
            "short": professional_summary['short'],
            "detailed": professional_summary['detailed'],
            "source": "portfolio.yaml"
        }
    ))
    
    return chunks


def create_chatbot_context_chunks(chatbot_context: Dict[str, Any]) -> List[Document]:
    """Crea chunks para contexto del chatbot"""
    chunks = []
    
    # Chunk principal del contexto
    context_content = f"""
PERSONALIDAD DEL CHATBOT: {chatbot_context['personality']}
TONO: {chatbot_context['tone']}
ÁREAS DE EXPERTISE: {', '.join(chatbot_context['expertise_areas'])}

GUÍAS DE RESPUESTA:
{chr(10).join(f"- {guideline}" for guideline in chatbot_context.get('response_guidelines', []))}
"""
    
    chunks.append(Document(
        page_content=context_content.strip(),
                metadata={
            "type": "chatbot_context",
            "personality": chatbot_context['personality'],
            "tone": chatbot_context['tone'],
            "expertise_areas": chatbot_context['expertise_areas'],
            "response_guidelines": chatbot_context.get('response_guidelines', []),
            "source": "portfolio.yaml"
        }
    ))
    
    # Chunks para respuestas comunes
    common_answers = chatbot_context.get('common_questions_answers', {})
    for question_type, answer in common_answers.items():
        answer_content = f"""
TIPO DE PREGUNTA: {question_type}
RESPUESTA PREPARADA: {answer}
"""
        chunks.append(Document(
            page_content=answer_content.strip(),
            metadata={
                "type": "common_answer",
                "question_type": question_type,
                "answer": answer,
                "source": "portfolio.yaml"
            }
        ))
    
    return chunks


def create_personal_details_chunks(personal_details: Dict[str, Any]) -> List[Document]:
    """Crea chunks para detalles personales"""
    chunks = []
    
    # Verificar que las claves existen
    nationality = personal_details.get('nationality', 'No especificado')
    work_permit = personal_details.get('work_permit', 'No especificado')
    remote_work = personal_details.get('remote_work', 'No especificado')
    notice_period = personal_details.get('notice_period', 'No especificado')
    
    details_content = f"""
NACIONALIDAD: {nationality}
PERMISO DE TRABAJO: {work_permit}
TRABAJO REMOTO: {remote_work}
PERÍODO DE NOTIFICACIÓN: {notice_period}

EXPECTATIVAS SALARIALES:
{chr(10).join(f"- {role['role']}: {role['range_euros_gross_annual']}" for role in personal_details.get('salary_expectations', []))}
"""
    
    chunks.append(Document(
        page_content=details_content.strip(),
                metadata={
            "type": "personal_details",
            "nationality": nationality,
            "work_permit": work_permit,
            "remote_work": remote_work,
            "notice_period": notice_period,
            "salary_expectations": personal_details.get('salary_expectations', []),
            "source": "portfolio.yaml"
        }
    ))
    
    return chunks

def create_skills_chunks(skills: List[Dict[str, Any]]) -> List[Document]:
    """Crea chunks para skills con estructura v2.0 (lista)"""
    chunks = []
    
    for skill_cat in skills:
        category = skill_cat.get('category', 'N/A')
        items = ", ".join(skill_cat.get('items', []))

        skills_content = f"""
CATEGORÍA: {category}
SKILLS: {items}
"""
        chunks.append(Document(
            page_content=skills_content.strip(),
            metadata={
                "type": "skills_category",
                "category": category,
                "skills": skill_cat.get('items', []),
                "source": "portfolio.yaml"
            }
        ))
    
    return chunks



def create_projects_chunks(projects: Dict[str, Any]) -> List[Document]:
    """Crea chunks para proyectos con nueva estructura v2.0"""
    chunks = []
    
    for project_id, project in projects.items():
        # Chunk principal del proyecto
        project_content = f"""
PROYECTO: {project['name']}
ID: {project_id}
EMPRESA: {project['company_ref']}
ROL: {project['role']}
DESCRIPCIÓN: {project['description']}

TECNOLOGÍAS: {', '.join(project.get('technologies', []))}
HARDWARE: {', '.join(project.get('hardware', []))}

LOGROS:
{chr(10).join(f"- {achievement}" for achievement in project.get('achievements', []))}

IMPACTO DE NEGOCIO: {project.get('business_impact', 'No especificado')}
"""
        
        chunks.append(Document(
            page_content=project_content.strip(),
            metadata={
                "type": "project",
                "project_id": project_id,
                "project_name": project['name'],
                "company_ref": project['company_ref'],
                "role": project['role'],
                "technologies": project.get('technologies', []),
                "hardware": project.get('hardware', []),
                "achievements": project.get('achievements', []),
                "business_impact": project.get('business_impact', ''),
                "source": "portfolio.yaml"
            }
        ))
        
        # Chunks individuales para tecnologías específicas
        for tech in project.get('technologies', []):
            tech_content = f"""
TECNOLOGÍA: {tech}
PROYECTO: {project['name']} ({project_id})
EMPRESA: {project['company_ref']}
ROL: {project['role']}
CONTEXTO: {project['description']}
"""
            chunks.append(Document(
                page_content=tech_content.strip(),
                metadata={
                    "type": "technology",
                    "technology": tech,
                    "project_id": project_id,
                    "project_name": project['name'],
                    "company_ref": project['company_ref'],
                    "role": project['role'],
                    "source": "portfolio.yaml"
                }
            ))
        
        # Chunks individuales para hardware específico
        for hw in project.get('hardware', []):
            hw_content = f"""
HARDWARE: {hw}
PROYECTO: {project['name']} ({project_id})
EMPRESA: {project['company_ref']}
ROL: {project['role']}
CONTEXTO: {project['description']}
"""
            chunks.append(Document(
                page_content=hw_content.strip(),
                metadata={
                    "type": "hardware",
                    "hardware": hw,
                    "project_id": project_id,
                    "project_name": project['name'],
                    "company_ref": project['company_ref'],
                    "role": project['role'],
                    "source": "portfolio.yaml"
                }
            ))
    
    return chunks

def create_companies_chunks(companies: Dict[str, Any]) -> List[Document]:
    """Crea chunks para empresas con nueva estructura v2.0"""
    chunks = []
    
    for company_id, company in companies.items():
        for position in company.get('positions', []):
            company_content = f"""
EMPRESA: {company['name']}
ID: {company_id}
POSICIÓN: {position['role']}
DURACIÓN: {position['duration']}
UBICACIÓN: {position['location']}
PROYECTOS TRABAJADOS: {', '.join(position.get('projects_worked_on', []))}
"""
            
            chunks.append(Document(
                page_content=company_content.strip(),
                metadata={
                    "type": "company",
                    "company_id": company_id,
                    "company_name": company['name'],
                    "position": position['role'],
                    "duration": position['duration'],
                    "location": position['location'],
                    "projects": position.get('projects_worked_on', []),
                    "source": "portfolio.yaml"
                }
            ))
    
    return chunks

def create_skills_showcase_chunks(skills_showcase: Dict[str, Any]) -> List[Document]:
    """Crea chunks para skills showcase con nueva estructura v2.0"""
    chunks = []
    
    for skill_name, skill_data in skills_showcase.items():
        skill_content = f"""
SKILL: {skill_name}
DESCRIPCIÓN: {skill_data.get('description', 'No especificado')}
PROYECTOS DONDE SE USÓ: {', '.join(skill_data.get('projects', []))}
TECNOLOGÍAS CLAVE: {', '.join(skill_data.get('key_technologies', []))}
"""
        
        chunks.append(Document(
            page_content=skill_content.strip(),
            metadata={
                "type": "skill_showcase",
                "skill_name": skill_name,
                "description": skill_data.get('description', ''),
                "projects": skill_data.get('projects', []),
                "key_technologies": skill_data.get('key_technologies', []),
                "source": "portfolio.yaml"
            }
        ))
    
    return chunks

def create_education_chunks(education: List[Dict[str, Any]]) -> List[Document]:
    """Crea chunks para educación con nueva estructura v2.0"""
    chunks = []
    
    for edu in education:
        edu_content = f"""
EDUCACIÓN: {edu.get('degree', 'N/A')}
INSTITUCIÓN: {edu.get('institution', 'N/A')}
PERÍODO: {edu.get('period', 'N/A')}
DETALLES: {edu.get('details', 'No especificado')}

CONOCIMIENTOS ADQUIRIDOS:
{chr(10).join(f"- {knowledge}" for knowledge in edu.get('knowledge_acquired', []))}
"""
        
        chunks.append(Document(
            page_content=edu_content.strip(),
                metadata={
                "type": "education",
                "degree": edu.get('degree', 'N/A'),
                "institution": edu.get('institution', 'N/A'),
                "period": edu.get('period', 'N/A'),
                "details": edu.get('details', ''),
                "knowledge_acquired": edu.get('knowledge_acquired', []),
                "source": "portfolio.yaml"
            }
        ))
    
    return chunks

def create_languages_chunks(languages: List[Dict[str, Any]]) -> List[Document]:
    """Crea chunks para idiomas con nueva estructura v2.0"""
    chunks = []
    
    for lang in languages:
        lang_content = f"""
IDIOMA: {lang.get('name', 'N/A')}
NIVEL: {lang.get('level', 'N/A')}
"""
        
        chunks.append(Document(
            page_content=lang_content.strip(),
            metadata={
                "type": "language",
                "language": lang.get('name', 'N/A'),
                "level": lang.get('level', 'N/A'),
                "source": "portfolio.yaml"
            }
        ))

    return chunks

def create_professional_conditions_chunks(professional_conditions: Dict[str, Any]) -> List[Document]:
    """Crea chunks enriquecidos para condiciones profesionales"""
    chunks = []
    
    # Chunk enriquecido con prosa semánticamente rica
    conditions_prose = f"""
Condiciones profesionales y laborales de Álvaro Maldonado.
Mi disponibilidad actual es: {professional_conditions.get('availability', {}).get('status', 'N/A')}.
Mi período de pre-aviso es: {professional_conditions.get('availability', {}).get('notice_period', 'N/A')}.
Trabajo remoto: {professional_conditions.get('availability', {}).get('remote_work', 'N/A')}.

Mi situación de permiso de trabajo es: {professional_conditions.get('work_permit', {}).get('status', 'N/A')}.
Mi país objetivo es: {professional_conditions.get('work_permit', {}).get('target_country', 'N/A')}.

Mis expectativas salariales: {professional_conditions.get('salary_expectations', {}).get('notes', 'N/A')}
"""
    
    chunks.append(Document(
        page_content=conditions_prose.strip(),
        metadata={
            "type": "professional_conditions",
            "availability": professional_conditions.get('availability', {}),
            "work_permit": professional_conditions.get('work_permit', {}),
            "salary_expectations": professional_conditions.get('salary_expectations', {}),
            "source": "portfolio.yaml"
        }
    ))

    return chunks

def create_philosophy_chunks(philosophy_and_interests: List[Dict[str, Any]]) -> List[Document]:
    """Crea chunks enriquecidos para filosofía e intereses"""
    chunks = []
    
    # Chunk específico para motivación (pregunta frecuente)
    motivation_chunk = f"""
Mi motivación para aceptar un nuevo reto profesional.
Lo que más me motiva es enfrentarme a problemas que no tienen una solución obvia.
Disfruto del proceso de análisis, la colaboración y la aplicación de la tecnología para encontrar soluciones creativas a desafíos complejos.
Mi filosofía se centra en la mentalidad de 'Product Engineer': entender el 'porqué' del negocio antes de diseñar el 'cómo' técnico.
Soy un profesional autodidacta por naturaleza y dedico tiempo al aprendizaje continuo sobre IA.
Mi objetivo es utilizar la tecnología para resolver problemas reales y aportar valor medible.
"""
    
    chunks.append(Document(
        page_content=motivation_chunk.strip(),
        metadata={
            "type": "philosophy",
            "title": "Motivación Profesional",
            "description": "Motivación para nuevos retos profesionales",
            "source": "portfolio.yaml"
        }
    ))
    
    # Chunk general de filosofía
    philosophy_prose = "Filosofía de trabajo, intereses y motivación profesional de Álvaro Maldonado.\n"
    for item in philosophy_and_interests:
        philosophy_prose += f"Título: {item.get('title')}. Descripción: {item.get('description')}\n"
    
    chunks.append(Document(
        page_content=philosophy_prose.strip(),
        metadata={
            "type": "philosophy",
            "title": "Filosofía General",
            "description": "Filosofía general de trabajo e intereses",
            "source": "portfolio.yaml"
        }
    ))

    return chunks

def prepare_knowledge_base_from_yaml(yaml_data: Dict[str, Any]) -> List[Document]:
    """Prepara la base de conocimiento desde los datos YAML v2.0"""
    all_chunks = []
    
    logger.info(f"Estructura YAML cargada: {list(yaml_data.keys())}")
    logger.info("Procesando estructura YAML v2.0")
    
    # Procesar cada sección del YAML v2.0
    if 'personal_info' in yaml_data:
        logger.info("Procesando personal_info...")
        all_chunks.extend(create_personal_info_chunks(yaml_data['personal_info']))
    
    if 'professional_summary' in yaml_data:
        logger.info("Procesando professional_summary...")
        all_chunks.extend(create_professional_summary_chunks(yaml_data['professional_summary']))
    
    if 'projects' in yaml_data:
        logger.info("Procesando projects...")
        all_chunks.extend(create_projects_chunks(yaml_data['projects']))
    
    if 'companies' in yaml_data:
        logger.info("Procesando companies...")
        all_chunks.extend(create_companies_chunks(yaml_data['companies']))
    
    if 'skills_showcase' in yaml_data:
        logger.info("Procesando skills_showcase...")
        all_chunks.extend(create_skills_showcase_chunks(yaml_data['skills_showcase']))
    
    if 'education' in yaml_data:
        logger.info("Procesando education...")
        all_chunks.extend(create_education_chunks(yaml_data['education']))
    
    if 'languages' in yaml_data:
        logger.info("Procesando languages...")
        all_chunks.extend(create_languages_chunks(yaml_data['languages']))
    
    if 'professional_conditions' in yaml_data:
        logger.info("Procesando professional_conditions...")
        all_chunks.extend(create_professional_conditions_chunks(yaml_data['professional_conditions']))
    
    if 'philosophy_and_interests' in yaml_data:
        logger.info("Procesando philosophy_and_interests...")
        all_chunks.extend(create_philosophy_chunks(yaml_data['philosophy_and_interests']))
    
    if 'skills' in yaml_data:
        logger.info("Procesando skills...")
        all_chunks.extend(create_skills_chunks(yaml_data['skills']))
    
    if 'chatbot_context' in yaml_data:
        logger.info("Procesando chatbot_context...")
        all_chunks.extend(create_chatbot_context_chunks(yaml_data['chatbot_context']))
    
    logger.info(f"Total de chunks creados: {len(all_chunks)}")
    return all_chunks

def main():
    """Función principal"""
    try:
        # Configuración
        bucket_name = "almapi-portfolio-data"
        blob_name = "portfolio.yaml"
        
        logger.info("Cargando portfolio.yaml desde Google Cloud Storage...")
        yaml_data = load_yaml_from_gcs(bucket_name, blob_name)
        
        logger.info("Preparando base de conocimiento...")
        chunks = prepare_knowledge_base_from_yaml(yaml_data)
        
        logger.info(f"Base de conocimiento preparada con {len(chunks)} chunks")

        # Mostrar estadísticas
        type_counts = {}
        for chunk in chunks:
            chunk_type = chunk.metadata.get('type', 'unknown')
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        
        logger.info("Estadísticas por tipo de chunk:")
        for chunk_type, count in type_counts.items():
            logger.info(f"  {chunk_type}: {count}")
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error preparando base de conocimiento: {e}")
        raise

if __name__ == "__main__":
    chunks = main()
    print(f"✅ Base de conocimiento preparada con {len(chunks)} chunks")