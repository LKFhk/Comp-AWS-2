"""
Cost Management API Endpoints for RiskIntel360 Platform
Provides REST API for cost estimation, monitoring, and configuration.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from ..services.cost_management import (
    get_cost_management_service,
    CostManagementService,
    CostProfile,
    CostEstimate,
    CostGuardrails
)
from ..auth.auth_decorators import require_auth, RequireAdmin, get_current_user
from ..models.core import ValidationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cost", tags=["cost-management"])


# Request/Response Models
class CostEstimationRequest(BaseModel):
    """Request model for cost estimation"""
    profile: Optional[str] = Field(None, description="Cost profile to use")
    validation_request: Optional[ValidationRequest] = Field(None, description="Validation request details")


class CostEstimationResponse(BaseModel):
    """Response model for cost estimation"""
    total_cost: float = Field(..., description="Total estimated cost in USD")
    bedrock_cost: float = Field(..., description="Bedrock model costs")
    infrastructure_cost: float = Field(..., description="Infrastructure costs")
    estimated_duration_hours: float = Field(..., description="Estimated duration in hours")
    confidence_level: float = Field(..., description="Confidence level (0-1)")
    profile_used: str = Field(..., description="Cost profile used")
    model_selection: Dict[str, str] = Field(..., description="Model selection per agent")
    breakdown: Dict[str, float] = Field(..., description="Detailed cost breakdown")


class ProfileSwitchRequest(BaseModel):
    """Request model for switching cost profiles"""
    profile: str = Field(..., description="New cost profile")


class APIKeyRequest(BaseModel):
    """Request model for storing API keys"""
    service: str = Field(..., description="Service name")
    key_type: str = Field(..., description="Key type (e.g., 'api_key', 'secret')")
    value: str = Field(..., description="API key value")


class GuardrailUpdateRequest(BaseModel):
    """Request model for updating cost guardrails"""
    daily_limit: Optional[float] = Field(None, description="Daily cost limit")
    monthly_limit: Optional[float] = Field(None, description="Monthly cost limit")
    per_validation_limit: Optional[float] = Field(None, description="Per validation cost limit")
    alert_thresholds: Optional[List[float]] = Field(None, description="Alert thresholds (0-1)")
    throttling_enabled: Optional[bool] = Field(None, description="Enable throttling")
    emergency_shutdown_enabled: Optional[bool] = Field(None, description="Enable emergency shutdown")


class UsageSummaryResponse(BaseModel):
    """Response model for usage summary"""
    current_profile: str = Field(..., description="Current cost profile")
    daily_cost: float = Field(..., description="Current daily cost")
    monthly_cost: float = Field(..., description="Current monthly cost")
    validations_today: int = Field(..., description="Validations completed today")
    validations_this_month: int = Field(..., description="Validations completed this month")
    daily_limit: float = Field(..., description="Daily cost limit")
    monthly_limit: float = Field(..., description="Monthly cost limit")
    per_validation_limit: float = Field(..., description="Per validation cost limit")
    daily_usage_percentage: float = Field(..., description="Daily usage as percentage")
    monthly_usage_percentage: float = Field(..., description="Monthly usage as percentage")


class ProfileComparisonResponse(BaseModel):
    """Response model for profile comparison"""
    profiles: Dict[str, Dict[str, Any]] = Field(..., description="Profile comparison data")


# API Endpoints
@router.post("/estimate", response_model=CostEstimationResponse)
async def estimate_cost(
    request: CostEstimationRequest,
    cost_service: CostManagementService = Depends(get_cost_management_service),
    current_user: Dict = Depends(require_auth)
):
    """
    Estimate cost for a validation workflow
    """
    try:
        # Parse profile if provided
        profile = None
        if request.profile:
            try:
                profile = CostProfile(request.profile.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid cost profile: {request.profile}"
                )
        
        # Get cost estimation
        estimate = await cost_service.estimate_validation_cost(profile)
        
        # Build response
        return CostEstimationResponse(
            total_cost=float(estimate.total_cost),
            bedrock_cost=float(estimate.service_costs.bedrock_cost),
            infrastructure_cost=float(
                estimate.service_costs.total_cost - estimate.service_costs.bedrock_cost
            ),
            estimated_duration_hours=float(estimate.estimated_duration_hours),
            confidence_level=estimate.confidence_level,
            profile_used=estimate.profile_used.value,
            model_selection=estimate.model_selection,
            breakdown={
                "bedrock": float(estimate.service_costs.bedrock_cost),
                "ecs": float(estimate.service_costs.ecs_cost),
                "aurora": float(estimate.service_costs.aurora_cost),
                "elasticache": float(estimate.service_costs.elasticache_cost),
                "api_gateway": float(estimate.service_costs.api_gateway_cost),
                "s3": float(estimate.service_costs.s3_cost),
                "cloudwatch": float(estimate.service_costs.cloudwatch_cost)
            }
        )
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost estimation failed: {str(e)}"
        )


@router.get("/profiles/compare", response_model=ProfileComparisonResponse)
async def compare_profiles(
    cost_service: CostManagementService = Depends(get_cost_management_service),
    current_user: Dict = Depends(require_auth)
):
    """
    Compare costs across different profiles
    """
    try:
        profiles_data = {}
        
        for profile in CostProfile:
            estimate = await cost_service.estimate_validation_cost(profile)
            config = cost_service.profile_manager.get_profile_config(profile)
            
            profiles_data[profile.value] = {
                "total_cost": float(estimate.total_cost),
                "bedrock_cost": float(estimate.service_costs.bedrock_cost),
                "infrastructure_cost": float(
                    estimate.service_costs.total_cost - estimate.service_costs.bedrock_cost
                ),
                "estimated_duration_hours": float(estimate.estimated_duration_hours),
                "model_selection": estimate.model_selection,
                "description": config.get("description", ""),
                "parallel_execution": config.get("parallel_execution", True),
                "caching_enabled": config.get("caching_enabled", True)
            }
        
        return ProfileComparisonResponse(profiles=profiles_data)
        
    except Exception as e:
        logger.error(f"Profile comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile comparison failed: {str(e)}"
        )


@router.post("/profile/switch")
async def switch_profile(
    request: ProfileSwitchRequest,
    cost_service: CostManagementService = Depends(get_cost_management_service),
    security_context = Depends(RequireAdmin)
):
    """
    Switch to a different cost profile (admin only)
    """
    try:
        profile = CostProfile(request.profile.lower())
        await cost_service.switch_profile(profile)
        
        return {"message": f"Switched to cost profile: {profile.value}"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cost profile: {request.profile}"
        )
    except Exception as e:
        logger.error(f"Profile switch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile switch failed: {str(e)}"
        )


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    cost_service: CostManagementService = Depends(get_cost_management_service),
    current_user: Dict = Depends(require_auth)
):
    """
    Get current usage summary and limits
    """
    try:
        summary = await cost_service.get_usage_summary()
        
        # Calculate usage percentages
        daily_usage_pct = (summary["daily_cost"] / summary["daily_limit"]) * 100 if summary["daily_limit"] > 0 else 0
        monthly_usage_pct = (summary["monthly_cost"] / summary["monthly_limit"]) * 100 if summary["monthly_limit"] > 0 else 0
        
        return UsageSummaryResponse(
            **summary,
            daily_usage_percentage=daily_usage_pct,
            monthly_usage_percentage=monthly_usage_pct
        )
        
    except Exception as e:
        logger.error(f"Usage summary failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usage summary failed: {str(e)}"
        )


@router.post("/credentials/store")
async def store_api_key(
    request: APIKeyRequest,
    cost_service: CostManagementService = Depends(get_cost_management_service),
    security_context = Depends(RequireAdmin)
):
    """
    Store encrypted API key (admin only)
    """
    try:
        await cost_service.store_api_key(
            request.service,
            request.key_type,
            request.value
        )
        
        return {"message": f"API key stored for {request.service}.{request.key_type}"}
        
    except Exception as e:
        logger.error(f"API key storage failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API key storage failed: {str(e)}"
        )


@router.get("/credentials/services")
async def list_configured_services(
    cost_service: CostManagementService = Depends(get_cost_management_service),
    security_context = Depends(RequireAdmin)
):
    """
    List services with stored credentials (admin only)
    """
    try:
        services = await cost_service.list_configured_services()
        return {"services": services}
        
    except Exception as e:
        logger.error(f"Service listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service listing failed: {str(e)}"
        )


@router.post("/validation/check")
async def check_validation_allowed(
    request: CostEstimationRequest,
    cost_service: CostManagementService = Depends(get_cost_management_service),
    current_user: Dict = Depends(require_auth)
):
    """
    Check if validation is allowed based on cost limits
    """
    try:
        # Get cost estimation
        profile = None
        if request.profile:
            profile = CostProfile(request.profile.lower())
        
        estimate = await cost_service.estimate_validation_cost(profile)
        
        # Check if allowed
        check_result = await cost_service.check_validation_allowed(estimate.total_cost)
        
        return {
            "allowed": check_result["allowed"],
            "estimated_cost": float(estimate.total_cost),
            "warnings": check_result["warnings"],
            "actions": check_result["actions"],
            "profile_used": estimate.profile_used.value
        }
        
    except Exception as e:
        logger.error(f"Validation check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation check failed: {str(e)}"
        )


@router.get("/models/selection")
async def get_model_selection(
    profile: Optional[str] = None,
    cost_service: CostManagementService = Depends(get_cost_management_service),
    current_user: Dict = Depends(require_auth)
):
    """
    Get model selection for current or specified profile
    """
    try:
        cost_profile = None
        if profile:
            cost_profile = CostProfile(profile.lower())
        
        model_selection = await cost_service.get_model_selection(cost_profile)
        
        return {
            "profile": cost_profile.value if cost_profile else cost_service.current_profile.value,
            "model_selection": model_selection
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cost profile: {profile}"
        )
    except Exception as e:
        logger.error(f"Model selection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model selection failed: {str(e)}"
        )


@router.get("/dashboard")
async def get_cost_dashboard(
    cost_service: CostManagementService = Depends(get_cost_management_service),
    current_user: Dict = Depends(require_auth)
):
    """
    Get comprehensive cost monitoring dashboard data
    """
    try:
        # Get usage summary
        summary = await cost_service.get_usage_summary()
        
        # Get current month costs from AWS
        current_costs = await cost_service.cost_tracker.get_current_month_costs()
        
        # Get optimization recommendations
        usage_pattern = {
            'daily_cost': summary['daily_cost'],
            'monthly_cost': summary['monthly_cost'],
            'validations_today': summary['validations_today']
        }
        
        recommendations = cost_service.optimizer.get_optimization_recommendations(
            cost_service.current_profile, usage_pattern
        )
        
        # Calculate usage percentages
        daily_usage_pct = (summary['daily_cost'] / summary['daily_limit']) * 100 if summary['daily_limit'] > 0 else 0
        monthly_usage_pct = (summary['monthly_cost'] / summary['monthly_limit']) * 100 if summary['monthly_limit'] > 0 else 0
        
        # Get profile comparison
        profile_comparison = {}
        for profile in CostProfile:
            estimate = await cost_service.estimate_validation_cost(profile)
            profile_comparison[profile.value] = {
                'cost_per_validation': float(estimate.total_cost),
                'model_selection': estimate.model_selection,
                'estimated_duration_hours': estimate.estimated_duration_hours
            }
        
        return {
            "usage_summary": {
                **summary,
                "daily_usage_percentage": daily_usage_pct,
                "monthly_usage_percentage": monthly_usage_pct
            },
            "service_costs": current_costs,
            "optimization_recommendations": recommendations,
            "profile_comparison": profile_comparison,
            "alerts": [
                {
                    "level": "warning" if daily_usage_pct > 80 else "info",
                    "message": f"Daily usage at {daily_usage_pct:.1f}% of limit",
                    "action": "Consider cost optimization" if daily_usage_pct > 80 else None
                },
                {
                    "level": "warning" if monthly_usage_pct > 80 else "info", 
                    "message": f"Monthly usage at {monthly_usage_pct:.1f}% of limit",
                    "action": "Monitor usage closely" if monthly_usage_pct > 80 else None
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cost dashboard failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost dashboard failed: {str(e)}"
        )


@router.post("/guardrails/update")
async def update_guardrails(
    request: GuardrailUpdateRequest,
    cost_service: CostManagementService = Depends(get_cost_management_service),
    security_context = Depends(RequireAdmin)
):
    """
    Update cost guardrails (admin only)
    """
    try:
        guardrails = cost_service.guardrail_manager.guardrails
        
        # Update provided fields
        if request.daily_limit is not None:
            guardrails.max_daily_spend = request.daily_limit
        if request.monthly_limit is not None:
            guardrails.max_monthly_spend = request.monthly_limit
        if request.per_validation_limit is not None:
            guardrails.max_per_validation = request.per_validation_limit
        if request.alert_thresholds is not None:
            guardrails.alert_threshold_percent = request.alert_thresholds[0] * 100 if request.alert_thresholds else 80.0
        if request.throttling_enabled is not None:
            guardrails.auto_throttle_enabled = request.throttling_enabled
        
        return {
            "message": "Cost guardrails updated successfully",
            "guardrails": {
                "daily_limit": guardrails.max_daily_spend,
                "monthly_limit": guardrails.max_monthly_spend,
                "per_validation_limit": guardrails.max_per_validation,
                "alert_threshold_percent": guardrails.alert_threshold_percent,
                "throttling_enabled": guardrails.auto_throttle_enabled
            }
        }
        
    except Exception as e:
        logger.error(f"Guardrail update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Guardrail update failed: {str(e)}"
        )


@router.get("/optimization/recommendations")
async def get_optimization_recommendations(
    cost_service: CostManagementService = Depends(get_cost_management_service),
    current_user: Dict = Depends(require_auth)
):
    """
    Get personalized cost optimization recommendations
    """
    try:
        summary = await cost_service.get_usage_summary()
        
        usage_pattern = {
            'daily_cost': summary['daily_cost'],
            'monthly_cost': summary['monthly_cost'],
            'validations_today': summary['validations_today'],
            'validations_this_month': summary['validations_this_month']
        }
        
        recommendations = cost_service.optimizer.get_optimization_recommendations(
            cost_service.current_profile, usage_pattern
        )
        
        # Suggest profile switch if beneficial
        suggested_profile = cost_service.optimizer.suggest_profile_switch(
            cost_service.current_profile, usage_pattern
        )
        
        return {
            "current_profile": cost_service.current_profile.value,
            "recommendations": recommendations,
            "suggested_profile": suggested_profile.value if suggested_profile else None,
            "usage_analysis": {
                "daily_cost": summary['daily_cost'],
                "monthly_cost": summary['monthly_cost'],
                "average_cost_per_validation": (
                    summary['monthly_cost'] / summary['validations_this_month'] 
                    if summary['validations_this_month'] > 0 else 0
                ),
                "cost_trend": "increasing" if summary['daily_cost'] > 5 else "stable"
            }
        }
        
    except Exception as e:
        logger.error(f"Optimization recommendations failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization recommendations failed: {str(e)}"
        )


@router.post("/throttle")
async def emergency_throttle(
    throttle_level: float = 0.5,
    cost_service: CostManagementService = Depends(get_cost_management_service),
    security_context = Depends(RequireAdmin)
):
    """
    Emergency cost throttling (admin only)
    """
    try:
        if not 0.0 <= throttle_level <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Throttle level must be between 0.0 and 1.0"
            )
        
        # Switch to demo profile for maximum cost savings
        if throttle_level < 0.3:
            await cost_service.switch_profile(CostProfile.DEMO)
            message = "Emergency throttling: Switched to DEMO profile"
        elif throttle_level < 0.7:
            await cost_service.switch_profile(CostProfile.DEVELOPMENT)
            message = "Moderate throttling: Switched to DEVELOPMENT profile"
        else:
            message = "Light throttling: Maintaining current profile"
        
        return {
            "message": message,
            "throttle_level": throttle_level,
            "new_profile": cost_service.current_profile.value,
            "estimated_cost_reduction": f"{(1 - throttle_level) * 100:.0f}%"
        }
        
    except Exception as e:
        logger.error(f"Emergency throttling failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emergency throttling failed: {str(e)}"
        )


@router.get("/health")
async def cost_management_health():
    """
    Health check for cost management service
    """
    try:
        cost_service = await get_cost_management_service()
        summary = await cost_service.get_usage_summary()
        
        return {
            "status": "healthy",
            "current_profile": summary["current_profile"],
            "services_configured": len(await cost_service.list_configured_services()),
            "daily_usage_percentage": (summary['daily_cost'] / summary['daily_limit']) * 100 if summary['daily_limit'] > 0 else 0,
            "monthly_usage_percentage": (summary['monthly_cost'] / summary['monthly_limit']) * 100 if summary['monthly_limit'] > 0 else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cost management health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
