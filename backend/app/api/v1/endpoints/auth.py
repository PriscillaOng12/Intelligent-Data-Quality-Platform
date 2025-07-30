from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/login")
async def login(credentials: dict):
    """User login endpoint"""
    try:
        # Mock authentication
        if credentials.get("username") == "admin" and credentials.get("password") == "password":
            return {
                "access_token": "mock_token_123",
                "token_type": "bearer",
                "user": {
                    "id": "user_1",
                    "username": "admin",
                    "email": "admin@example.com",
                    "role": "admin"
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/logout")
async def logout():
    """User logout endpoint"""
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user():
    """Get current user information"""
    return {
        "id": "user_1",
        "username": "admin", 
        "email": "admin@example.com",
        "role": "admin",
        "permissions": ["read", "write", "admin"]
    }
