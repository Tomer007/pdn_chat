# This file makes the app directory a Python package
# It's needed for the utility modules to import each other properly

# Import the create_app function from the parent app.py file
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from app import create_app
except ImportError:
    # Fallback: try to import directly from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.path.dirname(__file__), "..", "app.py"))
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    create_app = app_module.create_app 