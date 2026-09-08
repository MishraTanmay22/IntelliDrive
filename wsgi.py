import importlib.util
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_app_py = os.path.join(_current_dir, "app.py")

_spec = importlib.util.spec_from_file_location("intellidrive_main", _app_py)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

app = getattr(_mod, "app", None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
