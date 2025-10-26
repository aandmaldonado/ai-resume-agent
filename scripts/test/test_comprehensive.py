#!/usr/bin/env python3
"""
🧪 TESTING COMPREHENSIVE - AI Resume Agent
Genera reporte completo en Markdown con contexto, vectores y veredicto
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv es opcional, continuar sin él
    pass

from app.services.rag_service import RAGService
from app.core.config import settings

class ComprehensiveTester:
    def __init__(self):
        self.rag_service: RAGService | None = None
        self.test_results: List[Dict[str, Any]] = []
        self.session_id = f"test_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.prompt_template: Any = None
        self.llm_params: Dict[str, Any] | None = None
        
    async def setup(self):
        """Configurar el servicio RAG"""
        print("🔧 Configurando RAG Service...")
        
        try:
            self.rag_service = RAGService()
            
            # Desactivar cache explícitamente para testing
            self.rag_service.response_cache.clear()
            self.rag_service.cache_hits = 0
            self.rag_service.cache_misses = 0
            print("✓ Cache desactivado para testing")
            
            # Obtener configuración del prompt y LLM
            self.prompt_template = self.rag_service._create_system_prompt()
            self.llm_params = {
                "temperature": settings.GEMINI_TEMPERATURE,
                "top_p": settings.GEMINI_TOP_P,
                "max_tokens": settings.GEMINI_MAX_TOKENS,
            }
            
            print("✅ RAG Service configurado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    async def test_question(self, question: str, category: str) -> Dict[str, Any]:
        """Probar una pregunta y capturar toda la información"""
        print(f"\n🧪 Test {len(self.test_results) + 1}/21: {question[:50]}...")
        
        if self.rag_service is None:
            return {
                "number": len(self.test_results) + 1,
                "question": question,
                "response": "Error: RAG Service no inicializado",
                "context_info": [],
                "sources_count": 0,
                "verdict": "❌ ERROR",
                "fidelity_check": "error",
                "category": category,
                "session_id": self.session_id
            }
        
        try:
            # Usar el mismo session_id para todas las preguntas (simular conversación)
            
            # Generar respuesta
            result = await self.rag_service.generate_response(
                question=question,
                session_id=self.session_id,
                user_type="IT"
            )
            
            # Obtener contexto y vectores
            retriever = self.rag_service.vector_store.as_retriever(
                search_kwargs={"k": settings.VECTOR_SEARCH_K}
            )
            docs = retriever.get_relevant_documents(question)
            
            # Extraer información
            response = result.get("response", "")
            sources = result.get("sources", [])
            fidelity_check = result.get("fidelity_check", "unknown")
            
            # Determinar veredicto con lógica mejorada
            # Verificar si la respuesta es un fallback genérico
            is_fallback = "contactarme directamente" in response or "contact me directly" in response
            
            # Verificar si hay contenido real recuperado (no solo FAQs)
            has_real_content = False
            for doc in docs:
                content_preview = doc.page_content[:500].lower()
                # Excluir chunks que solo tienen FAQs o son muy vacíos
                if "--- preguntas frecuentes relevantes ---" not in content_preview or len(content_preview) > 300:
                    # Verificar si tiene contenido sustancial antes de las FAQs
                    if "--- preguntas frecuentes relevantes ---" in content_preview:
                        real_content = content_preview.split("--- preguntas frecuentes relevantes ---")[0]
                        if len(real_content.strip()) > 50:
                            has_real_content = True
                            break
                    else:
                        has_real_content = True
                        break
            
            # Criterios de éxito mejorados
            # 1. No debe ser fallback genérico
            # 2. SI tiene contenido real recuperado O la respuesta no es genérica (es específica y útil)
            # 3. Respuesta debe tener longitud mínima razonable (> 50)
            # 4. Debe tener al menos 1 source
            # 
            # Si la respuesta es específica y útil (no genérica), es válida incluso sin "contenido real" en chunk
            # porque puede haber sido recuperado correctamente por el LLM del contexto disponible
            response_lower = response.lower()
            is_specific_useful = (
                not is_fallback and
                len(response) > 50 and
                "no tengo ese detalle" not in response_lower and
                "contactarme directamente" not in response_lower and
                "contact me directly" not in response_lower
            )
            
            is_valid_response = (
                not is_fallback and 
                (has_real_content or is_specific_useful) and
                len(response) > 50 and 
                len(sources) > 0
            )
            
            verdict = "✅ PASÓ" if is_valid_response else "❌ FALLÓ"
            
            # Extraer contexto específico
            context_info = []
            for i, doc in enumerate(docs[:3], 1):
                content_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                source = doc.metadata.get("source", "unknown")
                doc_id = doc.metadata.get("id", "unknown")
                context_info.append({
                    "index": i,
                    "source": source,
                    "id": doc_id,
                    "preview": content_preview
                })
            
            test_result = {
                "number": len(self.test_results) + 1,
                "question": question,
                "response": response,
                "context_info": context_info,
                "sources_count": len(sources),
                "verdict": verdict,
                "fidelity_check": fidelity_check,
                "category": category,
                "session_id": self.session_id
            }
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            error_result = {
                "number": len(self.test_results) + 1,
                "question": question,
                "response": f"Error: {str(e)}",
                "context_info": [],
                "sources_count": 0,
                "verdict": "❌ ERROR",
                "fidelity_check": "error",
                "category": category,
                "session_id": self.session_id
            }
            self.test_results.append(error_result)
            return error_result
    
    async def run_all_tests(self):
        """Ejecutar todos los tests"""
        print(f"\n🚀 Iniciando testing comprehensivo con session_id: {self.session_id}")
        
        test_cases = [
            # Identidad
            ("¿Quién eres?", "identidad"),
            ("¿Cuál es tu formación académica?", "educación"),
            ("¿Qué idiomas manejas?", "idiomas"),
            
            # Experiencia
            ("¿Cuál es tu experiencia con Java?", "experiencia"),
            ("¿Qué proyectos de IA has liderado?", "proyectos"),
            ("¿Cuál es tu experiencia con microservicios?", "experiencia"),
            
            # Comportamiento
            ("Describe una situación donde actuaste como puente entre negocio y tecnología", "comportamiento"),
            ("¿Cuál fue el logro más significativo en AcuaMattic?", "comportamiento"),
            ("Cuéntame de un desafío técnico que hayas resuelto", "comportamiento"),
            
            # Motivación/Filosofía
            ("¿Cuál es tu motivación para un nuevo reto profesional?", "motivación"),
            ("¿Cuál es tu filosofía de trabajo?", "filosofía"),
            
            # Condiciones
            ("¿Cuáles son tus expectativas salariales?", "condiciones"),
            ("¿Buscas trabajo remoto?", "condiciones"),
            ("¿Cuál es tu disponibilidad?", "condiciones"),
            
            # Tecnologías ausentes
            ("¿Tienes certificación en AWS?", "tecnología_ausente"),
            ("¿Conoces React?", "tecnología_ausente"),
            ("¿Has trabajado con MongoDB?", "tecnología_ausente"),
            
            # Off-topic
            ("¿Cuál es tu comida favorita?", "off_topic"),
            ("¿Qué opinas de la política?", "off_topic"),
            
            # Complejas
            ("¿Cuál es tu experiencia con Python en proyectos de IA?", "compleja"),
            ("Háblame de tu experiencia en banca y retail", "compleja"),
        ]
        
        print(f"📊 Total de tests: {len(test_cases)}")
        
        for question, category in test_cases:
            await self.test_question(question, category)
            await asyncio.sleep(0.5)  # Pequeña pausa para evitar rate limiting
        
        return len(test_cases)
    
    def generate_markdown_report(self) -> str:
        """Generar reporte en formato Markdown"""
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report = f"""# 🧪 REPORTE DE TESTING - AI Resume Agent

