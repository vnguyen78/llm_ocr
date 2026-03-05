import os
import sys
# Ensure backend importable
sys.path.insert(0, os.path.join(os.getcwd(), "backend")) 

from app.database import engine, Base
from app.models.claim import Base as ClaimBase  
# Import all models to ensure they are registered in metadata
from app.models.claim import Claim, ClaimPage, ClaimTile  
from app.models.extraction import ExtractedData
from app.models.audit import AuditFlag
from app.models.application import ClaimApplication 

def reset_db():
    print("Resetting database...")
    
    # 1. Identify DB Locations (backend/sql_app.db and ./sql_app.db)
    # We want to nuke both to be safe, as configuration is relative.
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .../backend
    root_dir = os.path.dirname(backend_dir) # .../OCRAgent
    
    db_files = [
        os.path.join(backend_dir, "sql_app.db"),
        os.path.join(root_dir, "sql_app.db")
    ]
    
    for db_path in db_files:
        if os.path.exists(db_path):
            print(f"Removing existing DB: {db_path}")
            os.remove(db_path)
            
    # 2. Drop all tables (Just in case, though file removal handles it for SQLite)
    # For robust SQLite reset, removing the file is cleaner as it handles "no such column" issues by forcing fresh init.
    
    print("Creating all tables (fresh DB)...")
    ClaimBase.metadata.create_all(bind=engine)
    
    print("Database reset complete. Please restart your backend server.")

if __name__ == "__main__":
    reset_db()
