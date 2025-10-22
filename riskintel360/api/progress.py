"""
Progress tracking API endpoints for RiskIntel360 Platform
Provides HTTP endpoints for validation progress monitoring.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from riskintel360.models import WorkflowStatus, data_manager
from riskintel360.services.agent_runtime import get_session_manager
from riskintel360.auth.auth_decorators import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/validations")


class ProgressResponse(BaseModel):
    """Response model for validation progress"""
    validation_id: str
    status: WorkflowStatus
    progress_percentage: float
    current_agent: Optional[str] = None
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    elapsed_time_seconds: Optional[float] = None
    agent_progress: Optional[Dict[str, Any]] = None


class AgentProgressDetail(BaseModel):
    """Detailed progress information for individual agents"""
    agent_name: str
    status: str
    progress_percentage: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_task: Optional[str] = None
    results_summary: Optional[Dict[str, Any]] = None


@router.get("/{validation_id}/progress", response_model=ProgressResponse)
async def get_validation_progress(
    validation_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get the current progress of a validation request.
    Returns detailed progress information including agent status.
    """
    try:
        # Get validation request to verify access
        validation = await data_manager.get_validation_request(validation_id)
        
        if not validation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation not found"
            )
        
        # Check user access
        if validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get session information from session manager
        session_manager = await get_session_manager()
        session_info = await session_manager.get_session_info(validation_id)
        
        # Calculate elapsed time
        elapsed_time_seconds = None
        if validation.created_at:
            elapsed_time_seconds = (datetime.now(timezone.utc) - validation.created_at).total_seconds()
        
        # Determine current status and progress
        current_status = validation.status or WorkflowStatus.PENDING
        progress_percentage = 0.0
        current_agent = None
        message = "Validation pending"
        agent_progress = None
        
        if session_info:
            progress_percentage = session_info.get("progress", 0.0)
            current_agent = session_info.get("current_agent")
            message = session_info.get("message", "Validation in progress")
            
            # Get detailed agent progress
            agent_progress = await _get_agent_progress_details(validation_id, session_manager)
        
        # Estimate completion time based on progress
        estimated_completion = None
        if progress_percentage > 0 and elapsed_time_seconds:
            estimated_total_time = elapsed_time_seconds / (progress_percentage / 100)
            remaining_time = estimated_total_time - elapsed_time_seconds
            if remaining_time > 0:
                estimated_completion = datetime.now(timezone.utc).replace(
                    second=int(datetime.now(timezone.utc).second + remaining_time)
                )
        
        return ProgressResponse(
            validation_id=validation_id,
            status=current_status,
            progress_percentage=progress_percentage,
            current_agent=current_agent,
            message=message,
            started_at=validation.created_at,
            estimated_completion=estimated_completion,
            elapsed_time_seconds=elapsed_time_seconds,
            agent_progress=agent_progress
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation progress {validation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation progress: {str(e)}"
        )


@router.get("/{validation_id}/agents", response_model=Dict[str, AgentProgressDetail])
async def get_agent_progress(
    validation_id: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get detailed progress information for all agents in a validation.
    """
    try:
        # Get validation request to verify access
        validation = await data_manager.get_validation_request(validation_id)
        
        if not validation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation not found"
            )
        
        # Check user access
        if validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get detailed agent progress
        session_manager = await get_session_manager()
        agent_progress = await _get_agent_progress_details(validation_id, session_manager)
        
        if not agent_progress:
            return {}
        
        # Convert to response models
        agent_details = {}
        for agent_name, progress_data in agent_progress.items():
            agent_details[agent_name] = AgentProgressDetail(
                agent_name=agent_name,
                status=progress_data.get("status", "pending"),
                progress_percentage=progress_data.get("progress", 0.0),
                started_at=progress_data.get("started_at"),
                completed_at=progress_data.get("completed_at"),
                current_task=progress_data.get("current_task"),
                results_summary=progress_data.get("results_summary")
            )
        
        return agent_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent progress {validation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent progress: {str(e)}"
        )


@router.get("/{validation_id}/logs")
async def get_validation_logs(
    validation_id: str,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Get validation execution logs for debugging and monitoring.
    """
    try:
        # Get validation request to verify access
        validation = await data_manager.get_validation_request(validation_id)
        
        if not validation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation not found"
            )
        
        # Check user access
        if validation.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get logs from session manager
        session_manager = await get_session_manager()
        logs = await session_manager.get_session_logs(validation_id, limit=limit)
        
        return {
            "validation_id": validation_id,
            "logs": logs or [],
            "total_logs": len(logs) if logs else 0,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation logs {validation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation logs: {str(e)}"
        )


async def _get_agent_progress_details(validation_id: str, session_manager) -> Optional[Dict[str, Any]]:
    """
    Get detailed progress information for all agents in a validation.
    """
    try:
        # Get session information
        session_info = await session_manager.get_session_info(validation_id)
        
        if not session_info:
            return None
        
        # Get agent states
        agent_states = session_info.get("agent_states", {})
        
        # Expected agents for a validation
        expected_agents = [
            "market_research",
            "competitive_intelligence", 
            "financial_validation",
            "risk_assessment",
            "customer_intelligence",
            "synthesis_recommendation"
        ]
        
        agent_progress = {}
        
        for agent_name in expected_agents:
            agent_state = agent_states.get(agent_name, {})
            
            agent_progress[agent_name] = {
                "status": agent_state.get("status", "pending"),
                "progress": agent_state.get("progress", 0.0),
                "started_at": agent_state.get("started_at"),
                "completed_at": agent_state.get("completed_at"),
                "current_task": agent_state.get("current_task"),
                "results_summary": agent_state.get("results_summary"),
                "error": agent_state.get("error")
            }
        
        return agent_progress
        
    except Exception as e:
        logger.error(f"Failed to get agent progress details: {e}")
        return None