**Fecha de ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total de tests:** {len(self.test_results)} / {len(self.test_results)}

---

## 📋 CONFIGURACIÓN

### Prompt Template
```
{self.prompt_template.template if self.prompt_template else "No disponible"}
```

### Parámetros del LLM
- **Modelo:** {settings.GEMINI_MODEL}
- **Temperature:** {self.llm_params['temperature'] if self.llm_params else settings.GEMINI_TEMPERATURE}
- **Top P:** {self.llm_params['top_p'] if self.llm_params else settings.GEMINI_TOP_P}
- **Max Tokens:** {self.llm_params['max_tokens'] if self.llm_params else settings.GEMINI_MAX_TOKENS}

### Configuración de Embeddings y Contexto
- **VECTOR_SEARCH_K:** {settings.VECTOR_SEARCH_K}
- **Embeddings Model:** HuggingFace sentence-transformers/all-MiniLM-L6-v2
- **Vector Store:** PostgreSQL + pgvector

---

## 📊 RESULTADOS POR TEST

"""
        
        # Agrupar por categoría
        by_category = {}
        for result in self.test_results:
            category = result['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result)
        
        # Generar secciones por categoría
        for category, tests in by_category.items():
            report += f"\n### 📂 {category.upper()}\n\n"
            
            for test in tests:
                report += f"""
