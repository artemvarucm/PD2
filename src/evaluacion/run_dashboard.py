"""
Script para ejecutar el dashboard de análisis de tiempos de espera
"""

import os
import sys

def main():
    """Función principal que ejecuta el dashboard"""
    # Verificar si el archivo dashboard existe
    if not os.path.exists('dashboard_tiempos_espera.py'):
        print("Error: No se encuentra el archivo dashboard_tiempos_espera.py")
        sys.exit(1)
        
    # Verificar si existe el directorio assets
    if not os.path.exists('assets'):
        print("Creando directorio assets...")
        os.makedirs('assets')
        
    # Verificar si existe el archivo CSS
    if not os.path.exists('assets/styles.css'):
        print("Error: No se encuentra el archivo assets/styles.css")
        sys.exit(1)
        
    # Ejecutar el dashboard
    print("Iniciando el dashboard...")
    os.system('python dashboard_tiempos_espera.py')

if __name__ == "__main__":
    main() 