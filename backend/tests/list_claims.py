import sys
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Ensure we can import app
sys.path.append(os.getcwd())

from app.models.claim import Claim
from app.api.claims import ClaimStatus
from app.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def list_claims():
    db = SessionLocal()
    try:
        claims = db.query(Claim).all()
        print(f"Total Claims: {len(claims)}")
        for claim in claims:
            print(f"ID: {claim.id} | Status: {claim.status} | Created: {claim.created_at}")
    finally:
        db.close()

if __name__ == "__main__":
    list_claims()
