import json
import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import uuid

class RAGSystem:
    def __init__(self, data_path: str = None, persist_directory: str = None):
        """
        Inicializa el sistema RAG con ChromaDB y SentenceTransformers
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Configurar ChromaDB
        if persist_directory is None:
            persist_directory = os.path.join(os.path.dirname(__file__), '..', '..', 'chroma_db')
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="psychology_papers",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.data_path = data_path or os.path.join(os.path.dirname(__file__), '..', '..', 'data.json')
        self.papers_data = None
        
    def load_and_process_data(self):
        """
        Carga y procesa el archivo JSON de papers de psicología
        """
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.papers_data = json.load(f)
            
            # Verificar si ya hay documentos en la colección
            if self.collection.count() > 0:
                print(f"Base de datos ya contiene {self.collection.count()} documentos")
                return
            
            # Procesar papers seleccionados
            documents = []
            metadatas = []
            ids = []
            
            for i, paper in enumerate(self.papers_data.get('selected_papers', [])):
                # Crear texto combinado para embedding
                text_content = self._create_paper_text(paper)
                documents.append(text_content)
                
                # Crear metadata
                metadata = {
                    'title': paper.get('title', ''),
                    'authors': paper.get('authors', ''),
                    'year': paper.get('year', 0),
                    'doi': paper.get('doi', ''),
                    'keywords': ', '.join(paper.get('keywords', [])),
                    'citation_count': paper.get('citation_count', 0),
                    'conceptual_cluster': paper.get('conceptual_cluster', ''),
                    'final_score': paper.get('elm_scores', {}).get('final_score', 0),
                    'innovation_indicators': ', '.join(paper.get('innovation_indicators', [])),
                    'type': 'paper'
                }
                metadatas.append(metadata)
                ids.append(f"paper_{i}")
            
            # Agregar información de síntesis
            synthesis = self.papers_data.get('synthesis_insights', {})
            for key, value in synthesis.items():
                if isinstance(value, str) and len(value) > 50:
                    documents.append(value)
                    metadatas.append({
                        'title': f"Síntesis: {key.replace('_', ' ').title()}",
                        'type': 'synthesis',
                        'category': key
                    })
                    ids.append(f"synthesis_{key}")
            
            # Agregar metadatos de procesamiento
            processing_meta = self.papers_data.get('processing_metadata', {})
            semantic_analysis = processing_meta.get('semantic_analysis', {})
            
            # Agregar clusters conceptuales
            for i, cluster in enumerate(semantic_analysis.get('conceptual_clusters', [])):
                documents.append(f"Cluster conceptual: {cluster}")
                metadatas.append({
                    'title': f"Cluster: {cluster}",
                    'type': 'cluster',
                    'category': 'conceptual_cluster'
                })
                ids.append(f"cluster_{i}")
            
            # Agregar indicadores de innovación
            for i, indicator in enumerate(semantic_analysis.get('innovation_indicators', [])):
                documents.append(f"Indicador de innovación: {indicator}")
                metadatas.append({
                    'title': f"Innovación: {indicator}",
                    'type': 'innovation',
                    'category': 'innovation_indicator'
                })
                ids.append(f"innovation_{i}")
            
            # Generar embeddings y almacenar en ChromaDB
            print(f"Generando embeddings para {len(documents)} documentos...")
            embeddings = self.model.encode(documents, show_progress_bar=True)
            
            # Almacenar en ChromaDB
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Base de datos vectorial creada con {len(documents)} documentos")
            
        except Exception as e:
            print(f"Error al procesar datos: {str(e)}")
            raise
    
    def _create_paper_text(self, paper: Dict[str, Any]) -> str:
        """
        Crea un texto combinado del paper para embedding
        """
        text_parts = []
        
        # Título
        if paper.get('title'):
            text_parts.append(f"Título: {paper['title']}")
        
        # Autores
        if paper.get('authors'):
            text_parts.append(f"Autores: {paper['authors']}")
        
        # Abstract
        if paper.get('abstract'):
            text_parts.append(f"Resumen: {paper['abstract']}")
        
        # Keywords
        if paper.get('keywords'):
            text_parts.append(f"Palabras clave: {', '.join(paper['keywords'])}")
        
        # Cluster conceptual
        if paper.get('conceptual_cluster'):
            text_parts.append(f"Área: {paper['conceptual_cluster']}")
        
        # Contribución de síntesis
        if paper.get('synthesis_contribution'):
            text_parts.append(f"Contribución: {paper['synthesis_contribution']}")
        
        # Indicadores de innovación
        if paper.get('innovation_indicators'):
            text_parts.append(f"Innovaciones: {', '.join(paper['innovation_indicators'])}")
        
        return '\n\n'.join(text_parts)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Busca documentos similares usando embeddings
        """
        try:
            # Generar embedding de la consulta
            query_embedding = self.model.encode([query])
            
            # Buscar en ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Formatear resultados
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': 1 - results['distances'][0][i]  # Convertir distancia a similitud
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"Error en búsqueda: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos
        """
        try:
            count = self.collection.count()
            
            # Obtener algunos metadatos para estadísticas
            sample = self.collection.get(limit=count, include=['metadatas'])
            
            stats = {
                'total_documents': count,
                'papers': len([m for m in sample['metadatas'] if m.get('type') == 'paper']),
                'synthesis': len([m for m in sample['metadatas'] if m.get('type') == 'synthesis']),
                'clusters': len([m for m in sample['metadatas'] if m.get('type') == 'cluster']),
                'innovations': len([m for m in sample['metadatas'] if m.get('type') == 'innovation'])
            }
            
            return stats
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {str(e)}")
            return {'total_documents': 0}

