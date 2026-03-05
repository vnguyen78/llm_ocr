from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    # Mock Authentication Logic for Testing
    if request.username == "admin" and request.password == "admin":
        return {
            "token": str(uuid.uuid4()),
            "user": "admin",
            "role": "architect"
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )
