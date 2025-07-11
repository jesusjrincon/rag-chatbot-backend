import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import app

# Vercel necesita que la aplicación se llame 'app'
if __name__ == "__main__":
    app.run()

