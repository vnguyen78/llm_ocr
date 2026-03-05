import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.config import settings

print(f"TRIGGER_EXTRACTION_IMMEDIATELY: {settings.TRIGGER_EXTRACTION_IMMEDIATELY}")
print(f"LLM_BASE_URL: {settings.LLM_BASE_URL}")
