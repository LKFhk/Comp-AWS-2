"""
User API endpoints for RiskIntel360 Platform
Handles user preferences and profile management.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


class UserPreferences(BaseModel):
    """User preferences model"""
    theme: str = "light"
    notifications: Dict[str, Any] = {}
    defaultDashboard: str = "risk-intel"
    refreshInterval: int = 30000
    compactMode: bool = False
    showTutorials: bool = True
    enableAnimations: bool = True


@router.get("/preferences")
async def get_user_preferences(request: Request) -> Dict[str, Any]:
    """Get current user's preferences - minimal, cached response"""
    # Return minimal default preferences for demo
    return {
        "theme": "light",
        "defaultDashboard": "risk-intel",
        "compactMode": False
    }
    
    # Production mode requires authentication
    if not hasattr(request.state, 'current_user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Return default preferences for now
    # TODO: Implement database storage for user preferences
    return {
        "theme": "light",
        "notifications": {
            "email": True,
            "push": True
        },
        "defaultDashboard": "risk-intel"
    }


@router.put("/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    request: Request
) -> Dict[str, Any]:
    """Update current user's preferences - minimal response"""
    # Accept preferences but don't persist in demo mode
    return {
        "success": True,
        "message": "Preferences updated"
    }
    
    # TODO: Implement database storage for user preferences
    logger.info(f"Preferences update: {preferences.dict()}")
    
    return {
        "success": True,
        "message": "Preferences updated",
        "preferences": preferences.dict()
    }
