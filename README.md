# RAG ChatBot Backend

Backend Flask para el sistema RAG ChatBot de literatura científica en psicología.

## Despliegue Rápido

### Railway (Recomendado)
1. Fork este repositorio
2. Ve a [railway.app](https://railway.app)
3. "New Project" → "Deploy from GitHub repo"
4. Selecciona este repositorio
5. ¡Listo! Railway detectará automáticamente la configuración

### Render
1. Fork este repositorio  
2. Ve a [render.com](https://render.com)
3. "New" → "Web Service"
4. Conecta este repositorio
5. Render usará automáticamente `render.yaml`

### Vercel
1. Fork este repositorio
2. Ve a [vercel.com](https://vercel.com)
3. "New Project" → Import from GitHub
4. Selecciona este repositorio
5. Vercel usará automáticamente `vercel.json`

## Configuración Local

```bash
pip install -r requirements.txt
python initialize_rag.py
python src/main.py
```

## API Endpoints

- `GET /api/rag/health` - Estado del sistema
- `GET /api/rag/stats` - Estadísticas de la base de datos  
- `POST /api/rag/chat` - Conversación principal
- `POST /api/rag/search` - Búsqueda directa

## Datos

El sistema procesa un archivo JSON con 202 papers de psicología seleccionados, creando una base de datos vectorial con 24 documentos indexados.

## Tecnologías

- Flask + Flask-CORS
- ChromaDB (base de datos vectorial)
- SentenceTransformers (embeddings)
- Gunicorn (servidor WSGI)

