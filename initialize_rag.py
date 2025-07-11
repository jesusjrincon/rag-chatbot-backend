#!/usr/bin/env python3
"""
Script para inicializar la base de datos vectorial RAG
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

from src.models.rag_system import RAGSystem

def main():
    print("Inicializando sistema RAG...")
    
    try:
        # Crear instancia del sistema RAG
        rag = RAGSystem()
        
        # Cargar y procesar datos
        print("Cargando y procesando datos del JSON...")
        rag.load_and_process_data()
        
        # Obtener estadísticas
        stats = rag.get_stats()
        print(f"\nEstadísticas de la base de datos:")
        print(f"- Total de documentos: {stats['total_documents']}")
        print(f"- Papers académicos: {stats['papers']}")
        print(f"- Documentos de síntesis: {stats['synthesis']}")
        print(f"- Clusters conceptuales: {stats['clusters']}")
        print(f"- Indicadores de innovación: {stats['innovations']}")
        
        # Prueba de búsqueda
        print(f"\nPrueba de búsqueda:")
        test_query = "psicología positiva y bienestar"
        results = rag.search(test_query, n_results=3)
        
        print(f"Consulta: '{test_query}'")
        print(f"Resultados encontrados: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['metadata'].get('title', 'Sin título')}")
            print(f"   Similitud: {result['similarity']:.3f}")
            print(f"   Tipo: {result['metadata'].get('type', 'desconocido')}")
            if result['metadata'].get('type') == 'paper':
                print(f"   Autores: {result['metadata'].get('authors', 'N/A')}")
                print(f"   Año: {result['metadata'].get('year', 'N/A')}")
        
        print(f"\n✅ Sistema RAG inicializado correctamente!")
        
    except Exception as e:
        print(f"❌ Error al inicializar sistema RAG: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

