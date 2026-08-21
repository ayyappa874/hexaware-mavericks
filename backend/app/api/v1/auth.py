from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = "Supervisor"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

# Demo Accounts
MOCK_USERS = {
    "admin": {"password": "admin123password", "role": "Admin"},
    "supervisor": {"password": "supervisor123password", "role": "Supervisor"},
    "viewer": {"password": "viewer123password", "role": "Viewer"}
}

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    uname = req.username.lower().strip()
    
    # Check mock credentials or accept specified role for demo flexibility
    if uname in MOCK_USERS and req.password == MOCK_USERS[uname]["password"]:
        role = MOCK_USERS[uname]["role"]
    else:
        role = req.role if req.role in ["Admin", "Supervisor", "Viewer"] else "Supervisor"

    token = create_access_token(data={"sub": req.username, "role": role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=req.username,
        role=role
    )
