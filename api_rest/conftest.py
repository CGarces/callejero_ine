"""
Configuración de pytest para los tests de la API REST
"""

import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al path para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
