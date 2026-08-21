import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "survey_sentinel_mospi_secret_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_info(
    token: Optional[str] = Depends(oauth2_scheme),
    x_role: Optional[str] = Header(None, alias="X-Role"),
    x_user: Optional[str] = Header(None, alias="X-User")
) -> Dict[str, Any]:
    # Support X-Role header for simple testing / UI switching, or JWT token
    if x_role:
        role = x_role.capitalize()
        if role not in ["Admin", "Supervisor", "Viewer"]:
            role = "Viewer"
        return {"username": x_user or "government_official", "role": role}

    if not token:
        # Default fallback role if no auth header passed
        return {"username": "supervisor_default", "role": "Supervisor"}

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub", "official")
        role: str = payload.get("role", "Viewer")
        return {"username": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_roles: list[str]):
    def role_checker(user_info: Dict[str, Any] = Depends(get_current_user_info)):
        user_role = user_info.get("role", "Viewer")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {required_roles}. Current role: {user_role}"
            )
        return user_info
    return role_checker
