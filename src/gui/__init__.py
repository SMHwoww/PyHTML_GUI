import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from gui.main_window import run_gui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False
    run_gui = None

__all__ = ['run_gui', 'HAS_GUI']
