
import requests
import time
import os
import uuid

BACKEND_URL = "http://localhost:8000/api/v1/claims"

def test_upload_and_immediate_trigger():
    print("--- Testing Upload and Immediate Trigger ---")
    
    # Check if we have a test file
    test_file_path = "test_claim.jpg"
    if not os.path.exists(test_file_path):
        # Create a dummy image for testing if it doesn't exist
        from PIL import Image
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        img.save(test_file_path)
        print(f"Created dummy test file: {test_file_path}")

    # 1. Upload
    print(f"Uploading {test_file_path}...")
    with open(test_file_path, "rb") as f:
        files = {"file": (test_file_path, f, "image/jpeg")}
        response = requests.post(f"{BACKEND_URL}/ingest", files=files)
    
    if response.status_code != 202:
        print(f"FAILED: Upload returned status {response.status_code}")
        print(response.text)
        return

    data = response.json()
    claim_id = data["claim_id"]
    print(f"SUCCESS: Upload accepted. Claim ID: {claim_id}")

    # 2. Verify Processing Status immediately
    print("Checking queue for PROCESSING/EXTRACTING status...")
    
    # Wait a bit for background task to initialize
    time.sleep(2)
    
    found_in_queue = False
    for status in ["PROCESSING", "EXTRACTING"]:
        queue_url = f"{BACKEND_URL}/queue?status={status}"
        resp = requests.get(queue_url)
        if resp.status_code == 200:
            queue = resp.json()
            matching = [c for c in queue if c["id"] == claim_id]
            if matching:
                print(f"SUCCESS: Claim {claim_id} found in {status} queue.")
                found_in_queue = True
                break
    
    if not found_in_queue:
        print(f"FAILED: Claim {claim_id} NOT found in PROCESSING or EXTRACTING queue.")

    # 3. Wait and check for NEEDS_REVIEW (Triggering Extraction)
    print("Waiting for extraction to complete (checking for NEEDS_REVIEW status)...")
    max_retries = 30
    found = False
    for i in range(max_retries):
        time.sleep(5)
        resp = requests.get(f"{BACKEND_URL}/queue?status=NEEDS_REVIEW")
        if resp.status_code == 200:
            queue = resp.json()
            matching = [c for c in queue if c["id"] == claim_id]
            if matching:
                print(f"SUCCESS: Extraction completed! Claim {claim_id} is now in NEEDS_REVIEW.")
                found = True
                break
            else:
                print(f"Not yet in NEEDS_REVIEW... (Attempt {i+1}/{max_retries})")
        else:
            print(f"Error checking NEEDS_REVIEW queue: {resp.status_code}")
    
    if not found:
        print("FAILED: Extraction did not complete within timeout. Check backend logs for LLM errors.")

if __name__ == "__main__":
    test_upload_and_immediate_trigger()
