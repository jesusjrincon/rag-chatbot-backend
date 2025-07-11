import json
import os
import re
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SimpleRAGSystem:
    def __init__(self, data_file: str = "data.json"):
        self.data_file = data_file
        self.documents = []
        self.vectorizer = None
        self.document_vectors = None
        self.system_ready = False
        
    def initialize(self):
        """Inicializa el sistema RAG cargando y procesando los datos"""
        try:
            print("Inicializando sistema RAG...")
            
            # Cargar datos
            self._load_data()
            
            # Procesar documentos
            self._process_documents()
            
            # Crear vectores
            self._create_vectors()
            
            self.system_ready = True
            print(f"Sistema RAG inicializado exitosamente con {len(self.documents)} documentos")
            
        except Exception as e:
            print(f"Error inicializando sistema RAG: {e}")
            raise e
    
    def _load_data(self):
        """Carga los datos del archivo JSON"""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Archivo de datos no encontrado: {self.data_file}")
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraer documentos de diferentes secciones
        documents = []
        
        # Papers seleccionados
        if 'selected_papers' in data:
            for paper in data['selected_papers']:
                doc = {
                    'id': f"paper_{len(documents)}",
                    'title': paper.get('title', ''),
                    'content': f"{paper.get('title', '')} {paper.get('abstract', '')}",
                    'authors': paper.get('authors', []),
                    'year': paper.get('year', ''),
                    'type': 'paper',
                    'metadata': paper
                }
                documents.append(doc)
        
        # Documentos de síntesis
        if 'synthesis_documents' in data:
            for i, doc in enumerate(data['synthesis_documents']):
                document = {
                    'id': f"synthesis_{i}",
                    'title': doc.get('title', ''),
                    'content': f"{doc.get('title', '')} {doc.get('content', '')}",
                    'type': 'synthesis',
                    'metadata': doc
                }
                documents.append(document)
        
        # Clusters conceptuales
        if 'conceptual_clusters' in data:
            for i, cluster in enumerate(data['conceptual_clusters']):
                document = {
                    'id': f"cluster_{i}",
                    'title': cluster.get('name', ''),
                    'content': f"{cluster.get('name', '')} {cluster.get('description', '')} {' '.join(cluster.get('key_concepts', []))}",
                    'type': 'cluster',
                    'metadata': cluster
                }
                documents.append(document)
        
        # Indicadores de innovación
        if 'innovation_indicators' in data:
            for i, indicator in enumerate(data['innovation_indicators']):
                document = {
                    'id': f"innovation_{i}",
                    'title': indicator.get('indicator', ''),
                    'content': f"{indicator.get('indicator', '')} {indicator.get('description', '')}",
                    'type': 'innovation',
                    'metadata': indicator
                }
                documents.append(document)
        
        self.documents = documents
        print(f"Cargados {len(documents)} documentos")
    
    def _process_documents(self):
        """Procesa los documentos para mejorar la búsqueda"""
        for doc in self.documents:
            # Limpiar y normalizar el contenido
            content = doc['content']
            content = re.sub(r'\s+', ' ', content)  # Normalizar espacios
            content = content.strip()
            doc['processed_content'] = content
    
    def _create_vectors(self):
        """Crea vectores TF-IDF para los documentos"""
        texts = [doc['processed_content'] for doc in self.documents]
        
        # Configurar vectorizador TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
        # Crear vectores
        self.document_vectors = self.vectorizer.fit_transform(texts)
        print(f"Creados vectores TF-IDF con {self.document_vectors.shape[1]} características")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Busca documentos relevantes para la consulta"""
        if not self.system_ready:
            raise RuntimeError("Sistema RAG no inicializado")
        
        # Vectorizar la consulta
        query_vector = self.vectorizer.transform([query])
        
        # Calcular similitudes
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Obtener los mejores resultados
        top_indices = np.argsort(similarities)[::-1][:n_results]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.01:  # Umbral mínimo de similitud
                doc = self.documents[idx]
                result = {
                    'id': doc['id'],
                    'title': doc['title'],
                    'content': doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'],
                    'similarity': float(similarities[idx]),
                    'type': doc['type'],
                    'metadata': doc['metadata']
                }
                
                # Agregar información específica según el tipo
                if doc['type'] == 'paper':
                    result['authors'] = doc.get('authors', [])
                    result['year'] = doc.get('year', '')
                
                results.append(result)
        
        return results
    
    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Genera una respuesta basada en los resultados de búsqueda"""
        if not search_results:
            return "Lo siento, no encontré información relevante para tu consulta. Podrías reformular tu pregunta o preguntar sobre temas relacionados con psicología, neurociencia, bienestar mental, o metodologías de investigación."
        
        # Crear respuesta contextual
        response_parts = []
        
        # Introducción
        response_parts.append("Basándome en la literatura científica disponible, puedo proporcionarte la siguiente información:")
        
        # Información principal del resultado más relevante
        top_result = search_results[0]
        if top_result['type'] == 'paper':
            authors_str = ", ".join(top_result.get('authors', [])[:3])
            if len(top_result.get('authors', [])) > 3:
                authors_str += " et al."
            response_parts.append(f"\n\n**Investigación principal:** {top_result['title']}")
            if authors_str:
                response_parts.append(f"**Autores:** {authors_str} ({top_result.get('year', 'N/A')})")
        
        # Contenido relevante
        response_parts.append(f"\n{top_result['content']}")
        
        # Información adicional de otros resultados
        if len(search_results) > 1:
            response_parts.append("\n\n**Información relacionada:**")
            for result in search_results[1:3]:  # Máximo 2 resultados adicionales
                response_parts.append(f"\n• {result['title']}")
        
        return "".join(response_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        if not self.system_ready:
            return {"error": "Sistema no inicializado"}
        
        stats = {
            "total_documents": len(self.documents),
            "papers": len([d for d in self.documents if d['type'] == 'paper']),
            "synthesis": len([d for d in self.documents if d['type'] == 'synthesis']),
            "clusters": len([d for d in self.documents if d['type'] == 'cluster']),
            "innovations": len([d for d in self.documents if d['type'] == 'innovation']),
            "system_ready": self.system_ready
        }
        
        return stats

