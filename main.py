#!/usr/bin/env python3
import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
from src.gui import main as gui_main

if __name__ == "__main__":
    raise SystemExit(gui_main())