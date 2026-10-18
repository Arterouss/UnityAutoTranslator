import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import AutoTranslatorApp

if __name__ == "__main__":
    app = AutoTranslatorApp()
    app.mainloop()
