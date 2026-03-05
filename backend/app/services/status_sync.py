from sqlalchemy.orm import Session
from app.models.claim import Claim, ClaimStatus
from app.models.application import ClaimApplication, ApplicationStatus

class StatusSyncService:
    def __init__(self, db: Session):
        self.db = db

    def sync_application_status(self, application_id):
        # Get all claims for this app
        claims = self.db.query(Claim).filter(Claim.application_id == application_id).all()
        
        if not claims:
            return # No claims, maybe do nothing or set to COMPLETED?

        status_counts = {}
        for c in claims:
            status_counts[c.status] = status_counts.get(c.status, 0) + 1

        # Logic Priority
        # 1. Processing
        if status_counts.get(ClaimStatus.PROCESSING, 0) > 0 or status_counts.get(ClaimStatus.EXTRACTING, 0) > 0:
            new_status = ApplicationStatus.PROCESSING
        # 2. Needs Review
        elif status_counts.get(ClaimStatus.NEEDS_REVIEW, 0) > 0:
            new_status = ApplicationStatus.NEEDS_REVIEW
        # 3. Audited (Second Review)
        elif status_counts.get(ClaimStatus.AUDITED, 0) > 0:
             new_status = ApplicationStatus.AUDITED
        # 4. Completed
        else:
            new_status = ApplicationStatus.COMPLETED

        # Update Application
        app = self.db.query(ClaimApplication).get(application_id)
        if app and app.status != new_status:
            app.status = new_status
            self.db.commit()
