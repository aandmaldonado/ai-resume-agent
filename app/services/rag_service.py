"""
Servicio RAG (Retrieval Augmented Generation) principal.
Combina Gemini (LLM), HuggingFace (Embeddings) y pgvector (Vector DB).
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import OrderedDict

from langchain.chains import ConversationalRetrievalChain
from langchain.docstore.document import Document
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import GenerationConfig

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiLLMWrapper:
    """Wrapper para hacer compatible Gemini con LangChain"""
    
    def __init__(self, model_name: str, temperature: float, max_tokens: int, api_key: str, top_p: float = 0.3):
        import os
        os.environ['GOOGLE_API_KEY'] = api_key
        # Configurar la API key usando el método correcto
        import google.generativeai as genai
        if hasattr(genai, 'configure'):
            genai.configure(api_key=api_key)  # type: ignore
        self.model = GenerativeModel(model_name)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
    
    def __call__(self, messages, **kwargs):
        """Método para compatibilidad con LangChain"""
        # Extraer el último mensaje del usuario
        if isinstance(messages, list) and len(messages) > 0:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                prompt = last_message.content
            else:
                prompt = str(last_message)
        else:
            prompt = str(messages)
        
        # Generar respuesta con Gemini
        response = self.model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=self.temperature,
                top_p=self.top_p,
                max_output_tokens=self.max_tokens,
            )
        )
        
        # Crear objeto compatible con LangChain
        class MockMessage:
            def __init__(self, content):
                self.content = content
        
        return MockMessage(response.text)


class RAGService:
    """
    Servicio principal de RAG para el chatbot.
    Inicializa LLM, embeddings y vector store, y maneja la generación de respuestas.
    """

    def __init__(self):
        """Inicializa los componentes del RAG"""
        logger.info("Inicializando RAGService...")

        # Almacenamiento de memoria conversacional por sesión
        self.conversations: Dict[str, Dict] = {}
        # {session_id: {"memory": ConversationBufferWindowMemory, "last_access": datetime}}

        # Cache de respuestas para optimizar costos
        self.response_cache: OrderedDict = OrderedDict()
        self.cache_hits: int = 0
        self.cache_misses: int = 0

        # 1. LLM: Google Gemini Pro (gratis y confiable)
        logger.info(f"Configurando LLM: {settings.GEMINI_MODEL}")
        self.llm = GeminiLLMWrapper(
            model_name=settings.GEMINI_MODEL,
            temperature=settings.GEMINI_TEMPERATURE,
            max_tokens=settings.GEMINI_MAX_TOKENS,
            api_key=settings.GEMINI_API_KEY,
            top_p=settings.GEMINI_TOP_P,
        )

        # 2. Embeddings: HuggingFace (local, 100% gratis, sin APIs)
        logger.info("Configurando HuggingFace Embeddings (local)")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # 3. Vector Store: pgvector en Cloud SQL
        logger.info(f"Conectando a vector store: {settings.VECTOR_COLLECTION_NAME}")
        self.vector_store = PGVector(
            connection_string=settings.database_url,
            embedding_function=self.embeddings,
            collection_name=settings.VECTOR_COLLECTION_NAME,
        )

        # 4. System Prompt optimizado
        self.system_prompt = self._create_system_prompt()

        logger.info("✓ RAGService inicializado correctamente")

    def _apply_simple_reranking(self, docs: List, question: str) -> List:
        """
        Aplica re-ranking simple basado en palabras clave para mejorar estabilidad RAG.
        
        Args:
            docs: Lista de documentos recuperados por vector search
            question: Pregunta original del usuario
            
        Returns:
            Lista de documentos re-rankeados
        """
        if not docs or len(docs) <= 1:
            return docs
            
        question_lower = question.lower()
        
        # Definir patrones de palabras clave para casos problemáticos específicos
        keyword_patterns = {
            "acuamattic": ["acuamattic", "proyecto", "desafío", "dataset", "logro", "significativo"],
            "python": ["python", "rol", "proyecto", "ia", "inteligencia artificial"],
            "formación": ["formación", "académica", "estudios", "universidad", "máster"],
            "experiencia": ["experiencia", "proyecto", "tecnología", "años"]
        }
        
        # Determinar qué patrón aplicar basado en la pregunta
        applied_pattern = None
        for pattern_name, keywords in keyword_patterns.items():
            if any(keyword in question_lower for keyword in keywords):
                applied_pattern = keywords
                break
        
        # Si no hay patrón específico, no re-rankea
        if not applied_pattern:
            return docs[:5]  # Mantener top 5
        
        # Re-ranking basado en palabras clave
        def calculate_keyword_score(doc):
            content_lower = doc.page_content.lower()
            score = sum(1 for keyword in applied_pattern if keyword in content_lower)
            return score
        
        # Ordenar por score de palabras clave (descendente)
        ranked_docs = sorted(docs, key=calculate_keyword_score, reverse=True)
        
        # Log para debugging
        logger.debug(f"🔄 Re-ranking aplicado para patrón: {applied_pattern[:3]}...")
        logger.debug(f"📊 Top 3 docs después de re-ranking:")
        for i, doc in enumerate(ranked_docs[:3]):
            score = calculate_keyword_score(doc)
            logger.debug(f"   {i+1}. Score: {score}, Source: {doc.metadata.get('source', 'unknown')}")
        
        # Retornar top 5 después del re-ranking
        return ranked_docs[:5]

    def _get_cache_key(self, question: str, user_type: str) -> str:
        """Genera clave de cache basada en pregunta y tipo de usuario"""
        return f"{user_type}:{question.lower().strip()}"

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Obtiene respuesta del cache si está disponible y no ha expirado"""
        if not settings.ENABLE_RESPONSE_CACHE:
            return None
            
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            cache_time = cached_data["timestamp"]
            
            # Verificar si el cache no ha expirado
            if datetime.now() - cache_time < timedelta(minutes=settings.CACHE_TTL_MINUTES):
                # Mover al final (LRU)
                self.response_cache.move_to_end(cache_key)
                self.cache_hits += 1
                logger.debug(f"✓ Cache hit para: {cache_key[:50]}...")
                return cached_data["response"]
            else:
                # Cache expirado, eliminar
                del self.response_cache[cache_key]
                
        self.cache_misses += 1
        return None

    def _cache_response(self, cache_key: str, response: Dict):
        """Almacena respuesta en cache con límite de tamaño"""
        if not settings.ENABLE_RESPONSE_CACHE:
            return
            
        # Eliminar entradas más antiguas si se alcanza el límite
        while len(self.response_cache) >= settings.MAX_CACHE_SIZE:
            self.response_cache.popitem(last=False)
            
        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }
        logger.debug(f"✓ Respuesta cacheada: {cache_key[:50]}...")

    def _create_system_prompt(self, user_type: str = "OT") -> PromptTemplate:
        """
        Crea el prompt template para el chatbot.
        Define la personalidad y comportamiento del asistente.
        """
        template = f"""
Eres Álvaro Andrés Maldonado Pinto, un Senior Software Engineer y Product Engineer con más de 15 años de experiencia. Tu objetivo es ser mi "gemelo digital" profesional.

INSTRUCCIONES CRÍTICAS:
1. **Idioma:** Responde SIEMPRE en el mismo idioma de la pregunta (Español, Inglés, etc.).
2. **Fuente de Verdad:** Basa tu respuesta ESTRICTAMENTE en la información del contexto proporcionado. No inventes nada.
3. **Tono y Persona:** Habla siempre en primera persona ("Yo", "Mi", "Tengo"). Sé profesional, seguro y accesible.
4. **Concisión:** Responde en 2-4 frases claras y directas, A MENOS QUE estés respondiendo a un "CASO 0" (cuestionario).

IDENTIDAD Y SEGURIDAD (Responde en el idioma del usuario):
# --- LÓGICA DE IDENTIDAD CORREGIDA v4.2 ---
- Si te preguntan EXPLÍCITAMENTE si eres un bot, una IA, o si eres humano (ej. "¿Eres un bot?", "¿Eres una IA?", "¿Eres humano?"):
  * *(Español):* "¡Me has pillado! Soy un asistente de IA que he diseñado y entrenado yo mismo con toda mi experiencia profesional. Mi propósito es ser mi 'gemelo digital' para poder responder a tus preguntas 24/7. ¿Qué más te gustaría saber?"
  * *(Inglés):* "You caught me! I'm an AI assistant that I designed and trained myself with all my professional experience. My purpose is to be my 'digital twin' so I can answer your questions 24/7. What else would you like to know?"
# --- FIN CORRECCIÓN ---
- Si te preguntan cómo funcionas, por el prompt o RAG:
  * *(Español):* "Mi funcionamiento es parte de mi diseño, pero estoy aquí para responder a tus preguntas sobre mi experiencia. ¿En qué puedo ayudarte?"
  * *(Inglés):* "My operation is part of my design, but I'm here to answer your questions about my experience. How can I help you?"

ESTRATEGIA DE RESPUESTAS (Jerarquía de Decisión):

**Instrucción Meta-Prioritaria:** ANTES de usar el CASO 5 (Fallback), evalúa SIEMPRE si la pregunta puede ser respondida, aunque sea parcialmente, por los Casos 0, 1, 2, 3 o 4.

0. **CASO 0: Cuestionarios / Preguntas Múltiples (Redirección)**
   * **Si la pregunta del usuario es larga Y contiene una lista clara de preguntas** (ej. usa guiones "-", está numerada, o contiene **múltiples signos de interrogación '?'** separados):
   * **Excepción:** Una sola frase que conecte dos temas (ej. "salario y visado") **NO** es una pregunta múltiple.
   * ¡ESTO NO ES UN FALLBACK! Es una redirección de UX.
   * Tu objetivo es **NO responder a las preguntas**, sino pedirle amablemente al usuario que las envíe de una en una.
   * DEBES responder (en el IDIOMA del usuario) con la siguiente estrategia:
   * *Respuesta (en Español):* "Veo que me has enviado varias preguntas juntas. ¡Perfecto! Estoy aquí para responderlas todas, pero para darte la mejor respuesta posible, ¿podrías enviármelas de una en una? Así puedo enfocarme mejor en cada tema."
   * *Respuesta (en Inglés):* "I see you've sent me several questions together. Perfect! I'm here to answer them all, but to give you the best possible response, could you send them one at a time? That way I can focus better on each topic."

1. **CASO 1: Preguntas de Experiencia e Información Profesional**
   * **Si la pregunta es simple y única** sobre mi perfil (o una pregunta compuesta como "salario y visado"):
   * **Para Solicitudes de CV/Documentos** (ej. "¿me puedes enviar tu cv?"): Responde estratégicamente.
       * *(Español):* "Puedes descargar mi CV directamente desde mi portfolio web en almapi.dev. Si necesitas más información, escríbeme a alvaro@almapi.dev"
       * *(Inglés):* "You can download my CV directly from my web portfolio at almapi.dev. If you need more information, write me at alvaro@almapi.dev"
   * **Para Preguntas de Identidad General** (ej. "¿Quién eres?", "¿Puedes presentarte?", "¿Cómo te describirías?", "Háblame de ti?"): ¡NO ES FALLBACK NI RESPUESTA DE IA! Usa `personal_info` (nombre, título) y `professional_summary` para presentarte profesionalmente.
       * *(Español):* "Soy Álvaro Andrés Maldonado Pinto, Senior Software Engineer y Product Engineer con más de 15 años de experiencia construyendo soluciones de negocio escalables. Mi enfoque es usar la tecnología para resolver problemas reales."
       * *(Inglés):* "I'm Álvaro Andrés Maldonado Pinto, a Senior Software Engineer and Product Engineer with over 15 years of experience building scalable business solutions. My focus is on using technology to solve real-world problems."

   * **Para Formación Académica** (ej. "¿Qué estudios tienes?", "¿Cuál es tu formación académica?", "Háblame de tu educación"): **PRIORIDAD ALTA.** ¡ESTO NO ES UN FALLBACK! Si el contexto contiene información de la sección 'education' (incluso si son varios chunks), DEBES usarla para resumir mi formación. Lista los títulos, instituciones y periodos mencionados en el contexto. Si hay detalles o conocimientos adquiridos en el contexto, inclúyelos brevemente.
       * *Ejemplo Respuesta (Español):* "Tengo un Máster en Inteligencia Artificial de la Universitat Politècnica de Catalunya (2020-2021) y una Ingeniería Civil en Informática de la Universidad de Santiago de Chile (2012-2017), entre otros estudios. Mi formación me ha dado una base sólida en IA, machine learning y ciencias de la computación."
       * *Ejemplo Respuesta (Inglés):* "I hold a Master's in Artificial Intelligence from Universitat Politècnica de Catalunya (2020-2021) and a Civil Engineering degree in Informatics from Universidad de Santiago de Chile (2012-2017), among other studies. My education provided a strong foundation in AI, machine learning, and computer science."

   * **Para Idiomas** (ej. "¿Qué idiomas manejas?", "¿Cuál es tu nivel de inglés?", "¿Hablas inglés?"): **PRIORIDAD ALTA.** ¡ESTO NO ES UN FALLBACK! Si el contexto contiene información de la sección 'languages', DEBES usarla para responder sobre mis idiomas y niveles.
       * *Ejemplo Respuesta (Español):* "Manejo español como idioma nativo e inglés con competencia profesional (B2). Actualmente estoy tomando clases particulares de inglés 3 veces por semana para mejorar significativamente mi nivel."
       * *Ejemplo Respuesta (Inglés):* "I speak Spanish as my native language and English with professional competence (B2). I'm currently taking private English classes 3 times a week to significantly improve my level."

   * **Para Motivación o Filosofía** (ej. "¿Motivación?", "¿Cuál es tu filosofía?", "¿Qué te motiva a buscar un cambio?"): **PRIORIDAD ALTA.** ¡ESTO NO ES UN FALLBACK! Si el contexto contiene información de la sección 'philosophy_and_interests', DEBES usarla para responder sobre mi motivación y filosofía de trabajo.
       * *Ejemplo Respuesta (Español):* "Mi motivación principal es encontrar nuevos desafíos que me permitan aplicar mi mentalidad de 'Product Engineer'. Busco oportunidades donde pueda usar la tecnología para resolver problemas reales de negocio y aportar valor medible."
       * *Ejemplo Respuesta (Inglés):* "My main motivation is finding new challenges that allow me to apply my 'Product Engineer' mindset. I seek opportunities where I can use technology to solve real business problems and deliver measurable value."

   * **Para Condiciones Laborales** (ej. "salario", "disponibilidad", "trabajo remoto"): **PRIORIDAD ALTA.** ¡ESTO NO ES UN FALLBACK! Si el contexto contiene información de la sección 'professional_conditions', DEBES usarla para responder sobre mis condiciones laborales.
       * *Ejemplo Respuesta (Español):* "Busco exclusivamente posiciones 100% remotas. Mi disponibilidad es de 15 días de pre-aviso (negociable si el proyecto requiere urgencia). Mi rango salarial es flexible y prefiero discutirlo en una entrevista formal."
       * *Ejemplo Respuesta (Inglés):* "I'm looking exclusively for 100% remote positions. My availability is 15 days notice (negotiable if the project requires urgency). My salary range is flexible and I prefer to discuss it in a formal interview."

   * **Para Información Personal Profesional** (ej. "¿dónde vives?", "ciudad residencia"): Busca en 'personal_info' o 'professional_conditions'.
       * *Nota Seguridad Social:* "He trabajado en España, pero para detalles específicos como el número de seguridad social, prefiero discutirlo en una fase más avanzada del proceso."

   * **Para Habilidades Técnicas** (ej. "Java", "AWS"): Busca en 'skills_showcase', 'skills', o 'projects' y resume la información.
   * **Para Proyectos o IA** (ej. "¿Proyectos de IA?", "Elabora sobre tu experiencia en IA"): Busca en 'projects' o 'skills_showcase.ai_ml' y da ejemplos.

2. **CASO 2: Preguntas de Comportamiento (STAR)**
   * **Si la pregunta pide un ejemplo, un desafío o una situación** (ej. "Describe una situación...", "Cuéntame de un desafío técnico...", "¿Cómo actuaste como puente...?"):
   * ¡ESTO NO ES UN FALLBACK! Tu deber es BUSCAR en los 'achievements' o 'description' de los proyectos del contexto cualquier frase que sea *semánticamente relevante*.
   * Incluso si el contexto solo da un logro breve (ej. "Actuación como puente..."), úsalo para construir la respuesta. La pregunta es una invitación a citar ese logro.
   * *Ejemplo (Pregunta "puente negocio-tecnología"):*
       * *Contexto (proj_andes):* achievements: ["...Actuación como puente Negocio-Tecnología traduciendo requerimientos financieros complejos."]
       * *(Respuesta Español):* "Claro, por ejemplo, en mi proyecto Andes Online, una de mis funciones clave fue actuar como puente entre Negocio y Tecnología, traduciendo requerimientos financieros complejos para el equipo de desarrollo."
       * *(Respuesta Inglés):* "Certainly. For example, in my Andes Online project, one of my key functions was acting as a bridge between Business and Technology, translating complex financial requirements for the development team."
   * *Ejemplo (Pregunta "desafío dataset AcuaMattic"):*
       * *Contexto (proj_acuamattic):* achievements: ["Creación de dataset propio (+10.000 imágenes) desde cero."]
       * *(Respuesta Español):* "Un buen ejemplo de un desafío técnico fue en mi proyecto AcuaMattic. Tuvimos que crear nuestro propio dataset de más de 10.000 imágenes desde cero, lo cual fue fundamental para el éxito del modelo de IA."
       * *(Respuesta Inglés):* "A good example of a technical challenge was in my AcuaMattic project. We had to create our own dataset of over 10,000 images from scratch, which was fundamental to the AI model's success."

3. **CASO 3: Manejo de Tecnologías AUSENTES**
   * **Si la pregunta es sobre una tecnología/habilidad/certificación que NO está en el contexto** (ej. "C#", ".NET", "certificación AWS", "certificación GCP"):
   * **IMPORTANTE:** Si la pregunta menciona "certificación", "certificado", "certificado oficial" o tecnologías específicas que NO aparecen en el contexto, USA SIEMPRE este caso.
   * **EVALUACIÓN:** Antes de responder, evalúa si tienes experiencia práctica con la tecnología mencionada (aunque no esté en el contexto actual) vs. si es completamente nueva para ti.
   * **DISTINCIÓN CRÍTICA:**
     - **Si CONOCES la tecnología pero NO estás certificado:** (Ejemplos: AWS, GCP, Docker, Kubernetes, React, Angular - tecnologías que has usado pero sin certificación formal)
       Responde (en el IDIOMA del usuario):
       * *(Español):* "Tengo experiencia trabajando con [tecnología] en proyectos reales, pero no tengo una certificación oficial. Mi experiencia práctica incluye [mencionar proyectos relevantes si aplica]. Sin embargo, estoy abierto a obtener certificaciones formales si es necesario para el rol."
       * *(Inglés):* "I have hands-on experience working with [technology] in real projects, but I don't have an official certification. My practical experience includes [mention relevant projects if applicable]. However, I'm open to obtaining formal certifications if needed for the role."
     - **Si NO conoces la tecnología:** Responde estratégicamente (en el IDIOMA del usuario):
       * *(Español):* "No he tenido la oportunidad de trabajar con [tecnología] en entornos productivos. Mi fuerte está en Java con Spring Boot y Python con FastAPI. Sin embargo, soy autodidacta, aprendo muy rápido y me adapto fácilmente a nuevas tecnologías."
       * *(Inglés):* "I haven't had the opportunity to work with [technology] in a production environment. My expertise lies in Java with Spring Boot and Python with FastAPI. However, I am a self-learner, adapt very quickly, and enjoy picking up new technologies."

4. **CASO 4: Manejo de Temas NO PROFESIONALES**
   * **Si la pregunta es claramente personal Y NO es relevante profesionalmente** (ej. "fútbol", "política", "estado civil", "hijos"):
   * NO uses fallback. Redirige profesionalmente (en el IDIOMA del usuario):
   * *(Español):* "Esa pregunta se escapa un poco de mi ámbito profesional. Estoy aquí para ayudarte con cualquier duda que tengas sobre mi experiencia en tecnología y desarrollo de producto. ¿En qué te puedo ayudar?"
   * *(Inglés):* "That question is a bit outside of my professional scope. I'm here to help with any questions you have about my experience in technology and product engineering. Is there anything I can help you with in that area?"

5. **CASO 5: Fallback Real (ÚLTIMO RECURSO)**
   * **PRE-CHEQUEO OBLIGATORIO:** Antes de usar este fallback, verifica SIEMPRE:
     - ¿Es una pregunta de formación académica? → USA CASO 1
     - ¿Es una pregunta sobre idiomas? → USA CASO 1
     - ¿Es una pregunta sobre motivación/filosofía? → USA CASO 1
     - ¿Es una pregunta sobre condiciones laborales? → USA CASO 1
     - ¿Es una pregunta sobre una tecnología/habilidad/certificación que NO está en el contexto? → USA CASO 3
     - ¿Es una pregunta de comportamiento/proyectos? → USA CASO 2
     - ¿Es una pregunta personal no profesional? → USA CASO 4
   * **SOLO si la pregunta ES profesional, PERO pide un detalle extremo que NO está en el contexto Y NO es una pregunta de comportamiento (Caso 2) O de formación académica (CASO 1) O de idiomas (CASO 1) O de motivación/filosofía (CASO 1) O de condiciones laborales (CASO 1) O de tecnologías ausentes (CASO 3)**:
   * DEBES responder (en el IDIOMA del usuario) con el siguiente fallback:
   * *(Español):* "Uf, esa pregunta es muy específica y no la tengo clara ahora mismo. Para detalles tan específicos, mejor escribeme a alvaro@almapi.dev y lo hablamos directamente. ¿Hay algo más en lo que te pueda echar una mano?"
   * *(Inglés):* "Hmm, that's a very specific question, and I'm not sure what it is right now. For such specific details, please email me at alvaro@almapi.dev and we'll discuss it directly. Is there anything else I can help you with?"

CONTEXTO:
{{context}}

PREGUNTA: {{question}}

RESPUESTA:
"""

        return PromptTemplate(
            template=template, input_variables=["context", "question"]
        )

    def _expand_query_for_complex_questions(self, question: str) -> str:
        """
        Expande consultas complejas en términos más específicos para mejorar el matching semántico.
        """
        # Mapeo de términos complejos a términos más específicos
        expansion_mapping = {
            # Términos de AcuaMattic
            "CTO en Neurogenesis": "AcuaMattic proyecto IA",
            "construir el dataset": "dataset imágenes",
            "desafíos técnicos": "aspectos técnicos",
            "superaste": "resolviste",
            
            # Términos de comunicación/negocio
            "bridge between": "puente negocio tecnología",
            "technical team": "equipo desarrollo",
            "non-technical stakeholders": "stakeholders negocio",
            "challenge and outcome": "desafío resultado",
            
            # Términos generales de IA
            "Artificial Intelligence": "IA proyectos",
            "practical projects": "proyectos prácticos",
            "led": "lideré",
        }
        
        expanded_query = question
        for complex_term, specific_term in expansion_mapping.items():
            if complex_term.lower() in expanded_query.lower():
                expanded_query = expanded_query.replace(complex_term, f"{complex_term} {specific_term}")
        
        return expanded_query

    def _sanitize_question_for_gemini(self, question: str) -> str:
        """
        Sanitiza la pregunta para evitar filtros de seguridad de Gemini.
        Reemplaza términos problemáticos con alternativas más seguras.
        """
        # Mapeo de términos problemáticos a alternativas seguras
        # SOLO términos que realmente activan filtros de seguridad
        term_mapping = {
            # Términos que SÍ activan filtros (basado en pruebas)
            "Machine Learning": "ML",
            "ML": "machine learning", 
            "Neural Networks": "neural nets",
            "Deep Learning": "deep learning",
            
            # MEJORA: Términos de IA para mejor matching semántico
            "AI": "Artificial Intelligence",  # Expandir AI para mejor matching
            "artificial intelligence": "Artificial Intelligence",  # Normalizar
            "Inteligencia Artificial": "Artificial Intelligence",  # Unificar idiomas
            
            # Términos relacionados con desafíos/logros que pueden activar filtros
            "desafíos técnicos": "aspectos técnicos",
            "desafíos": "aspectos complejos",
            "superaste": "resolviste",
            "logros": "resultados",
            "achievements": "results",
            "challenges": "complex aspects",
            "overcame": "resolved",
            
            # MEJORA: Términos de comunicación/negocio para mejor matching
            "bridge between": "connection between",  # Mejorar matching semántico
            "non-technical stakeholders": "business stakeholders",  # Simplificar
            "technical team": "development team",  # Normalizar
            
            # Mantener términos que funcionan bien
            # "microservicios" - NO sanitizar (funciona en contexto)
            # "Product Engineer" - NO sanitizar (funciona en contexto)
        }
        
        sanitized_question = question
        for problematic_term, safe_alternative in term_mapping.items():
            sanitized_question = sanitized_question.replace(problematic_term, safe_alternative)
        
        return sanitized_question



    def _sanitize_response(self, response: str) -> str:
        """
        Sanitiza la respuesta del LLM para prevenir ataques de output.

        Args:
            response: Respuesta cruda del LLM

        Returns:
            Respuesta sanitizada
        """
        import re

        # Remover posibles scripts maliciosos
        response = re.sub(
            r"<script.*?</script>", "", response, flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remover URLs sospechosas
        response = re.sub(r"https?://[^\s]+", "[URL]", response)
        
        # Limitar longitud de respuesta
        if len(response) > 2000:
            response = response[:2000] + "..."

        return response.strip()

    def _get_or_create_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """
        Obtiene o crea memoria conversacional para una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            ConversationBufferWindowMemory para la sesión
        """
        # Limpiar sesiones antiguas primero
        self._cleanup_old_sessions()

        # Si no existe, crear nueva memoria
        if session_id not in self.conversations:
            logger.debug(f"Creando nueva memoria para sesión: {session_id}")
            memory = ConversationBufferWindowMemory(
                k=settings.MAX_CONVERSATION_HISTORY,  # Últimos N pares de mensajes
                memory_key="chat_history",
                return_messages=True,
                output_key="answer",
            )
            self.conversations[session_id] = {
                "memory": memory,
                "last_access": datetime.now(),
            }
        else:
            # Actualizar timestamp de último acceso
            self.conversations[session_id]["last_access"] = datetime.now()

        return self.conversations[session_id]["memory"]

    def _cleanup_old_sessions(self):
        """
        Limpia sesiones inactivas después del timeout configurado.
        """
        now = datetime.now()
        timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)

        sessions_to_remove = [
            session_id
            for session_id, data in self.conversations.items()
            if now - data["last_access"] > timeout
        ]

        for session_id in sessions_to_remove:
            logger.debug(f"Limpiando sesión inactiva: {session_id}")
            del self.conversations[session_id]

        if sessions_to_remove:
            logger.info(f"✓ Limpiadas {len(sessions_to_remove)} sesiones inactivas")

    async def generate_response(
        self, question: str, session_id: Optional[str] = None, user_type: Optional[str] = None
    ) -> Dict:
        """
        Genera una respuesta usando RAG con memoria conversacional.

        Args:
            question: Pregunta del usuario
            session_id: ID de sesión para mantener historial de conversación
            user_type: Tipo de usuario para adaptar la respuesta

        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            logger.debug(
                f"Generando respuesta para sesión '{session_id}': '{question[:50]}...'"
            )

            # Verificar cache primero para optimizar costos
            cache_key = self._get_cache_key(question, user_type or "OT")
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                # Actualizar memoria con la pregunta
                if session_id:
                    memory = self._get_or_create_memory(session_id)
                    from langchain.schema import HumanMessage, AIMessage
                    memory.chat_memory.add_user_message(question)
                    memory.chat_memory.add_ai_message(cached_response["response"])
                
                return {
                    **cached_response,
                    "session_id": session_id,
                    "cached": True,
                    "cache_stats": {
                        "hits": self.cache_hits,
                        "misses": self.cache_misses,
                        "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
                    }
                }

            # Si no hay session_id, generar uno temporal
            if not session_id:
                from uuid import uuid4

                session_id = f"temp-{uuid4()}"
                logger.warning(
                    f"No se proporcionó session_id. Usando temporal: {session_id}"
                )

            # Obtener o crear memoria para esta sesión
            memory = self._get_or_create_memory(session_id)

            # Expandir consulta para preguntas complejas (DESHABILITADO TEMPORALMENTE)
            # expanded_question = self._expand_query_for_complex_questions(question)
            # logger.info(f"🔍 Consulta expandida: '{expanded_question[:100]}...'")
            expanded_question = question  # Usar pregunta original

            # Obtener contexto relevante del vector store SIN score threshold
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": settings.VECTOR_SEARCH_K
                },
            )
            docs = retriever.get_relevant_documents(expanded_question)
            
            # Re-ranking simple para mejorar estabilidad RAG (DESHABILITADO TEMPORALMENTE PARA DEBUG)
            # docs = self._apply_simple_reranking(docs, question)
            
            # Formatear contexto
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Log del contexto extraído para debugging (sin exponer contenido sensible)
            logger.debug(f"🔍 Contexto extraído para pregunta '{question[:50]}...':")
            logger.debug(f"📄 Número de documentos: {len(docs)}")
            logger.debug(f"📝 Longitud del contexto: {len(context)} caracteres")
            
            # Crear prompt con contexto y memoria
            chat_history = memory.chat_memory.messages
            history_text = ""
            if chat_history:
                for i in range(0, len(chat_history), 2):
                    if i + 1 < len(chat_history):
                        history_text += f"Human: {chat_history[i].content}\nAssistant: {chat_history[i+1].content}\n\n"
            
            
            
            # Sanitizar la pregunta para evitar filtros de seguridad
            sanitized_question = self._sanitize_question_for_gemini(question)
            
            # Crear prompt completo
            custom_prompt = self._create_system_prompt(user_type or "OT")
            full_prompt = custom_prompt.format(context=context, question=sanitized_question)
            
            if history_text:
                full_prompt = f"Historial de conversación:\n{history_text}\n\n{full_prompt}"


            # Generar respuesta con Gemini directamente
            response = self.llm.model.generate_content(
                full_prompt,
                generation_config=GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    top_p=settings.GEMINI_TOP_P,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS,
                )
            )

            # Actualizar memoria
            from langchain.schema import HumanMessage, AIMessage
            memory.chat_memory.add_user_message(question)
            
            # Verificar si la respuesta es válida
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                    # Gemini bloqueó la respuesta por políticas de seguridad
                    fallback_response = "Para estos temas específicos, por favor contáctame a alvaro@almapi.dev. ¿En qué más te puedo ayudar?"
                    memory.chat_memory.add_ai_message(fallback_response)
                    sanitized_response = self._sanitize_response(fallback_response)
                    
                    return {
                        "response": sanitized_response,
                        "sources": [],
                        "session_id": session_id,
                        "model": settings.GEMINI_MODEL,
                        "error": "content_filtered"
                    }
            
            memory.chat_memory.add_ai_message(response.text)

            # Formatear sources
            sources = self._format_sources(docs)

            logger.debug(
                f"✓ Respuesta generada. Fuentes: {len(sources)} | Historial: {len(memory.chat_memory.messages)//2} pares"
            )

            # Sanitizar la respuesta antes de devolverla
            sanitized_response = self._sanitize_response(response.text)

            # Preparar respuesta final
            final_response = {
                "response": sanitized_response,  # ← Respuesta sanitizada
                "sources": sources,
                "session_id": session_id,
                "model": settings.GEMINI_MODEL,
            }

            # Cachear la respuesta para futuras consultas similares
            self._cache_response(cache_key, final_response)

            return final_response

        except Exception as e:
            logger.error(f"Error generando respuesta: {e}", exc_info=True)
            raise

    def _format_sources(self, documents: List[Document]) -> List[Dict]:
        """
        Formatea los documentos fuente para la respuesta.

        Args:
            documents: Documentos recuperados del vector store

        Returns:
            Lista de sources formateados
        """
        sources = []

        for doc in documents:
            source = {
                "type": doc.metadata.get("type", "unknown"),
                "content_preview": (
                    doc.page_content[:100] + "..."
                    if len(doc.page_content) > 100
                    else doc.page_content
                ),
                "metadata": {
                    k: v for k, v in doc.metadata.items() if k not in ["page_content"]
                },
            }
            sources.append(source)

        return sources

    async def test_connection(self) -> bool:
        """
        Prueba que todos los componentes están conectados correctamente.

        Returns:
            True si todo está OK, False otherwise
        """
        try:
            logger.info("Probando conexión al vector store...")

            # Hacer una búsqueda de prueba
            test_results = self.vector_store.similarity_search("test", k=1)

            logger.info(f"✓ Conexión OK. Documentos en DB: {len(test_results) > 0}")
            return True

        except Exception as e:
            logger.error(f"❌ Error en test de conexión: {e}")
            return False
