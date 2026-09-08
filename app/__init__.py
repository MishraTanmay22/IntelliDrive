import importlib.util
import os

# Make `app` available when importing the package `app` (e.g. for `gunicorn app:app`)
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_app_py = os.path.join(_parent_dir, "app.py")

if os.path.exists(_app_py):
    _spec = importlib.util.spec_from_file_location("intellidrive_main", _app_py)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    app = getattr(_mod, "app", None)