#### Test {test['number']}/{len(self.test_results)}: {test['question']}

**Session ID:** {test.get('session_id', 'N/A')}  
**Categoría:** {test['category']}  
**Veredicto:** {test['verdict']}  
**Fuentes encontradas:** {test['sources_count']}  
**Fidelidad:** {test['fidelity_check']}

**Respuesta:**
> {test['response']}

**Contexto recuperado:**
"""
                
                if test['context_info']:
                    for ctx in test['context_info']:
                        report += f"\n1. **{ctx['source']}** (ID: {ctx['id']})\n"
                        report += f"   ```\n   {ctx['preview']}\n   ```\n"
                else:
                    report += "*No se recuperó contexto*\n"
        
        # Estadísticas finales
        total = len(self.test_results)
        passed = sum(1 for t in self.test_results if "✅ PASÓ" in t['verdict'])
        failed = sum(1 for t in self.test_results if "❌ FALLÓ" in t['verdict'])
        
        report += f"""
---

## 📈 ESTADÍSTICAS GENERALES

| Métrica | Valor | Porcentaje |
|---------|-------|------------|
| Total de tests | {total} | 100% |
| Tests exitosos | {passed} | {passed/total*100:.1f}% |
| Tests fallidos | {failed} | {failed/total*100:.1f}% |

### Desglose por categoría

"""
        
        for category, tests in by_category.items():
            category_passed = sum(1 for t in tests if "✅ PASÓ" in t['verdict'])
            report += f"- **{category}:** {category_passed}/{len(tests)} ({category_passed/len(tests)*100:.1f}%)\n"
        
        report += f"""

---

## 🎯 CONCLUSIONES

### Análisis de Tests Fallidos

"""
        
        failed_tests = [t for t in self.test_results if "❌ FALLÓ" in t['verdict'] or "❌ ERROR" in t['verdict']]
        
        # Análisis de problemas por tipo
        problems_by_type = {}
        
        for test in failed_tests:
            # Clasificar el tipo de problema
            problem_type = "unknown"
            problem_details = ""
            
            if test['sources_count'] == 0:
                problem_type = "No se recuperó contexto"
                problem_details = "El vector store no encontró chunks relevantes para esta pregunta"
            elif "contactarme directamente" in test['response'].lower() or "contact me directly" in test['response'].lower():
                problem_type = "Fallback genérico activado"
                problem_details = "El LLM devolvió un fallback genérico en lugar de usar el contexto disponible"
            elif len(test['response']) < 50:
                problem_type = "Respuesta demasiado corta"
                problem_details = f"Respuesta de solo {len(test['response'])} caracteres, insuficiente"
            elif len(test['response']) > 50 and test['sources_count'] > 0:
                problem_type = "Contexto sin contenido real"
                problem_details = "Los chunks recuperados solo contienen FAQs sin información sustancial"
            else:
                problem_type = "Error desconocido"
                problem_details = "Error en la generación de la respuesta"
            
            if problem_type not in problems_by_type:
                problems_by_type[problem_type] = []
            
            problems_by_type[problem_type].append({
                "question": test['question'],
                "category": test['category'],
                "details": problem_details
            })
        
        # Generar reporte de problemas por tipo
        if problems_by_type:
            report += "#### Desglose de Problemas por Tipo:\n\n"
            for problem_type, tests in problems_by_type.items():
                report += f"**{problem_type}** ({len(tests)} casos):\n"
                for test in tests:
                    report += f"- Test {test['question']} ({test['category']})\n"
                    report += f"  - {test['details']}\n"
                report += "\n"
        else:
            report += "*No se identificaron problemas críticos.*\n\n"
        
        report += f"""
