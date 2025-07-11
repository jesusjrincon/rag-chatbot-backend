from flask import Blueprint, request, jsonify
from src.models.simple_rag import SimpleRAGSystem
import os

rag_bp = Blueprint('rag', __name__)

# Inicializar sistema RAG
rag_system = None

def get_rag_system():
    global rag_system
    if rag_system is None:
        rag_system = SimpleRAGSystem()
        if not rag_system.system_ready:
            try:
                rag_system.initialize()
            except Exception as e:
                print(f"Error inicializando RAG: {e}")
                return None
    return rag_system

@rag_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado del sistema"""
    try:
        rag = get_rag_system()
        if rag and rag.system_ready:
            stats = rag.get_stats()
            return jsonify({
                "status": "healthy",
                "system_ready": True,
                "documents_loaded": stats.get("total_documents", 0),
                "message": "Sistema RAG funcionando correctamente"
            })
        else:
            return jsonify({
                "status": "error",
                "system_ready": False,
                "message": "Sistema RAG no disponible"
            }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "system_ready": False,
            "message": f"Error en el sistema: {str(e)}"
        }), 500

@rag_bp.route('/stats', methods=['GET'])
def get_stats():
    """Endpoint para obtener estadísticas del sistema"""
    try:
        rag = get_rag_system()
        if rag and rag.system_ready:
            stats = rag.get_stats()
            return jsonify(stats)
        else:
            return jsonify({"error": "Sistema RAG no disponible"}), 503
    except Exception as e:
        return jsonify({"error": f"Error obteniendo estadísticas: {str(e)}"}), 500

@rag_bp.route('/chat', methods=['POST'])
def chat():
    """Endpoint principal para el chat RAG"""
    try:
        # Validar entrada
        if not request.json or 'message' not in request.json:
            return jsonify({"error": "Mensaje requerido"}), 400
        
        user_message = request.json['message'].strip()
        if not user_message:
            return jsonify({"error": "Mensaje no puede estar vacío"}), 400
        
        # Obtener sistema RAG
        rag = get_rag_system()
        if not rag or not rag.system_ready:
            return jsonify({
                "error": "Sistema RAG no disponible. Por favor, intenta más tarde."
            }), 503
        
        # Realizar búsqueda
        search_results = rag.search(user_message, n_results=5)
        
        # Generar respuesta
        response_text = rag.generate_response(user_message, search_results)
        
        # Preparar fuentes
        sources = []
        for result in search_results[:3]:  # Máximo 3 fuentes
            source = {
                "title": result['title'],
                "similarity": result['similarity'],
                "type": result['type']
            }
            
            # Agregar información específica según el tipo
            if result['type'] == 'paper':
                source['authors'] = result.get('authors', [])
                source['year'] = result.get('year', '')
            
            sources.append(source)
        
        return jsonify({
            "response": response_text,
            "sources": sources,
            "query": user_message
        })
        
    except Exception as e:
        print(f"Error en chat: {e}")
        return jsonify({
            "error": "Error interno del servidor. Por favor, intenta más tarde.",
            "details": str(e) if os.getenv('DEBUG') else None
        }), 500

@rag_bp.route('/search', methods=['POST'])
def search():
    """Endpoint para búsqueda directa"""
    try:
        if not request.json or 'query' not in request.json:
            return jsonify({"error": "Query requerido"}), 400
        
        query = request.json['query'].strip()
        if not query:
            return jsonify({"error": "Query no puede estar vacío"}), 400
        
        n_results = request.json.get('n_results', 5)
        n_results = min(max(n_results, 1), 20)  # Entre 1 y 20
        
        rag = get_rag_system()
        if not rag or not rag.system_ready:
            return jsonify({"error": "Sistema RAG no disponible"}), 503
        
        results = rag.search(query, n_results=n_results)
        
        return jsonify({
            "query": query,
            "results": results,
            "total_found": len(results)
        })
        
    except Exception as e:
        return jsonify({"error": f"Error en búsqueda: {str(e)}"}), 500

