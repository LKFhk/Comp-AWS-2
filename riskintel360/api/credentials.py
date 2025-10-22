"""
AWS Credentials Management API Endpoints
Provides secure credential management with validation and cost estimation.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, field_validator
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..services.credential_manager import credential_manager, CredentialConfig
from ..services.cost_management import AWSCostManager, CostProfile, DetailedCostEstimate
from ..auth.dependencies import get_current_user
from ..auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])

class AWSCredentialsRequest(BaseModel):
    """AWS credentials input model"""
    access_key_id: str = Field(..., min_length=16, max_length=128, description="AWS Access Key ID")
    secret_access_key: str = Field(..., min_length=16, max_length=128, description="AWS Secret Access Key")
    region: str = Field(default="us-east-1", description="AWS Region")
    enable_production_mode: bool = Field(default=False, description="Enable AWS Bedrock Agents production mode")
    
    @field_validator('access_key_id')
    @classmethod
    def validate_access_key_format(cls, v):
        if not v.startswith('AKIA') and not v.startswith('ASIA'):
            raise ValueError('Invalid AWS Access Key ID format')
        return v
    
    @field_validator('region')
    @classmethod
    def validate_region(cls, v):
        valid_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
        ]
        if v not in valid_regions:
            raise ValueError(f'Region must be one of: {", ".join(valid_regions)}')
        return v

class ExternalAPIKeyRequest(BaseModel):
    """External API key input model"""
    service_name: str = Field(..., description="Service name (e.g., alpha_vantage, news_api)")
    api_key: str = Field(..., min_length=8, max_length=256, description="API Key")
    endpoint_url: Optional[str] = Field(None, description="Custom endpoint URL")
    additional_config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")

class CredentialValidationResponse(BaseModel):
    """Credential validation response"""
    valid: bool
    service_name: str
    region: Optional[str] = None
    error_message: Optional[str] = None
    permissions: Optional[List[str]] = None
    cost_estimate: Optional[Dict[str, Any]] = None

class CostEstimationRequest(BaseModel):
    """Cost estimation request"""
    profile: str = Field(default="development", description="Cost profile (demo, development, production)")
    business_concept: str = Field(..., description="Business concept to validate")
    analysis_scope: List[str] = Field(default=["market", "competitive", "financial"], description="Analysis scope")
    target_market: str = Field(..., description="Target market")

class BudgetLimitsRequest(BaseModel):
    """Budget limits configuration"""
    max_daily_spend: float = Field(..., gt=0, description="Maximum daily spend in USD")
    max_monthly_spend: float = Field(..., gt=0, description="Maximum monthly spend in USD")
    max_per_validation: float = Field(..., gt=0, description="Maximum cost per validation in USD")
    alert_threshold_percent: float = Field(default=80.0, ge=0, le=100, description="Alert threshold percentage")
    auto_throttle_enabled: bool = Field(default=True, description="Enable automatic throttling")

@router.post("/aws/setup", response_model=CredentialValidationResponse)
async def setup_aws_credentials(
    credentials: AWSCredentialsRequest,
    current_user: User = Depends(get_current_user)
):
    """Setup and validate AWS credentials with AgentCore mode configuration"""
    try:
        # Store credentials securely with production mode setting
        credential_manager.setup_aws_credentials(
            access_key_id=credentials.access_key_id,
            secret_access_key=credentials.secret_access_key,
            region=credentials.region
        )
        
        # Store AgentCore production mode setting
        agentcore_config = CredentialConfig(
            service_name="agentcore_config",
            api_key="config",
            region=credentials.region,
            additional_config={
                "enable_production_mode": credentials.enable_production_mode,
                "mode": "production" if credentials.enable_production_mode else "development",
                "user_id": current_user.id
            }
        )
        await credential_manager.store_credential("agentcore_config", agentcore_config)
        
        # Validate credentials by making a test call
        validation_result = await validate_aws_credentials(
            credentials.access_key_id, 
            credentials.secret_access_key, 
            credentials.region
        )
        
        if validation_result["valid"]:
            mode_msg = "production" if credentials.enable_production_mode else "development"
            logger.info(f"AWS credentials configured for user {current_user.id} in {mode_msg} mode")
            
            # Get cost estimate for typical validation
            cost_manager = AWSCostManager(CostProfile.DEVELOPMENT)
            cost_estimate = await cost_manager.estimate_validation_cost(
                business_concept="Sample SaaS platform",
                analysis_scope=["market", "competitive", "financial"],
                target_market="Enterprise B2B"
            )
            
            # Add mode information to cost estimate
            cost_dict = cost_estimate.to_dict()
            cost_dict["agentcore_mode"] = mode_msg
            cost_dict["agentcore_production_enabled"] = credentials.enable_production_mode
            
            return CredentialValidationResponse(
                valid=True,
                service_name="aws",
                region=credentials.region,
                permissions=validation_result.get("permissions", []),
                cost_estimate=cost_dict
            )
        else:
            return CredentialValidationResponse(
                valid=False,
                service_name="aws",
                region=credentials.region,
                error_message=validation_result.get("error_message", "Invalid credentials")
            )
            
    except Exception as e:
        logger.error(f"Failed to setup AWS credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup AWS credentials: {str(e)}"
        )

@router.post("/external/setup", response_model=CredentialValidationResponse)
async def setup_external_api_key(
    api_key_request: ExternalAPIKeyRequest,
    current_user: User = Depends(get_current_user)
):
    """Setup external API key"""
    try:
        config = CredentialConfig(
            service_name=api_key_request.service_name,
            api_key=api_key_request.api_key,
            region="us-east-1",  # Default region for external APIs
            endpoint_url=api_key_request.endpoint_url,
            additional_config=api_key_request.additional_config
        )
        
        await credential_manager.store_credential(api_key_request.service_name, config)
        
        # Validate the API key if possible
        validation_result = await validate_external_api_key(api_key_request.service_name, api_key_request.api_key)
        
        logger.info(f"External API key for {api_key_request.service_name} configured for user {current_user.id}")
        
        return CredentialValidationResponse(
            valid=validation_result["valid"],
            service_name=api_key_request.service_name,
            error_message=validation_result.get("error_message")
        )
        
    except Exception as e:
        logger.error(f"Failed to setup external API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup external API key: {str(e)}"
        )

@router.get("/list")
async def list_configured_services() -> Dict[str, Any]:
    """List all configured services with AgentCore mode"""
    try:
        # Check if credential_manager is available
        if credential_manager is None:
            logger.warning("Credential manager not initialized")
            return {
                "aws_services": [],
                "external_services": [],
                "total_count": 0,
                "agentcore_mode": "development"
            }
        
        services = await credential_manager.list_services()
        
        # Categorize services
        aws_services = [s for s in services if s in ['aws', 'bedrock']]
        external_services = [s for s in services if s not in ['aws', 'bedrock']]
        
        # Get AgentCore configuration
        agentcore_mode = "development"
        agentcore_config = credential_manager.get_credential("agentcore_config")
        if agentcore_config and agentcore_config.additional_config:
            agentcore_mode = agentcore_config.additional_config.get("mode", "development")
        
        return {
            "aws_services": aws_services,
            "external_services": external_services,
            "total_count": len(services),
            "agentcore_mode": agentcore_mode,
            "agentcore_production_enabled": agentcore_mode == "production"
        }
        
    except Exception as e:
        logger.warning(f"Failed to list services: {e}")
        # Return empty list instead of error in dev mode
        return {
            "aws_services": [],
            "external_services": [],
            "total_count": 0,
            "agentcore_mode": "development"
        }

@router.get("/agentcore/mode")
async def get_agentcore_mode() -> Dict[str, Any]:
    """Get current AgentCore mode configuration"""
    try:
        agentcore_config = credential_manager.get_credential("agentcore_config")
        
        if not agentcore_config or not agentcore_config.additional_config:
            return {
                "mode": "development",
                "production_enabled": False,
                "description": "Using simulation mode (no Bedrock Agents setup required)"
            }
        
        config = agentcore_config.additional_config
        mode = config.get("mode", "development")
        production_enabled = config.get("enable_production_mode", False)
        
        return {
            "mode": mode,
            "production_enabled": production_enabled,
            "description": (
                "Using real AWS Bedrock Agents API for multi-agent coordination" 
                if production_enabled 
                else "Using simulation mode (no Bedrock Agents setup required)"
            ),
            "region": agentcore_config.region
        }
        
    except Exception as e:
        logger.error(f"Failed to get AgentCore mode: {e}")
        return {
            "mode": "development",
            "production_enabled": False,
            "description": "Using simulation mode (default)"
        }

@router.post("/validate/{service_name}")
async def validate_service_credentials(
    service_name: str,
    current_user: User = Depends(get_current_user)
) -> CredentialValidationResponse:
    """Validate stored credentials for a service"""
    try:
        if not credential_manager.validate_credentials(service_name):
            return CredentialValidationResponse(
                valid=False,
                service_name=service_name,
                error_message="Credentials not found or invalid format"
            )
        
        config = credential_manager.get_credential(service_name)
        if not config:
            return CredentialValidationResponse(
                valid=False,
                service_name=service_name,
                error_message="Credentials not found"
            )
        
        if service_name in ['aws', 'bedrock']:
            validation_result = await validate_aws_credentials(
                config.api_key,
                config.additional_config.get('secret_access_key'),
                config.region
            )
        else:
            validation_result = await validate_external_api_key(service_name, config.api_key)
        
        return CredentialValidationResponse(
            valid=validation_result["valid"],
            service_name=service_name,
            region=config.region,
            error_message=validation_result.get("error_message"),
            permissions=validation_result.get("permissions")
        )
        
    except Exception as e:
        logger.error(f"Failed to validate credentials for {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate credentials for {service_name}"
        )

@router.delete("/{service_name}")
async def delete_service_credentials(
    service_name: str,
    current_user: User = Depends(get_current_user)
):
    """Delete stored credentials for a service"""
    try:
        success = await credential_manager.delete_credential(service_name)
        
        if success:
            logger.info(f"Deleted credentials for {service_name} for user {current_user.id}")
            return {"message": f"Credentials for {service_name} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credentials for {service_name} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credentials for {service_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete credentials for {service_name}"
        )

@router.post("/cost/estimate", response_model=Dict[str, Any])
async def estimate_validation_cost(
    request: CostEstimationRequest,
    current_user: User = Depends(get_current_user)
):
    """Estimate cost for a validation request"""
    try:
        # Validate profile
        try:
            profile = CostProfile(request.profile.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid profile. Must be one of: demo, development, production"
            )
        
        cost_manager = AWSCostManager(profile)
        estimate = await cost_manager.estimate_validation_cost(
            business_concept=request.business_concept,
            analysis_scope=request.analysis_scope,
            target_market=request.target_market
        )
        
        # Get optimization recommendations
        recommendations = cost_manager.get_cost_optimization_recommendations()
        
        return {
            "estimate": estimate.to_dict(),
            "recommendations": recommendations,
            "profile_used": profile.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate validation cost"
        )

@router.post("/budget/set")
async def set_budget_limits(
    budget_request: BudgetLimitsRequest,
    current_user: User = Depends(get_current_user)
):
    """Set budget limits and guardrails"""
    try:
        # Store budget limits (in a real implementation, this would be stored per user)
        budget_config = {
            "max_daily_spend": budget_request.max_daily_spend,
            "max_monthly_spend": budget_request.max_monthly_spend,
            "max_per_validation": budget_request.max_per_validation,
            "alert_threshold_percent": budget_request.alert_threshold_percent,
            "auto_throttle_enabled": budget_request.auto_throttle_enabled,
            "user_id": current_user.id
        }
        
        # Store in credential manager as a special configuration
        config = CredentialConfig(
            service_name="budget_limits",
            api_key="budget_config",
            region="global",
            additional_config=budget_config
        )
        await credential_manager.store_credential("budget_limits", config)
        
        logger.info(f"Budget limits set for user {current_user.id}")
        
        return {
            "message": "Budget limits configured successfully",
            "limits": budget_config
        }
        
    except Exception as e:
        logger.error(f"Failed to set budget limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set budget limits"
        )

@router.get("/budget/current")
async def get_current_budget_usage(
    current_user: User = Depends(get_current_user)
):
    """Get current budget usage and limits"""
    try:
        # Get budget limits
        budget_config = credential_manager.get_credential("budget_limits")
        if not budget_config:
            return {
                "limits": None,
                "usage": {"daily": 0.0, "monthly": 0.0},
                "alerts": []
            }
        
        limits = budget_config.additional_config
        
        # Mock current usage (in real implementation, this would come from cost tracking)
        current_usage = {
            "daily": 5.25,
            "monthly": 45.80,
            "validations_today": 3,
            "validations_this_month": 12
        }
        
        # Calculate alert status
        alerts = []
        daily_percent = (current_usage["daily"] / limits["max_daily_spend"]) * 100
        monthly_percent = (current_usage["monthly"] / limits["max_monthly_spend"]) * 100
        
        if daily_percent > limits["alert_threshold_percent"]:
            alerts.append({
                "type": "daily_threshold",
                "message": f"Daily usage is {daily_percent:.1f}% of limit",
                "severity": "warning"
            })
        
        if monthly_percent > limits["alert_threshold_percent"]:
            alerts.append({
                "type": "monthly_threshold",
                "message": f"Monthly usage is {monthly_percent:.1f}% of limit",
                "severity": "warning"
            })
        
        return {
            "limits": limits,
            "usage": current_usage,
            "usage_percentages": {
                "daily": daily_percent,
                "monthly": monthly_percent
            },
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to get budget usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get budget usage"
        )

# Helper functions

async def validate_aws_credentials(access_key_id: str, secret_access_key: str, region: str) -> Dict[str, Any]:
    """Validate AWS credentials by making test API calls"""
    try:
        # Create boto3 client with provided credentials
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        
        # Test STS (Security Token Service) to validate credentials
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        
        # Test Bedrock access
        bedrock_client = session.client('bedrock', region_name=region)
        try:
            models = bedrock_client.list_foundation_models()
            bedrock_access = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                bedrock_access = False
            else:
                raise
        
        permissions = ["sts:GetCallerIdentity"]
        if bedrock_access:
            permissions.append("bedrock:ListFoundationModels")
        
        return {
            "valid": True,
            "account_id": identity.get("Account"),
            "user_arn": identity.get("Arn"),
            "permissions": permissions
        }
        
    except NoCredentialsError:
        return {
            "valid": False,
            "error_message": "Invalid credentials provided"
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidUserID.NotFound':
            return {
                "valid": False,
                "error_message": "Access key ID not found"
            }
        elif error_code == 'SignatureDoesNotMatch':
            return {
                "valid": False,
                "error_message": "Invalid secret access key"
            }
        else:
            return {
                "valid": False,
                "error_message": f"AWS API error: {error_code}"
            }
    except Exception as e:
        return {
            "valid": False,
            "error_message": f"Validation error: {str(e)}"
        }

async def validate_external_api_key(service_name: str, api_key: str) -> Dict[str, Any]:
    """Validate external API keys"""
    # For now, just check if the key is not empty and has reasonable length
    # In a real implementation, you would make test API calls to each service
    
    if not api_key or len(api_key.strip()) < 8:
        return {
            "valid": False,
            "error_message": "API key is too short or empty"
        }
    
    # Service-specific validation could be added here
    service_validators = {
        "alpha_vantage": lambda key: len(key) >= 16,
        "news_api": lambda key: len(key) >= 32,
        "twitter_api": lambda key: len(key) >= 25,
        "crunchbase": lambda key: len(key) >= 20
    }
    
    validator = service_validators.get(service_name.lower())
    if validator and not validator(api_key):
        return {
            "valid": False,
            "error_message": f"Invalid API key format for {service_name}"
        }
    
    return {
        "valid": True,
        "message": f"API key format is valid for {service_name}"
    }
