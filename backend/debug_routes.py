import sys
import os
sys.path.insert(0, os.getcwd())
import app
import app.main

print(f"App Module Path: {app.__file__}")
try:
    print(f"App Main Path: {app.main.__file__}")
except:
    print("app.main has no __file__")

from app.main import app as fastapi_app
print("Registered Routes:")
for route in fastapi_app.routes:
    methods = getattr(route, "methods", None)
    print(f"{route.path} {methods}")
