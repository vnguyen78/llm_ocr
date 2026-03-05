import asyncio
import logging
import sys
import os

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from app.config import settings
from app.services.scheduler import process_pending_claims

async def main():
    print(f"DEBUG: Loaded Settings")
    print(f"DEBUG: LLM_BASE_URL (from config): {getattr(settings, 'LLM_BASE_URL', 'NOT_FOUND')}")
    print(f"DEBUG: LLM_API_BASE (old, should be gone): {getattr(settings, 'LLM_API_BASE', 'GONE')}")
    print(f"DEBUG: Confirmed .env override: {os.environ.get('LLM_BASE_URL')}")

    print("DEBUG: Running process_pending_claims()...")
    await process_pending_claims()
    print("DEBUG: Done.")

if __name__ == "__main__":
    asyncio.run(main())
