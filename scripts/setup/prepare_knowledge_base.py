"""
Script para procesar portfolio.yaml en documentos semánticos para RAG.
Convierte el YAML en chunks optimizados para embeddings y retrieval.
"""
from pathlib import Path
from typing import List

import yaml
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def process_portfolio_to_chunks(portfolio_path: str) -> List[Document]:
    """
    Procesa el archivo portfolio.yaml y lo convierte en chunks semánticos.

    Args:
        portfolio_path: Ruta al archivo portfolio.yaml

    Returns:
        Lista de documentos LangChain listos para embeddings
    """
    # Leer YAML
    with open(portfolio_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    documents = []

    # 1. Información Personal
    personal = data.get("personal_info", {})
    if personal:
        content = f"""
Información Personal:
Nombre: {personal.get('name', 'N/A')}
Título: {personal.get('title', 'N/A')}
Email: {personal.get('email', 'N/A')}
Ubicación: {personal.get('location', 'N/A')}
LinkedIn: {personal.get('linkedin', 'N/A')}
GitHub: {personal.get('github', 'N/A')}
Sitio Web: {personal.get('website', 'N/A')}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={"type": "personal_info", "source": "portfolio.yaml"},
            )
        )

    # 2. Resumen Profesional
    prof_summary = data.get("professional_summary", {})
    if prof_summary:
        short_summary = prof_summary.get("short", "")
        detailed_summary = prof_summary.get("detailed", "")

        content = f"""
Resumen Profesional:

{short_summary}

{detailed_summary}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={"type": "professional_summary", "source": "portfolio.yaml"},
            )
        )

    # 3. Experiencia Laboral (cada empresa es un documento)
    for exp in data.get("experience", []):
        company = exp.get("company", "N/A")
        position = exp.get("position", "N/A")
        duration = exp.get("duration", "N/A")
        location = exp.get("location", "N/A")
        description = exp.get("description", "N/A")
        technologies = ", ".join(exp.get("technologies", []))
        projects = ", ".join(exp.get("related_projects", []))

        content = f"""
Experiencia Laboral:

Empresa: {company}
Posición: {position}
Duración: {duration}
Ubicación: {location}

Descripción:
{description}

Tecnologías utilizadas: {technologies}

Proyectos relacionados: {projects}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "type": "experience",
                    "company": company,
                    "position": position,
                    "duration": duration,
                    "source": "portfolio.yaml",
                },
            )
        )

    # 4. Educación (cada título es un documento)
    for edu in data.get("education", []):
        institution = edu.get("institution", "N/A")
        degree = edu.get("degree", "N/A")
        period = edu.get("period", "N/A")
        details = edu.get("details", "")
        knowledge = edu.get("knowledge_acquired", [])

        knowledge_list = "\n".join([f"- {k}" for k in knowledge])

        content = f"""
Educación:

Institución: {institution}
Título: {degree}
Periodo: {period}

{details}

Conocimientos adquiridos:
{knowledge_list}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "type": "education",
                    "institution": institution,
                    "degree": degree,
                    "period": period,
                    "source": "portfolio.yaml",
                },
            )
        )

    # 5. Skills por categoría
    for skill_cat in data.get("skills", []):
        category = skill_cat.get("category", "N/A")
        items = ", ".join(skill_cat.get("items", []))

        content = f"""
Habilidades Técnicas:

Categoría: {category}

Habilidades: {items}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "type": "skills",
                    "category": category,
                    "source": "portfolio.yaml",
                },
            )
        )

    # 6. Proyectos Destacados
    for project in data.get("projects", []):
        name = project.get("name", "N/A")
        company = project.get("company", "N/A")
        description = project.get("description", "N/A")
        technologies = ", ".join(project.get("technologies", []))

        content = f"""
Proyecto Destacado:

Nombre: {name}
Empresa: {company}

Descripción:
{description}

Tecnologías utilizadas: {technologies}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "type": "project",
                    "name": name,
                    "company": company,
                    "source": "portfolio.yaml",
                },
            )
        )

    # 7. Idiomas
    for lang in data.get("languages", []):
        name = lang.get("name", "N/A")
        level = lang.get("level", "N/A")

        content = f"""
Idioma: {name}
Nivel: {level}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "type": "language",
                    "language": name,
                    "level": level,
                    "source": "portfolio.yaml",
                },
            )
        )

    # 8. Disponibilidad
    availability = data.get("availability", {})
    if availability:
        status = availability.get("status", "N/A")
        notice_period = availability.get("notice_period", "N/A")
        remote_work = availability.get("remote_work", "N/A")

        content = f"""
Disponibilidad:

Estado: {status}
Periodo de aviso: {notice_period}
Trabajo remoto: {remote_work}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={"type": "availability", "source": "portfolio.yaml"},
            )
        )

    # 9. Filosofía e Intereses
    for interest in data.get("philosophy_and_interests", []):
        title = interest.get("title", "N/A")
        description = interest.get("description", "N/A")

        content = f"""
Filosofía e Intereses:

{title}:
{description}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "type": "philosophy",
                    "title": title,
                    "source": "portfolio.yaml",
                },
            )
        )

    # 10. Contexto del chatbot (personalidad)
    chatbot_context = data.get("chatbot_context", {})
    if chatbot_context:
        personality = chatbot_context.get("personality", "N/A")
        tone = chatbot_context.get("tone", "N/A")
        expertise_areas = ", ".join(chatbot_context.get("expertise_areas", []))

        content = f"""
Personalidad del Profesional:

Personalidad: {personality}
Tono de comunicación: {tone}
Áreas de expertise: {expertise_areas}
"""
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={"type": "personality", "source": "portfolio.yaml"},
            )
        )

    # Crear chunks semánticos con overlap para mejor retrieval
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # Tamaño óptimo para embeddings
        chunk_overlap=50,  # Overlap para mantener contexto
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)

    return chunks


def save_chunks_summary(
    chunks: List[Document], output_path: str = "data/chunks_summary.txt"
):
    """
    Guarda un resumen de los chunks generados para inspección.

    Args:
        chunks: Lista de documentos chunk
        output_path: Ruta donde guardar el resumen
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Total de chunks generados: {len(chunks)}\n\n")
        f.write("=" * 80 + "\n\n")

        for i, chunk in enumerate(chunks, 1):
            f.write(f"CHUNK #{i}\n")
            f.write(f"Metadata: {chunk.metadata}\n")
            f.write(f"Content:\n{chunk.page_content}\n")
            f.write("=" * 80 + "\n\n")

    print(f"✓ Resumen guardado en: {output_path}")


if __name__ == "__main__":
    # Test del script
    portfolio_path = "data/portfolio.yaml"

    if not Path(portfolio_path).exists():
        print(f"❌ Error: No se encontró {portfolio_path}")
        exit(1)

    print(f"📄 Procesando {portfolio_path}...")
    chunks = process_portfolio_to_chunks(portfolio_path)

    print(f"✓ {len(chunks)} chunks generados")

    # Mostrar estadísticas
    types = {}
    for chunk in chunks:
        chunk_type = chunk.metadata.get("type", "unknown")
        types[chunk_type] = types.get(chunk_type, 0) + 1

    print("\n📊 Distribución por tipo:")
    for chunk_type, count in sorted(types.items()):
        print(f"  - {chunk_type}: {count} chunks")

    # Guardar resumen
    save_chunks_summary(chunks)
    print("\n✅ Preparación de datos completada")
