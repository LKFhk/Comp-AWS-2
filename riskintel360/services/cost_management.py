"""
AWS Cost Management Service for RiskIntel360 Platform
Provides cost estimation, optimization, and guardrails for AWS services.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import boto3
from decimal import Decimal

from .credential_manager import credential_manager

logger = logging.getLogger(__name__)

class UsageMetrics:
    """Simple usage metrics tracker"""
    def __init__(self):
        self.current_daily_cost = Decimal('0.0')
        self.current_monthly_cost = Decimal('0.0')
        self.validations_today = 0
        self.validations_this_month = 0

class CostProfile(Enum):
    """Cost optimization profiles"""
    DEMO = "demo"
    DEVELOPMENT = "development"
    PRODUCTION = "production"

class ModelTier(Enum):
    """AWS Bedrock model tiers"""
    BASIC = "basic"      # Haiku models
    STANDARD = "standard"  # Sonnet models  
    PREMIUM = "premium"   # Opus models

@dataclass
class CostEstimate:
    """Cost estimation result"""
    total_cost_usd: float
    bedrock_cost: float
    compute_cost: float
    storage_cost: float
    data_transfer_cost: float
    estimated_duration_minutes: int
    confidence_score: float
    profile: CostProfile
    
    def to_dict(self) -> Dict:
        return {
            'total_cost_usd': self.total_cost_usd,
            'bedrock_cost': self.bedrock_cost,
            'compute_cost': self.compute_cost,
            'storage_cost': self.storage_cost,
            'data_transfer_cost': self.data_transfer_cost,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'confidence_score': self.confidence_score,
            'profile': self.profile.value
        }

@dataclass
class CostGuardrails:
    """Cost guardrails configuration"""
    max_daily_spend: float
    max_monthly_spend: float
    max_per_validation: float
    alert_threshold_percent: float
    auto_throttle_enabled: bool
    
class AWSCostManager:
    """AWS Cost Management and Optimization Service"""
    
    # AWS Service Pricing (USD)
    PRICING = {
        'bedrock': {
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'claude-3-opus': {'input': 0.015, 'output': 0.075}
        },
        'ecs_fargate': {
            'vcpu_hour': 0.04048,
            'memory_gb_hour': 0.004445
        },
        'aurora_serverless': {
            'acu_hour': 0.06,
            'storage_gb_month': 0.10
        },
        'api_gateway': {
            'request': 0.0000035,
            'data_transfer_gb': 0.09
        },
        's3': {
            'storage_gb_month': 0.023,
            'requests_1k': 0.0005
        }
    }
    
    # Cost profiles with different optimization strategies
    COST_PROFILES = {
        CostProfile.DEMO: {
            'model_tier': ModelTier.BASIC,
            'compute_scale': 0.5,
            'storage_optimization': True,
            'max_concurrent_agents': 3,
            'timeout_minutes': 30
        },
        CostProfile.DEVELOPMENT: {
            'model_tier': ModelTier.STANDARD,
            'compute_scale': 0.8,
            'storage_optimization': True,
            'max_concurrent_agents': 6,
            'timeout_minutes': 60
        },
        CostProfile.PRODUCTION: {
            'model_tier': ModelTier.PREMIUM,
            'compute_scale': 1.0,
            'storage_optimization': False,
            'max_concurrent_agents': 12,
            'timeout_minutes': 120
        }
    }
    
    def __init__(self, profile: CostProfile = CostProfile.DEVELOPMENT):
        self.profile = profile
        self.config = self.COST_PROFILES[profile]
        self.guardrails = self._get_default_guardrails()
        self.current_spend = {'daily': 0.0, 'monthly': 0.0}
        
    def _get_default_guardrails(self) -> CostGuardrails:
        """Get default cost guardrails based on profile"""
        if self.profile == CostProfile.DEMO:
            return CostGuardrails(
                max_daily_spend=10.0,
                max_monthly_spend=100.0,
                max_per_validation=2.0,
                alert_threshold_percent=80.0,
                auto_throttle_enabled=True
            )
        elif self.profile == CostProfile.DEVELOPMENT:
            return CostGuardrails(
                max_daily_spend=50.0,
                max_monthly_spend=500.0,
                max_per_validation=10.0,
                alert_threshold_percent=85.0,
                auto_throttle_enabled=True
            )
        else:  # PRODUCTION
            return CostGuardrails(
                max_daily_spend=200.0,
                max_monthly_spend=2000.0,
                max_per_validation=50.0,
                alert_threshold_percent=90.0,
                auto_throttle_enabled=False
            )
    
    async def estimate_validation_cost(
        self,
        business_concept: str,
        analysis_scope: List[str],
        target_market: str
    ) -> CostEstimate:
        """Estimate cost for a validation request"""
        
        # Determine complexity
        complexity_score = self._calculate_complexity(
            business_concept, analysis_scope, target_market
        )
        
        # Estimate token usage based on complexity
        estimated_tokens = self._estimate_token_usage(complexity_score, analysis_scope)
        
        # Calculate costs by service
        bedrock_cost = self._calculate_bedrock_cost(estimated_tokens)
        compute_cost = self._calculate_compute_cost(complexity_score)
        storage_cost = self._calculate_storage_cost(complexity_score)
        data_transfer_cost = self._calculate_data_transfer_cost(complexity_score)
        
        total_cost = bedrock_cost + compute_cost + storage_cost + data_transfer_cost
        
        # Apply profile optimizations
        total_cost *= self.config['compute_scale']
        
        # Apply profile-specific cost multipliers
        if self.profile == CostProfile.DEMO:
            total_cost *= 0.4  # 60% cost reduction for demo
        elif self.profile == CostProfile.DEVELOPMENT:
            total_cost *= 0.8  # 20% cost reduction for development
        # Production uses full cost
        
        # Estimate duration
        duration_minutes = int(30 * complexity_score * self.config['compute_scale'])
        
        return CostEstimate(
            total_cost_usd=round(total_cost, 4),
            bedrock_cost=round(bedrock_cost, 4),
            compute_cost=round(compute_cost, 4),
            storage_cost=round(storage_cost, 4),
            data_transfer_cost=round(data_transfer_cost, 4),
            estimated_duration_minutes=duration_minutes,
            confidence_score=0.85,
            profile=self.profile
        )
    
    def _calculate_complexity(
        self, 
        business_concept: str, 
        analysis_scope: List[str], 
        target_market: str
    ) -> float:
        """Calculate complexity score (1.0 - 3.0)"""
        score = 1.5  # Base complexity
        
        # Analysis scope complexity
        scope_weights = {
            'market': 0.3,
            'competitive': 0.4,
            'financial': 0.5,
            'risk': 0.3,
            'customer': 0.3,
            'regulatory': 0.6
        }
        
        for scope in analysis_scope:
            score += scope_weights.get(scope.lower(), 0.2)
        
        # Business concept complexity
        concept_lower = business_concept.lower()
        if any(term in concept_lower for term in ['ai', 'ml', 'blockchain']):
            score += 0.8
        if any(term in concept_lower for term in ['enterprise', 'b2b']):
            score += 0.5
        if any(term in concept_lower for term in ['platform', 'marketplace']):
            score += 0.4
        
        # Market complexity
        market_lower = target_market.lower()
        if any(term in market_lower for term in ['global', 'international']):
            score += 0.6
        if any(term in market_lower for term in ['enterprise', 'fortune']):
            score += 0.3
        
        return min(score, 3.0)
    
    def _estimate_token_usage(self, complexity: float, analysis_scope: List[str]) -> Dict[str, int]:
        """Estimate token usage by model type"""
        base_tokens = {
            'input': 5000,
            'output': 2000
        }
        
        # Scale by complexity and scope
        multiplier = complexity * len(analysis_scope) * 0.3
        
        return {
            'input': int(base_tokens['input'] * multiplier),
            'output': int(base_tokens['output'] * multiplier)
        }
    
    def _calculate_bedrock_cost(self, tokens: Dict[str, int]) -> float:
        """Calculate Bedrock Nova costs"""
        model_tier = self.config['model_tier']
        
        if model_tier == ModelTier.BASIC:
            model_key = 'claude-3-haiku'
        elif model_tier == ModelTier.STANDARD:
            model_key = 'claude-3-sonnet'
        else:
            model_key = 'claude-3-opus'
        
        pricing = self.PRICING['bedrock'][model_key]
        
        input_cost = (tokens['input'] / 1000) * pricing['input']
        output_cost = (tokens['output'] / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def _calculate_compute_cost(self, complexity: float) -> float:
        """Calculate ECS Fargate compute costs"""
        # Estimate compute time based on complexity
        hours = (complexity * 0.5) * self.config['compute_scale']
        
        # Assume 2 vCPU, 4GB memory per agent
        vcpu_cost = hours * 2 * self.PRICING['ecs_fargate']['vcpu_hour']
        memory_cost = hours * 4 * self.PRICING['ecs_fargate']['memory_gb_hour']
        
        return vcpu_cost + memory_cost
    
    def _calculate_storage_cost(self, complexity: float) -> float:
        """Calculate Aurora Serverless storage costs"""
        # Estimate storage usage
        storage_gb = complexity * 0.1  # Small storage footprint
        acu_hours = complexity * 0.25
        
        storage_cost = storage_gb * self.PRICING['aurora_serverless']['storage_gb_month'] / 30
        compute_cost = acu_hours * self.PRICING['aurora_serverless']['acu_hour']
        
        return storage_cost + compute_cost
    
    def _calculate_data_transfer_cost(self, complexity: float) -> float:
        """Calculate data transfer costs"""
        # Estimate API calls and data transfer
        api_calls = int(complexity * 1000)
        data_gb = complexity * 0.01
        
        api_cost = api_calls * self.PRICING['api_gateway']['request']
        transfer_cost = data_gb * self.PRICING['api_gateway']['data_transfer_gb']
        
        return api_cost + transfer_cost
    
    async def check_cost_guardrails(self, estimated_cost: float) -> Tuple[bool, str]:
        """Check if request passes cost guardrails"""
        
        # Check per-validation limit
        if estimated_cost > self.guardrails.max_per_validation:
            return False, f"Cost ${estimated_cost:.2f} exceeds per-validation limit ${self.guardrails.max_per_validation:.2f}"
        
        # Check daily spend limit
        projected_daily = self.current_spend['daily'] + estimated_cost
        if projected_daily > self.guardrails.max_daily_spend:
            return False, f"Would exceed daily spend limit ${self.guardrails.max_daily_spend:.2f}"
        
        # Check monthly spend limit
        projected_monthly = self.current_spend['monthly'] + estimated_cost
        if projected_monthly > self.guardrails.max_monthly_spend:
            return False, f"Would exceed monthly spend limit ${self.guardrails.max_monthly_spend:.2f}"
        
        # Check alert thresholds
        daily_percent = (projected_daily / self.guardrails.max_daily_spend) * 100
        if daily_percent > self.guardrails.alert_threshold_percent:
            return True, f"Warning: {daily_percent:.1f}% of daily budget"
        
        return True, "Within cost limits"
    
    def get_optimal_model_selection(self, complexity: float, budget: float) -> str:
        """Select optimal model based on complexity and budget"""
        
        # Calculate costs for each model tier
        base_tokens = {'input': 5000, 'output': 2000}
        
        costs = {}
        for tier, model_key in [
            (ModelTier.BASIC, 'claude-3-haiku'),
            (ModelTier.STANDARD, 'claude-3-sonnet'),
            (ModelTier.PREMIUM, 'claude-3-opus')
        ]:
            pricing = self.PRICING['bedrock'][model_key]
            cost = ((base_tokens['input'] / 1000) * pricing['input'] + 
                   (base_tokens['output'] / 1000) * pricing['output'])
            costs[tier] = cost
        
        # Select best model within budget
        if budget >= costs[ModelTier.PREMIUM] and complexity > 2.0:
            return 'claude-3-opus'
        elif budget >= costs[ModelTier.STANDARD] and complexity > 1.5:
            return 'claude-3-sonnet'
        else:
            return 'claude-3-haiku'
    
    async def record_actual_cost(self, validation_id: str, actual_cost: float):
        """Record actual cost for tracking"""
        self.current_spend['daily'] += actual_cost
        self.current_spend['monthly'] += actual_cost
        
        logger.info(f"Recorded cost ${actual_cost:.4f} for validation {validation_id}")
    
    def get_cost_optimization_recommendations(self) -> List[str]:
        """Get cost optimization recommendations"""
        recommendations = []
        
        if self.profile == CostProfile.PRODUCTION:
            recommendations.extend([
                "Consider using Reserved Instances for predictable workloads",
                "Enable Aurora Serverless v2 for better cost optimization",
                "Use S3 Intelligent Tiering for storage optimization"
            ])
        
        if self.profile == CostProfile.DEVELOPMENT:
            recommendations.extend([
                "Switch to Demo profile for testing to reduce costs",
                "Use smaller model tiers for non-critical validations",
                "Enable auto-scaling to optimize compute costs"
            ])
        
        if self.profile == CostProfile.DEMO:
            recommendations.extend([
                "Demo profile active - costs are optimized for testing",
                "Consider caching results to reduce repeated API calls",
                "Use batch processing for multiple validations"
            ])
        
        return recommendations

@dataclass
class ServiceCosts:
    """Detailed service cost breakdown"""
    bedrock_cost: float = 0.0
    ecs_cost: float = 0.0
    aurora_cost: float = 0.0
    elasticache_cost: float = 0.0
    api_gateway_cost: float = 0.0
    s3_cost: float = 0.0
    cloudwatch_cost: float = 0.0
    
    @property
    def total_cost(self) -> float:
        return (self.bedrock_cost + self.ecs_cost + self.aurora_cost + 
                self.elasticache_cost + self.api_gateway_cost + 
                self.s3_cost + self.cloudwatch_cost)

@dataclass
class DetailedCostEstimate:
    """Detailed cost estimation with service breakdown"""
    total_cost: Decimal
    service_costs: ServiceCosts
    estimated_duration_hours: float
    confidence_level: float
    profile_used: CostProfile
    model_selection: Dict[str, str]
    optimization_recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_cost': self.total_cost,
            'service_costs': asdict(self.service_costs),
            'estimated_duration_hours': self.estimated_duration_hours,
            'confidence_level': self.confidence_level,
            'profile_used': self.profile_used.value,
            'model_selection': self.model_selection,
            'optimization_recommendations': self.optimization_recommendations
        }

class CostProfileManager:
    """Manages cost profiles and configurations"""
    
    def __init__(self, estimation_engine=None):
        self.estimation_engine = estimation_engine
        self.profiles = {
            CostProfile.DEMO: {
                'description': 'Optimized for demos and testing with minimal costs',
                'model_selection': {
                    'market_analysis': 'claude-3-haiku',
                    'regulatory_compliance': 'claude-3-haiku',
                    'fraud_detection': 'claude-3-haiku',
                    'risk_assessment': 'claude-3-haiku',
                    'customer_behavior_intelligence': 'claude-3-haiku',
                    'kyc_verification': 'claude-3-haiku'
                },
                'token_limits': {
                    'max_input_tokens': 50000,
                    'max_output_tokens': 2000
                },
                'parallel_execution': False,
                'caching_enabled': True,
                'max_concurrent_agents': 2,
                'timeout_minutes': 30,
                'compute_scale': 0.3
            },
            CostProfile.DEVELOPMENT: {
                'description': 'Balanced performance and cost for development',
                'model_selection': {
                    'market_analysis': 'claude-3-haiku',
                    'regulatory_compliance': 'claude-3-sonnet',
                    'fraud_detection': 'claude-3-sonnet',
                    'risk_assessment': 'claude-3-sonnet',
                    'customer_behavior_intelligence': 'claude-3-haiku',
                    'kyc_verification': 'claude-3-opus'
                },
                'token_limits': {
                    'max_input_tokens': 100000,
                    'max_output_tokens': 4000
                },
                'parallel_execution': True,
                'caching_enabled': True,
                'max_concurrent_agents': 4,
                'timeout_minutes': 60,
                'compute_scale': 0.7
            },
            CostProfile.PRODUCTION: {
                'description': 'Maximum performance for production workloads',
                'model_selection': {
                    'market_analysis': 'claude-3-haiku',
                    'regulatory_compliance': 'claude-3-sonnet',
                    'fraud_detection': 'claude-3-opus',
                    'risk_assessment': 'claude-3-sonnet',
                    'customer_behavior_intelligence': 'claude-3-haiku',
                    'kyc_verification': 'claude-3-opus'
                },
                'token_limits': {
                    'max_input_tokens': 200000,
                    'max_output_tokens': 8000
                },
                'parallel_execution': True,
                'caching_enabled': False,
                'max_concurrent_agents': 8,
                'timeout_minutes': 120,
                'compute_scale': 1.0
            }
        }
    
    def get_profile_config(self, profile: CostProfile) -> Dict[str, Any]:
        """Get configuration for a cost profile"""
        return self.profiles.get(profile, self.profiles[CostProfile.DEVELOPMENT])
    
    def get_model_selection(self, profile: CostProfile) -> Dict[str, str]:
        """Get model selection for a profile"""
        config = self.get_profile_config(profile)
        return config.get('model_selection', {})
    
    async def estimate_profile_cost(self, profile: CostProfile) -> DetailedCostEstimate:
        """Estimate cost for a profile"""
        if self.estimation_engine:
            # Use the estimation engine if available
            config = self.get_profile_config(profile)
            model_selection = config.get('model_selection', {})
            
            # Estimate based on model usage
            total_cost = Decimal('0.0')
            service_costs = {}
            
            for agent, model in model_selection.items():
                # Simple cost estimation based on model type
                if 'haiku' in model:
                    cost = Decimal('10.0')  # $10 per agent for haiku
                elif 'sonnet' in model:
                    cost = Decimal('25.0')  # $25 per agent for sonnet
                elif 'opus' in model:
                    cost = Decimal('50.0')  # $50 per agent for opus
                else:
                    cost = Decimal('15.0')  # Default cost
                
                service_costs[agent] = cost
                total_cost += cost
            
            # Create ServiceCosts object
            service_costs_obj = ServiceCosts(
                bedrock_cost=float(total_cost * Decimal('0.8')),
                ecs_cost=float(Decimal('5.0')),
                aurora_cost=float(Decimal('2.0')),
                elasticache_cost=float(Decimal('1.0')),
                api_gateway_cost=float(Decimal('0.5')),
                s3_cost=float(Decimal('1.0')),
                cloudwatch_cost=float(Decimal('0.5'))
            )
            
            return DetailedCostEstimate(
                total_cost=total_cost,
                service_costs=service_costs_obj,
                estimated_duration_hours=2.0,
                confidence_level=0.85,
                profile_used=profile,
                model_selection=model_selection,
                optimization_recommendations=["Use caching to reduce costs", "Consider batch processing"]
            )
        else:
            # Fallback estimation
            if profile == CostProfile.DEMO:
                base_cost = Decimal('50.0')
            elif profile == CostProfile.DEVELOPMENT:
                base_cost = Decimal('150.0')
            elif profile == CostProfile.PRODUCTION:
                base_cost = Decimal('300.0')
            else:
                base_cost = Decimal('100.0')
            
            # Create ServiceCosts object
            service_costs_obj = ServiceCosts(
                bedrock_cost=float(base_cost * Decimal('0.8')),
                ecs_cost=float(base_cost * Decimal('0.1')),
                aurora_cost=float(base_cost * Decimal('0.05')),
                elasticache_cost=float(base_cost * Decimal('0.02')),
                api_gateway_cost=float(base_cost * Decimal('0.01')),
                s3_cost=float(base_cost * Decimal('0.01')),
                cloudwatch_cost=float(base_cost * Decimal('0.01'))
            )
            
            return DetailedCostEstimate(
                total_cost=base_cost,
                service_costs=service_costs_obj,
                estimated_duration_hours=2.0,
                confidence_level=0.8,
                profile_used=profile,
                model_selection={},
                optimization_recommendations=["Consider upgrading to development profile for better performance"]
            )

class CostGuardrailManager:
    """Manages cost guardrails and limits"""
    
    def __init__(self, profile: CostProfile):
        self.profile = profile
        self.guardrails = self._get_default_guardrails(profile)
        self.current_usage = {
            'daily_cost': 0.0,
            'monthly_cost': 0.0,
            'validations_today': 0,
            'validations_this_month': 0,
            'last_reset_date': datetime.now(timezone.utc).date()
        }
    
    def _get_default_guardrails(self, profile: CostProfile) -> CostGuardrails:
        """Get default guardrails for profile"""
        if profile == CostProfile.DEMO:
            return CostGuardrails(
                max_daily_spend=5.0,
                max_monthly_spend=50.0,
                max_per_validation=1.0,
                alert_threshold_percent=80.0,
                auto_throttle_enabled=True
            )
        elif profile == CostProfile.DEVELOPMENT:
            return CostGuardrails(
                max_daily_spend=25.0,
                max_monthly_spend=250.0,
                max_per_validation=5.0,
                alert_threshold_percent=85.0,
                auto_throttle_enabled=True
            )
        else:  # PRODUCTION
            return CostGuardrails(
                max_daily_spend=100.0,
                max_monthly_spend=1000.0,
                max_per_validation=25.0,
                alert_threshold_percent=90.0,
                auto_throttle_enabled=False
            )
    
    async def check_validation_allowed(self, estimated_cost: float) -> Dict[str, Any]:
        """Check if validation is allowed based on guardrails"""
        self._reset_usage_if_needed()
        
        warnings = []
        actions = []
        allowed = True
        
        # Convert estimated_cost to float if it's Decimal
        if hasattr(estimated_cost, '__float__'):
            estimated_cost = float(estimated_cost)
        
        # Check per-validation limit
        if estimated_cost > self.guardrails.max_per_validation:
            allowed = False
            warnings.append(f"Cost ${estimated_cost:.2f} exceeds per-validation limit ${self.guardrails.max_per_validation:.2f}")
            actions.append(f"Reduce scope or switch to lower cost profile")
            return {
                'allowed': False,
                'reason': f'Cost ${estimated_cost:.2f} exceeds per-validation limit ${self.guardrails.max_per_validation:.2f}',
                'warnings': warnings,
                'actions': actions
            }
        
        # Check daily limit
        projected_daily = self.current_usage['daily_cost'] + estimated_cost
        if projected_daily > self.guardrails.max_daily_spend:
            allowed = False
            warnings.append(f"Would exceed daily limit ${self.guardrails.max_daily_spend:.2f}")
            actions.append("Wait until tomorrow or increase daily limit")
            return {
                'allowed': False,
                'reason': f'Would exceed daily limit ${self.guardrails.max_daily_spend:.2f}',
                'warnings': warnings,
                'actions': actions
            }
        
        # Check monthly limit
        projected_monthly = self.current_usage['monthly_cost'] + estimated_cost
        if projected_monthly > self.guardrails.max_monthly_spend:
            allowed = False
            warnings.append(f"Would exceed monthly limit ${self.guardrails.max_monthly_spend:.2f}")
            actions.append("Wait until next month or increase monthly limit")
            return {
                'allowed': False,
                'reason': f'Would exceed monthly limit ${self.guardrails.max_monthly_spend:.2f}',
                'warnings': warnings,
                'actions': actions
            }
        
        # Check alert thresholds
        daily_percent = (projected_daily / self.guardrails.max_daily_spend) * 100
        monthly_percent = (projected_monthly / self.guardrails.max_monthly_spend) * 100
        
        if daily_percent > self.guardrails.alert_threshold_percent:
            warnings.append(f"Daily usage will be {daily_percent:.1f}% of limit")
            actions.append("Consider switching to a lower cost profile")
        
        if monthly_percent > self.guardrails.alert_threshold_percent:
            warnings.append(f"Monthly usage will be {monthly_percent:.1f}% of limit")
            actions.append("Monitor usage closely")
        
        return {
            'allowed': allowed,
            'warnings': warnings,
            'actions': actions
        }
    
    def _reset_usage_if_needed(self):
        """Reset usage counters if date has changed"""
        today = datetime.now(timezone.utc).date()
        
        if today != self.current_usage['last_reset_date']:
            # Reset daily counters
            self.current_usage['daily_cost'] = 0.0
            self.current_usage['validations_today'] = 0
            
            # Reset monthly counters if month changed
            if today.month != self.current_usage['last_reset_date'].month:
                self.current_usage['monthly_cost'] = 0.0
                self.current_usage['validations_this_month'] = 0
            
            self.current_usage['last_reset_date'] = today
    
    async def record_usage(self, cost: float):
        """Record actual usage"""
        self._reset_usage_if_needed()
        
        self.current_usage['daily_cost'] += cost
        self.current_usage['monthly_cost'] += cost
        self.current_usage['validations_today'] += 1
        self.current_usage['validations_this_month'] += 1
        
        logger.info(f"Recorded usage: ${cost:.4f} (Daily: ${self.current_usage['daily_cost']:.4f}, Monthly: ${self.current_usage['monthly_cost']:.4f})")

class RealTimeCostTracker:
    """Real-time cost tracking with AWS Cost Explorer integration"""
    
    def __init__(self):
        self.cost_explorer_client = None
        self._initialize_aws_client()
    
    def _initialize_aws_client(self):
        """Initialize AWS Cost Explorer client"""
        try:
            aws_config = credential_manager.get_aws_config()
            if aws_config and aws_config.get('aws_access_key_id'):
                self.cost_explorer_client = boto3.client(
                    'ce',
                    **aws_config
                )
                logger.info("AWS Cost Explorer client initialized")
            else:
                logger.warning("AWS credentials not available, using mock cost tracking")
        except Exception as e:
            logger.warning(f"Failed to initialize Cost Explorer client: {e}")
    
    async def get_current_month_costs(self) -> Dict[str, float]:
        """Get current month costs from AWS"""
        if not self.cost_explorer_client:
            return self._get_mock_costs()
        
        try:
            today = datetime.now(timezone.utc)
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
            
            response = self.cost_explorer_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            costs = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    costs[service.lower().replace(' ', '_')] = amount
            
            return costs
            
        except Exception as e:
            logger.error(f"Failed to get AWS costs: {e}")
            return self._get_mock_costs()
    
    def _get_mock_costs(self) -> Dict[str, float]:
        """Get mock costs for development/testing"""
        return {
            'bedrock': 15.50,
            'ecs': 8.25,
            'aurora': 12.75,
            'elasticache': 5.50,
            'api_gateway': 2.25,
            's3': 1.75,
            'cloudwatch': 3.25
        }

class CostOptimizer:
    """Cost optimization engine"""
    
    def __init__(self, profile_manager: CostProfileManager):
        self.profile_manager = profile_manager
    
    def get_optimization_recommendations(
        self, 
        current_profile: CostProfile,
        usage_pattern: Dict[str, Any]
    ) -> List[str]:
        """Get cost optimization recommendations"""
        recommendations = []
        
        # Profile-specific recommendations
        if current_profile == CostProfile.PRODUCTION:
            recommendations.extend([
                "Consider using Reserved Instances for predictable workloads",
                "Enable Aurora Serverless v2 for better cost optimization",
                "Use S3 Intelligent Tiering for storage optimization",
                "Implement CloudWatch cost anomaly detection"
            ])
        
        if current_profile == CostProfile.DEVELOPMENT:
            recommendations.extend([
                "Switch to Demo profile for testing to reduce costs by 70%",
                "Use smaller model tiers for non-critical validations",
                "Enable auto-scaling to optimize compute costs",
                "Consider batch processing for multiple validations"
            ])
        
        if current_profile == CostProfile.DEMO:
            recommendations.extend([
                "Demo profile active - costs are optimized for testing",
                "Consider caching results to reduce repeated API calls",
                "Use sequential processing to minimize peak usage",
                "Pre-cache common demo scenarios"
            ])
        
        # Usage-based recommendations
        daily_cost = usage_pattern.get('daily_cost', 0)
        monthly_cost = usage_pattern.get('monthly_cost', 0)
        
        if daily_cost > 20:
            recommendations.append("High daily usage detected - consider cost optimization")
        
        if monthly_cost > 200:
            recommendations.append("High monthly usage - review model selection strategy")
        
        return recommendations
    
    def suggest_profile_switch(
        self, 
        current_profile: CostProfile,
        usage_pattern: Dict[str, Any]
    ) -> Optional[CostProfile]:
        """Suggest profile switch based on usage"""
        daily_cost = usage_pattern.get('daily_cost', 0)
        validations_today = usage_pattern.get('validations_today', 0)
        
        # If low usage, suggest demo profile
        if daily_cost < 2 and validations_today < 5 and current_profile != CostProfile.DEMO:
            return CostProfile.DEMO
        
        # If high usage but on demo, suggest development
        if daily_cost > 4 and current_profile == CostProfile.DEMO:
            return CostProfile.DEVELOPMENT
        
        # If very high usage, suggest production
        if daily_cost > 15 and current_profile != CostProfile.PRODUCTION:
            return CostProfile.PRODUCTION
        
        return None

class CostManagementService:
    """Main cost management service"""
    
    def __init__(self, initial_profile: CostProfile = CostProfile.DEVELOPMENT):
        self.current_profile = initial_profile
        self.profile_manager = CostProfileManager()
        self.guardrail_manager = CostGuardrailManager(initial_profile)
        self.cost_tracker = RealTimeCostTracker()
        self.optimizer = CostOptimizer(self.profile_manager)
        self.cost_estimator = AWSCostManager(initial_profile)
        # Add missing attributes for backward compatibility
        from .credential_manager import credential_manager
        self.credential_manager = credential_manager
        self.cost_controller = CostController(credential_manager, self.guardrail_manager)
        self.estimation_engine = CostEstimationEngine()
        
    async def initialize(self):
        """Initialize the cost management service"""
        logger.info(f"Initializing cost management service with profile: {self.current_profile.value}")
        
        # Load current usage from tracking
        try:
            current_costs = await self.cost_tracker.get_current_month_costs()
            total_monthly = sum(current_costs.values())
            
            # Update guardrail manager with actual usage
            self.guardrail_manager.current_usage['monthly_cost'] = total_monthly
            
            logger.info(f"Loaded current month costs: ${total_monthly:.2f}")
            
        except Exception as e:
            logger.warning(f"Failed to load current costs: {e}")
    
    async def estimate_validation_cost(
        self, 
        profile: Optional[CostProfile] = None
    ) -> DetailedCostEstimate:
        """Estimate cost for validation with detailed breakdown"""
        
        target_profile = profile or self.current_profile
        
        # Create a temporary cost estimator for the target profile
        temp_estimator = AWSCostManager(target_profile)
        basic_estimate = await temp_estimator.estimate_validation_cost(
            business_concept="Sample business concept",
            analysis_scope=["market", "competitive", "financial", "risk", "customer"],
            target_market="Enterprise B2B"
        )
        
        # Get profile configuration
        profile_config = self.profile_manager.get_profile_config(target_profile)
        model_selection = profile_config['model_selection']
        
        # Calculate detailed service costs
        service_costs = ServiceCosts(
            bedrock_cost=basic_estimate.bedrock_cost,
            ecs_cost=basic_estimate.compute_cost * 0.6,
            aurora_cost=basic_estimate.storage_cost * 0.7,
            elasticache_cost=basic_estimate.storage_cost * 0.3,
            api_gateway_cost=basic_estimate.data_transfer_cost * 0.8,
            s3_cost=basic_estimate.storage_cost * 0.1,
            cloudwatch_cost=basic_estimate.data_transfer_cost * 0.2
        )
        
        # Get optimization recommendations
        usage_pattern = {
            'daily_cost': self.guardrail_manager.current_usage['daily_cost'],
            'monthly_cost': self.guardrail_manager.current_usage['monthly_cost'],
            'validations_today': self.guardrail_manager.current_usage['validations_today']
        }
        
        recommendations = self.optimizer.get_optimization_recommendations(
            target_profile, usage_pattern
        )
        
        return DetailedCostEstimate(
            total_cost=Decimal(str(service_costs.total_cost)),
            service_costs=service_costs,
            estimated_duration_hours=basic_estimate.estimated_duration_minutes / 60.0,
            confidence_level=basic_estimate.confidence_score,
            profile_used=target_profile,
            model_selection=model_selection,
            optimization_recommendations=recommendations
        )
    
    async def check_validation_allowed(self, estimated_cost: float) -> Dict[str, Any]:
        """Check if validation is allowed based on guardrails"""
        return await self.guardrail_manager.check_validation_allowed(estimated_cost)
    
    async def record_actual_cost(self, validation_id: str, actual_cost: float):
        """Record actual cost for a validation"""
        await self.guardrail_manager.record_usage(actual_cost)
        logger.info(f"Recorded actual cost ${actual_cost:.4f} for validation {validation_id}")
    
    async def switch_profile(self, new_profile: CostProfile):
        """Switch to a different cost profile"""
        old_profile = self.current_profile
        self.current_profile = new_profile
        
        # Update guardrail manager
        self.guardrail_manager = CostGuardrailManager(new_profile)
        
        # Update cost estimator
        self.cost_estimator = AWSCostManager(new_profile)
        
        # Update cost controller to use new guardrail manager
        self.cost_controller = CostController(self.credential_manager, self.guardrail_manager)
        
        logger.info(f"Switched cost profile from {old_profile.value} to {new_profile.value}")
    
    async def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        # Don't reset usage when just getting summary to avoid losing recent updates
        # self.guardrail_manager._reset_usage_if_needed()
        
        return {
            'current_profile': self.current_profile.value,
            'daily_cost': self.guardrail_manager.current_usage['daily_cost'],
            'monthly_cost': self.guardrail_manager.current_usage['monthly_cost'],
            'validations_today': self.guardrail_manager.current_usage['validations_today'],
            'validations_this_month': self.guardrail_manager.current_usage['validations_this_month'],
            'daily_limit': self.guardrail_manager.guardrails.max_daily_spend,
            'monthly_limit': self.guardrail_manager.guardrails.max_monthly_spend,
            'per_validation_limit': self.guardrail_manager.guardrails.max_per_validation
        }
    
    async def get_model_selection(
        self, 
        profile: Optional[CostProfile] = None
    ) -> Dict[str, str]:
        """Get model selection for profile"""
        target_profile = profile or self.current_profile
        return self.profile_manager.get_model_selection(target_profile)
    
    async def store_api_key(self, service: str, key_type: str, value: str):
        """Store API key securely"""
        from .credential_manager import CredentialConfig
        
        config = CredentialConfig(
            service_name=service,
            api_key=value,
            region=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            additional_config={'key_type': key_type}
        )
        
        credential_manager.store_credential(service, config)
        logger.info(f"Stored API key for {service}.{key_type}")
    
    async def get_api_key(self, service: str, key_type: str) -> Optional[str]:
        """Retrieve API key"""
        config = credential_manager.get_credential(service)
        if config and config.additional_config.get('key_type') == key_type:
            return config.api_key
        return None
    
    async def list_configured_services(self) -> List[str]:
        """List services with stored credentials"""
        return await credential_manager.list_services()

# Global service instance
_cost_management_service: Optional[CostManagementService] = None

async def get_cost_management_service() -> CostManagementService:
    """Get or create cost management service instance"""
    global _cost_management_service
    
    if _cost_management_service is None:
        _cost_management_service = CostManagementService()
        await _cost_management_service.initialize()
    
    return _cost_management_service

# Additional classes for backward compatibility
class CostEstimationEngine:
    """Cost estimation engine for backward compatibility"""
    
    def __init__(self):
        self.cost_manager = AWSCostManager()
        # Add model pricing for backward compatibility
        class ModelPricing:
            def __init__(self, input_price, output_price):
                self.input_tokens_per_1k = Decimal(str(input_price))
                self.output_tokens_per_1k = Decimal(str(output_price))
        
        self.model_pricing = {
            "anthropic.claude-3-haiku-20240307-v1:0": ModelPricing(0.00025, 0.00125),
            "anthropic.claude-3-sonnet-20240229-v1:0": ModelPricing(0.003, 0.015),
            "anthropic.claude-3-opus-20240229-v1:0": ModelPricing(0.015, 0.075)
        }
    
    async def estimate_cost(self, **kwargs):
        """Estimate cost using the cost manager"""
        return await self.cost_manager.estimate_validation_cost(
            business_concept=kwargs.get('business_concept', 'Sample'),
            analysis_scope=kwargs.get('analysis_scope', ['market']),
            target_market=kwargs.get('target_market', 'Enterprise')
        )
    
    async def estimate_bedrock_cost(self, model_selection: Dict[str, str], estimated_tokens) -> Decimal:
        """Estimate Bedrock costs"""
        total_cost = 0.0
        
        for agent_type, model_name in model_selection.items():
            # Get token counts for this agent
            if isinstance(estimated_tokens, dict) and agent_type in estimated_tokens:
                # Test format: estimated_tokens[agent] = (input, output)
                if isinstance(estimated_tokens[agent_type], tuple):
                    input_tokens, output_tokens = estimated_tokens[agent_type]
                else:
                    # Fallback format
                    input_tokens = estimated_tokens.get('input', 5000)
                    output_tokens = estimated_tokens.get('output', 2000)
            else:
                # Default fallback
                input_tokens = estimated_tokens.get('input', 5000) if isinstance(estimated_tokens, dict) else 5000
                output_tokens = estimated_tokens.get('output', 2000) if isinstance(estimated_tokens, dict) else 2000
            
            # Get pricing from model_pricing (test format)
            if model_name in self.model_pricing:
                pricing = self.model_pricing[model_name]
                input_cost = (input_tokens / 1000) * float(pricing.input_tokens_per_1k)
                output_cost = (output_tokens / 1000) * float(pricing.output_tokens_per_1k)
            else:
                # Fallback to cost_manager pricing
                if 'haiku' in model_name.lower():
                    model_key = 'claude-3-haiku'
                elif 'sonnet' in model_name.lower():
                    model_key = 'claude-3-sonnet'
                else:
                    model_key = 'claude-3-opus'
                
                pricing = self.cost_manager.PRICING['bedrock'][model_key]
                input_cost = (input_tokens / 1000) * pricing['input']
                output_cost = (output_tokens / 1000) * pricing['output']
            
            total_cost += input_cost + output_cost
        
        return Decimal(str(total_cost))
    
    async def estimate_infrastructure_cost(self, duration_hours, concurrent_agents: int) -> Dict[str, Decimal]:
        """Estimate infrastructure costs"""
        # Convert duration_hours to float if it's Decimal
        if hasattr(duration_hours, '__float__'):
            duration_hours = float(duration_hours)
        
        # ECS Fargate costs
        ecs_cost = duration_hours * concurrent_agents * 2 * self.cost_manager.PRICING['ecs_fargate']['vcpu_hour']
        ecs_cost += duration_hours * concurrent_agents * 4 * self.cost_manager.PRICING['ecs_fargate']['memory_gb_hour']
        
        # Aurora costs
        aurora_cost = duration_hours * 0.25 * self.cost_manager.PRICING['aurora_serverless']['acu_hour']
        
        # S3 costs (minimal)
        s3_cost = 0.1 * self.cost_manager.PRICING['s3']['storage_gb_month'] / 30
        
        # ElastiCache costs (minimal)
        elasticache_cost = duration_hours * 0.1  # Minimal cache usage
        
        # API Gateway costs
        api_gateway_cost = concurrent_agents * 100 * self.cost_manager.PRICING['api_gateway']['request']
        
        # CloudWatch costs
        cloudwatch_cost = duration_hours * 0.05  # Minimal monitoring costs
        
        # Create a simple object with the expected attributes
        class InfrastructureCosts:
            def __init__(self, ecs, aurora, s3, elasticache, api_gateway, cloudwatch):
                self.ecs_cost = Decimal(str(ecs))
                self.aurora_cost = Decimal(str(aurora))
                self.s3_cost = Decimal(str(s3))
                self.elasticache_cost = Decimal(str(elasticache))
                self.api_gateway_cost = Decimal(str(api_gateway))
                self.cloudwatch_cost = Decimal(str(cloudwatch))
                self.total_cost = (self.ecs_cost + self.aurora_cost + self.s3_cost + 
                                 self.elasticache_cost + self.api_gateway_cost + self.cloudwatch_cost)
        
        return InfrastructureCosts(ecs_cost, aurora_cost, s3_cost, elasticache_cost, api_gateway_cost, cloudwatch_cost)

class CostController:
    """Cost controller for backward compatibility"""
    
    def __init__(self, credential_manager=None, guardrail_manager=None):
        self.credential_manager = credential_manager
        self.guardrail_manager = guardrail_manager
        # Don't create CostManagementService to avoid circular dependency
        self.cost_estimator = AWSCostManager()
        self.usage_tracker = {'daily_cost': 0.0, 'monthly_cost': 0.0}
        self._usage_metrics = UsageMetrics()
    
    @property
    def usage_metrics(self):
        """Get usage metrics"""
        return self._usage_metrics
    
    async def get_cost_estimate(self, **kwargs):
        """Get cost estimate"""
        return await self.cost_estimator.estimate_validation_cost(
            business_concept=kwargs.get('business_concept', 'Sample'),
            analysis_scope=kwargs.get('analysis_scope', ['market']),
            target_market=kwargs.get('target_market', 'Enterprise')
        )
    
    async def update_usage_metrics(self, cost):
        """Update usage metrics"""
        if hasattr(cost, '__float__'):
            cost = float(cost)
        
        # Convert to Decimal for usage metrics
        cost_decimal = Decimal(str(cost))
        
        # Update both tracking systems
        self.usage_tracker['daily_cost'] += cost
        self.usage_tracker['monthly_cost'] += cost
        
        self._usage_metrics.current_daily_cost += cost_decimal
        self._usage_metrics.current_monthly_cost += cost_decimal
        self._usage_metrics.validations_today += 1
        self._usage_metrics.validations_this_month += 1
        
        # Also update the guardrail manager if available
        if self.guardrail_manager:
            await self.guardrail_manager.record_usage(cost)
            # Increment validation count manually since record_usage doesn't do it
            self.guardrail_manager.current_usage['validations_today'] += 1
            self.guardrail_manager.current_usage['validations_this_month'] += 1
    
    async def check_cost_limits(self, cost):
        """Check if cost is within limits"""
        from decimal import Decimal
        
        # Convert cost to Decimal if needed
        if not isinstance(cost, Decimal):
            cost = Decimal(str(cost))
        
        result = {
            "allowed": True,
            "warnings": []
        }
        
        # Default per-validation limit of $50
        per_validation_limit = Decimal('50.00')
        
        if cost > per_validation_limit:
            result["allowed"] = False
            result["warnings"].append(f"Cost ${cost} exceeds per-validation limit of ${per_validation_limit}")
        
        # Check guardrail manager limits if available
        if self.guardrail_manager:
            try:
                guardrail_check = await self.guardrail_manager.check_limits(float(cost))
                if not guardrail_check.allowed:
                    result["allowed"] = False
                    result["warnings"].extend(guardrail_check.warnings)
            except Exception as e:
                # If guardrail check fails, add warning but don't block
                result["warnings"].append(f"Guardrail check failed: {e}")
        
        return result

# Global cost manager instance (for backward compatibility)
cost_manager = AWSCostManager()
