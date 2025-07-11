from flask import Blueprint, request, jsonify
from src.models.rag_system import RAGSystem
import os

rag_bp = Blueprint('rag', __name__)

# Instancia global del sistema RAG
rag_system = None

def get_rag_system():
    """
    Obtiene la instancia del sistema RAG (singleton)
    """
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem()
        # Verificar si la base de datos ya está inicializada
        if rag_system.collection.count() == 0:
            rag_system.load_and_process_data()
    return rag_system

@rag_bp.route('/search', methods=['POST'])
def search():
    """
    Endpoint para buscar documentos similares
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Se requiere el campo "query"'}), 400
        
        query = data['query']
        n_results = data.get('n_results', 5)
        
        if not query.strip():
            return jsonify({'error': 'La consulta no puede estar vacía'}), 400
        
        # Obtener sistema RAG
        rag = get_rag_system()
        
        # Realizar búsqueda
        results = rag.search(query, n_results=n_results)
        
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error en la búsqueda: {str(e)}'}), 500

@rag_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal para conversación tipo ChatGPT
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Se requiere el campo "message"'}), 400
        
        user_message = data['message']
        
        if not user_message.strip():
            return jsonify({'error': 'El mensaje no puede estar vacío'}), 400
        
        # Obtener sistema RAG
        rag = get_rag_system()
        
        # Buscar documentos relevantes
        search_results = rag.search(user_message, n_results=3)
        
        # Crear contexto a partir de los resultados
        context_parts = []
        sources = []
        
        for result in search_results:
            metadata = result['metadata']
            document = result['document']
            similarity = result['similarity']
            
            # Solo incluir resultados con similitud razonable
            if similarity > 0.1:
                context_parts.append(document)
                
                # Crear información de fuente
                source_info = {
                    'title': metadata.get('title', 'Sin título'),
                    'type': metadata.get('type', 'desconocido'),
                    'similarity': round(similarity, 3)
                }
                
                if metadata.get('type') == 'paper':
                    source_info.update({
                        'authors': metadata.get('authors', 'N/A'),
                        'year': metadata.get('year', 'N/A'),
                        'doi': metadata.get('doi', 'N/A')
                    })
                
                sources.append(source_info)
        
        # Crear respuesta contextualizada
        if context_parts:
            context = '\n\n'.join(context_parts[:3])  # Limitar contexto
            
            # Generar respuesta basada en el contexto
            response = generate_contextual_response(user_message, context, sources)
        else:
            response = {
                'answer': 'Lo siento, no encontré información relevante en la base de datos para responder tu pregunta. Podrías reformular tu consulta o preguntar sobre temas relacionados con psicología, bienestar, neurociencia, o los estudios incluidos en esta revisión.',
                'context_used': False
            }
        
        return jsonify({
            'user_message': user_message,
            'response': response['answer'],
            'sources': sources,
            'context_used': response.get('context_used', True)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error en el chat: {str(e)}'}), 500

def generate_contextual_response(user_message: str, context: str, sources: list) -> dict:
    """
    Genera una respuesta contextualizada basada en los documentos encontrados
    """
    try:
        # Análisis simple del tipo de pregunta
        question_lower = user_message.lower()
        
        # Respuestas específicas según el tipo de pregunta
        if any(word in question_lower for word in ['qué es', 'define', 'definición', 'concepto']):
            response_type = 'definition'
        elif any(word in question_lower for word in ['cómo', 'método', 'proceso', 'procedimiento']):
            response_type = 'process'
        elif any(word in question_lower for word in ['por qué', 'causa', 'razón', 'motivo']):
            response_type = 'explanation'
        elif any(word in question_lower for word in ['cuándo', 'año', 'fecha', 'tiempo']):
            response_type = 'temporal'
        elif any(word in question_lower for word in ['quién', 'autor', 'investigador']):
            response_type = 'author'
        else:
            response_type = 'general'
        
        # Generar respuesta basada en el contexto
        answer = create_answer_from_context(user_message, context, sources, response_type)
        
        return {
            'answer': answer,
            'context_used': True
        }
        
    except Exception as e:
        return {
            'answer': f'Error al generar respuesta: {str(e)}',
            'context_used': False
        }

def create_answer_from_context(question: str, context: str, sources: list, response_type: str) -> str:
    """
    Crea una respuesta estructurada basada en el contexto
    """
    # Extraer información clave del contexto
    paper_sources = [s for s in sources if s['type'] == 'paper']
    synthesis_sources = [s for s in sources if s['type'] == 'synthesis']
    
    answer_parts = []
    
    # Introducción basada en el tipo de pregunta
    if response_type == 'definition':
        answer_parts.append("Según la literatura científica disponible:")
    elif response_type == 'process':
        answer_parts.append("Los estudios indican que:")
    elif response_type == 'explanation':
        answer_parts.append("La investigación sugiere que:")
    elif response_type == 'temporal':
        answer_parts.append("En cuanto al aspecto temporal:")
    elif response_type == 'author':
        answer_parts.append("Los investigadores identificados incluyen:")
    else:
        answer_parts.append("Basándome en la información disponible:")
    
    # Extraer información relevante del contexto
    context_summary = summarize_context(context, response_type)
    answer_parts.append(context_summary)
    
    # Agregar información de fuentes
    if paper_sources:
        answer_parts.append("\\n**Estudios relevantes:**")
        for source in paper_sources[:2]:  # Limitar a 2 estudios
            year = source.get('year', 'N/A')
            authors = source.get('authors', 'N/A')
            if authors != 'N/A' and len(authors) > 100:
                # Truncar lista de autores si es muy larga
                authors = authors.split(',')[0] + " et al."
            answer_parts.append(f"- {source['title']} ({year}) - {authors}")
    
    if synthesis_sources:
        answer_parts.append("\\n**Información adicional de síntesis:**")
        for source in synthesis_sources[:1]:  # Limitar a 1 síntesis
            answer_parts.append(f"- {source['title']}")
    
    return '\\n\\n'.join(answer_parts)

def summarize_context(context: str, response_type: str) -> str:
    """
    Crea un resumen del contexto basado en el tipo de respuesta
    """
    # Dividir el contexto en secciones
    sections = context.split('\\n\\n')
    
    # Extraer información clave
    key_info = []
    
    for section in sections:
        if len(section.strip()) > 50:  # Ignorar secciones muy cortas
            # Buscar información específica según el tipo de respuesta
            if response_type == 'definition' and ('concepto' in section.lower() or 'definición' in section.lower()):
                key_info.append(section[:300] + '...' if len(section) > 300 else section)
            elif response_type == 'process' and ('método' in section.lower() or 'proceso' in section.lower()):
                key_info.append(section[:300] + '...' if len(section) > 300 else section)
            elif response_type == 'author' and ('autor' in section.lower() or 'investigador' in section.lower()):
                key_info.append(section[:200] + '...' if len(section) > 200 else section)
            elif len(key_info) < 2:  # Agregar información general si no hay específica
                # Extraer las primeras oraciones más informativas
                sentences = section.split('.')
                for sentence in sentences[:2]:
                    if len(sentence.strip()) > 30:
                        key_info.append(sentence.strip() + '.')
                        break
    
    if not key_info:
        # Si no se encontró información específica, usar las primeras líneas del contexto
        first_section = sections[0] if sections else context
        key_info.append(first_section[:400] + '...' if len(first_section) > 400 else first_section)
    
    return ' '.join(key_info[:2])  # Limitar a 2 elementos de información clave

@rag_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Endpoint para obtener estadísticas de la base de datos
    """
    try:
        rag = get_rag_system()
        stats = rag.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Error obteniendo estadísticas: {str(e)}'}), 500

@rag_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado del sistema
    """
    try:
        rag = get_rag_system()
        count = rag.collection.count()
        return jsonify({
            'status': 'healthy',
            'documents_loaded': count,
            'system_ready': count > 0
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

