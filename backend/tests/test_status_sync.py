import pytest
from uuid import uuid4
from app.api.claims import ClaimStatus
from app.models.application import ClaimApplication, ApplicationStatus
from app.models.claim import Claim
from app.services.status_sync import StatusSyncService
from app.database import SessionLocal, Base, engine

# Setup DB
Base.metadata.create_all(bind=engine)

def test_status_sync_logic():
    db = SessionLocal()
    try:
        # Create App
        app_id = uuid4()
        app = ClaimApplication(id=app_id, name="Test App", status=ApplicationStatus.PROCESSING)
        db.add(app)
        db.commit()

        # Case 1: 1 Processing -> App Processing
        c1 = Claim(id=uuid4(), application_id=app_id, original_filename="doc1.jpg", status=ClaimStatus.PROCESSING)
        db.add(c1)
        db.commit()
        
        service = StatusSyncService(db)
        service.sync_application_status(app_id)
        db.refresh(app)
        assert app.status == ApplicationStatus.PROCESSING, "Should remain PROCESSING if child is PROCESSING"

        # Case 2: 1 Processing, 1 Needs Review -> App Processing
        c2 = Claim(id=uuid4(), application_id=app_id, original_filename="doc2.jpg", status=ClaimStatus.NEEDS_REVIEW)
        db.add(c2)
        db.commit()
        
        service.sync_application_status(app_id)
        db.refresh(app)
        assert app.status == ApplicationStatus.PROCESSING, "Should be PROCESSING if ANY child is PROCESSING"

        # Case 3: 2 Needs Review -> App Needs Review
        c1.status = ClaimStatus.NEEDS_REVIEW
        db.commit()
        
        service.sync_application_status(app_id)
        db.refresh(app)
        assert app.status == ApplicationStatus.NEEDS_REVIEW, "Should be NEEDS_REVIEW if all are reviewed/done"

        # Case 4: 1 Audited, 1 Needs Review -> App Needs Review
        c1.status = ClaimStatus.AUDITED
        db.commit()
        
        service.sync_application_status(app_id)
        db.refresh(app)
        assert app.status == ApplicationStatus.NEEDS_REVIEW, "Should be NEEDS_REVIEW if any pending review"

        # Case 5: 2 Audited -> App Audited
        c2.status = ClaimStatus.AUDITED
        db.commit()
        
        service.sync_application_status(app_id)
        db.refresh(app)
        assert app.status == ApplicationStatus.AUDITED, "Should be AUDITED if all audited"

        print("All Status Sync Tests Passed!")

    finally:
        db.close()

if __name__ == "__main__":
    test_status_sync_logic()
