from uuid import uuid4
from unittest.mock import MagicMock
from app.models.claim import Claim, ClaimStatus
from app.services.review import ReviewService

def test_bulk_reject_claims():
    # Setup
    db = MagicMock()
    service = ReviewService(db)
    
    claim_ids = [uuid4(), uuid4()]
    
    # Action
    service.bulk_reject_claims(claim_ids)
    
    # Assert
    # Verify update was called with correct filter and status
    # Note: synchronize_session=False is used in implementation
    db.query(Claim).filter().update.assert_called_once()
    args, kwargs = db.query(Claim).filter().update.call_args
    assert args[0][Claim.status] == ClaimStatus.REJECTED
    db.commit.assert_called_once()

def test_bulk_delete_claims():
    # Setup
    db = MagicMock()
    service = ReviewService(db)
    
    claim_ids = [uuid4(), uuid4()]
    
    # Action
    service.bulk_delete_claims(claim_ids)
    
    # Assert
    db.query(Claim).filter().delete.assert_called_once()
    db.commit.assert_called_once()
