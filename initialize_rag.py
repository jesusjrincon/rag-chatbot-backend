#!/usr/bin/env python3
"""
Script para inicializar el sistema RAG simplificado
"""

import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.simple_rag import SimpleRAGSystem

def main():
    """Función principal para inicializar el sistema RAG"""
    try:
        print("=== Inicializando Sistema RAG Simplificado ===")
        
        # Crear instancia del sistema RAG
        rag_system = SimpleRAGSystem()
        
        # Inicializar el sistema
        rag_system.initialize()
        
        # Verificar que funciona
        if rag_system.system_ready:
            stats = rag_system.get_stats()
            print(f"\n✅ Sistema inicializado exitosamente!")
            print(f"📊 Estadísticas:")
            print(f"   - Total de documentos: {stats['total_documents']}")
            print(f"   - Papers académicos: {stats['papers']}")
            print(f"   - Documentos de síntesis: {stats['synthesis']}")
            print(f"   - Clusters conceptuales: {stats['clusters']}")
            print(f"   - Indicadores de innovación: {stats['innovations']}")
            
            # Prueba rápida
            print(f"\n🧪 Realizando prueba de búsqueda...")
            test_results = rag_system.search("psicología positiva", n_results=3)
            print(f"   - Encontrados {len(test_results)} resultados para 'psicología positiva'")
            
            if test_results:
                print(f"   - Resultado principal: {test_results[0]['title']}")
                print(f"   - Similitud: {test_results[0]['similarity']:.3f}")
            
            print(f"\n🚀 Sistema listo para usar!")
            return True
        else:
            print("❌ Error: Sistema no se pudo inicializar correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

