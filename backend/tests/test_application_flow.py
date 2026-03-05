import asyncio
import httpx
import logging
import sys
import uuid
import os
from PIL import Image

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Application Flow Test")
    
    # 1. Create Dummy Images
    files_to_create = ["test_doc_1.jpg", "test_doc_2.jpg"]
    for f in files_to_create:
        img = Image.new('RGB', (100, 100), color = 'white')
        img.save(f)
    
    try:
        import app.main
        logger.info(f"Imported app from: {app.main.__file__}")
        from app.main import app
        from httpx import ASGITransport

        # Debug: Print Routes
        logger.info("Registered Routes:")
        for route in app.routes:
            logger.info(f" -> {route.path} [{route.name}]")

        # 2. Ingest Application (Batch Upload)
        logger.info("Step 1: Ingesting Application (2 files)...")
        
        # Prepare multipart upload
        # httpx expects list of tuples for multiple files with same key
        files = []
        for f in files_to_create:
            files.append(("files", (f, open(f, "rb"), "image/jpeg")))
            
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/applications/ingest", files=files)
            
        if response.status_code != 200:
            logger.error(f"Ingestion failed: {response.status_code} {response.text}")
            sys.exit(1)
            
        data = response.json()
        app_id = data["id"]
        logger.info(f" -> Ingestion Success. App ID: {app_id}")
        logger.info(f" -> Response Data: {data}")
        
        assert data["status"] == "PROCESSING"
        # Note: Response model might just be summary, check if it includes documents or count
        # Update: In endpoints/applications.py, response_model is ClaimApplicationResponse
        # Check if it has 'documents' list.
        
        # 3. Get Application Details
        logger.info("Step 2: Fetching Application Details...")
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/applications/{app_id}")
            
        if response.status_code != 200:
            logger.error(f"Get Application failed: {response.text}")
            sys.exit(1)
            
        details = response.json()
        logger.info(f" -> Details: {details}")
        
        assert details["id"] == app_id
        assert "documents" in details
        assert len(details["documents"]) == 2
        
        doc_filenames = [d["original_filename"] for d in details["documents"]]
        assert "test_doc_1.jpg" in doc_filenames
        assert "test_doc_2.jpg" in doc_filenames
        
        logger.info(" -> Application Details Verified.")
        
        # 4. List Applications
        logger.info("Step 3: Listing Applications...")
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/applications/")
            
        list_data = response.json()
        logger.info(f" -> List count: {len(list_data)}")
        
        found = False
        for item in list_data:
            if item["id"] == app_id:
                found = True
                break
        
        if not found:
            logger.error("Created application not found in list!")
            sys.exit(1)
            
        logger.info(" -> Application found in list.")
        
        logger.info("APPLICATION FLOW TEST PASSED ✅")

    except Exception as e:
        logger.error(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        for f in files_to_create:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    # Ensure we can import app
    # PRIORITIZE local backend folder over site-packages to avoid name collision with 'app' library
    sys.path.insert(0, os.path.join(os.getcwd(), "backend")) 
    sys.path.insert(0, os.getcwd()) 
    
    asyncio.run(main())
