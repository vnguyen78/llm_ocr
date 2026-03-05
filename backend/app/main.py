from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.claims import router as claims_router
from app.api.audit import router as audit_router
from app.api.endpoints.review import router as review_router
import logging
from app.auditor.pii import PIIMasker

# Global PII Masking
logging.getLogger().addFilter(PIIMasker())
from app.database import engine, Base
from app.models.claim import Base as ClaimBase
from app.models.extraction import ExtractedData
from app.models.application import ClaimApplication # Ensure metadata is registered

# Create Tables
ClaimBase.metadata.create_all(bind=engine)

app = FastAPI(title="OCRAgent API")

from app.config import settings

# CORS Configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173", # Fallback for local dev if not in env
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development to avoid CORS issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.endpoints.applications import router as applications_router

# Include Routers
app.include_router(auth_router)
app.include_router(applications_router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(claims_router, prefix="/api/v1/claims", tags=["claims"])
app.include_router(audit_router, prefix="/api/v1/claims", tags=["audit"])
app.include_router(review_router, prefix="/api/v1/claims", tags=["review"])

# Note: Static /tiles mount removed for security. 
# Tiles are now served via authenticated endpoint in claims router.

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "OCRAgent Backend"}

import asyncio
from app.services.scheduler import process_pending_claims

@app.on_event("startup")
async def start_scheduler():
    async def scheduler_loop():
        logging.info("Scheduler started.")
        while True:
            await process_pending_claims()
            await asyncio.sleep(settings.EXTRACTION_POLL_INTERVAL_SECONDS)
    
    asyncio.create_task(scheduler_loop())
