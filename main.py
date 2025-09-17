#!/usr/bin/env python3
"""
NutriLink - Sistema de Registro de Pacientes para Consultorio Nutricionista
Versión: 1.0.0
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("NutriLink")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Equipo 3")
    app.setOrganizationDomain("nutrilink.local")
    
    # TODO: Initialize main window when GUI module is ready
    print("NutriLink - Sistema de Registro de Pacientes")
    print("Versión: 1.0.0")
    print("Estado: Entorno de desarrollo inicializado")
    
    # For now, just show a message and exit
    # Later this will be replaced with the main window
    return 0

if __name__ == "__main__":
    sys.exit(main())