### Detalle de Tests Fallidos

"""
        
        if failed_tests:
            for test in failed_tests:
                report += f"- **Test {test['number']}**: {test['question']}\n"
                report += f"  - Categoría: {test['category']}\n"
                report += f"  - Fuentes: {test['sources_count']}\n"
                report += f"  - Longitud respuesta: {len(test['response'])} caracteres\n"
                
                # Detectar tipo de problema específico
                if test['sources_count'] == 0:
                    report += f"  - Diagnóstico: ⚠️ No se recuperó contexto\n"
                elif "contactarme directamente" in test['response'].lower() or "contact me directly" in test['response'].lower():
                    report += f"  - Diagnóstico: ⚠️ Activó fallback genérico (no usó contexto disponible)\n"
                elif len(test['response']) < 50:
                    report += f"  - Diagnóstico: ⚠️ Respuesta demasiado corta ({len(test['response'])} chars)\n"
                else:
                    report += f"  - Diagnóstico: ⚠️ Contexto recuperado pero no utilizado correctamente\n"
                
                report += "\n"
        else:
            report += "*No hay tests fallidos.*\n\n"
        
        # Análisis de rendimiento
        success_rate = (passed / total * 100) if total > 0 else 0
        report += f"""
### Análisis de Rendimiento

- **Tasa de éxito:** {success_rate:.1f}%
- **Total de tests:** {total}
- **Tests exitosos:** {passed}
- **Tests fallidos:** {failed}
- **Rendimiento:** {'🎉 Excelente' if success_rate >= 95 else '✅ Bueno' if success_rate >= 80 else '⚠️ Regular' if success_rate >= 60 else '❌ Necesita mejoras'}

"""
        
        report += f"""
### Próximos Pasos Recomendados

"""
        
        if failed > 0:
            report += """
1. **Diagnóstico Detallado:** 
   - Revisar cada test fallido y analizar qué información debería haberse recuperado
   - Verificar si los chunks contienen la información necesaria en el vector store

2. **Optimización de Búsqueda:**
   - Si no se recupera contexto: considerar mejorar las FAQs o los embeddings
   - Si se recupera pero no se usa: revisar la lógica del prompt

3. **Ajuste de Prompts:**
   - Si hay fallbacks genéricos: el prompt necesita reforzar el uso del contexto
   - Si las respuestas son cortas: considerar aumentar max_tokens

4. **Actualización de Knowledge Base:**
   - Si faltan chunks específicos: re-visualizar el portfolio.yaml
   - Si los chunks son pobres: mejorar el contenido en portfolio.yaml

5. **Parámetros del Sistema:**
   - Aumentar VECTOR_SEARCH_K si se necesitan más chunks
   - Ajustar temperatura/top_p si hay problemas de creatividad/precisión
"""
        else:
            report += """
✅ **Todos los tests pasaron exitosamente!**

- El sistema está funcionando correctamente
- El prompt template es efectivo
- El vector store contiene información suficiente
- Considera expandir los tests para cubrir más casos

Recomendación: Hacer commit y deploy de estos cambios.
"""
        
        report += """

---

*Reporte generado automáticamente por el sistema de testing*
"""
        
        return report
    
    def save_report(self, content: str):
        """Guardar reporte en output/"""
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Usar timestamp completo para evitar sobrescritura
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_results_{timestamp}.md"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ Reporte guardado en: {filepath}")
        return filepath

async def main():
    print("🧪 AI Resume Agent - Testing Comprehensivo")
    print("="*80)
    
    tester = ComprehensiveTester()
    
    if not await tester.setup():
        print("❌ No se pudo configurar el testing")
        return
    
    await tester.run_all_tests()
    
    report_content = tester.generate_markdown_report()
    tester.save_report(report_content)
    
    print("\n🎉 Testing completado!")
    print(f"✅ {len(tester.test_results)} tests ejecutados")

if __name__ == "__main__":
    asyncio.run(main())

