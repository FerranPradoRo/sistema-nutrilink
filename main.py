#!/usr/bin/env python3
"""
NutriLink - Sistema de Registro de Pacientes (Desktop)
"""
import sys, os
# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.gui import main as gui_main  # el GUI crea QApplication y carga QSS

if __name__ == "__main__":
    sys.exit(gui_main())