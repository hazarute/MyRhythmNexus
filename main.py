import os
import runpy

# Compatibility wrapper so `uvicorn main:app` works even if package imports
# would fail in some container setups. This executes `license_server/main.py`
# as a script and exposes the `app` object.
module_path = os.path.join(os.path.dirname(__file__), "license_server", "main.py")
module_globals = runpy.run_path(module_path)
app = module_globals.get("app")
