"""
Smart Model Selection Service for RiskIntel360
Optimizes model selection based on cost, performance, and complexity requirements.
"""

import logging
from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent types for model selection"""
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    FRAUD_DETECTION = "fraud_detection"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_ANALYSIS = "market_analysis"
    KYC_VERIFICATION = "kyc_verification"
    CUSTOMER_BEHAVIOR_INTELLIGENCE = "customer_behavior_intelligence"


class ModelTier(Enum):
    """Model performance tiers"""
    BASIC = "basic"      # Haiku models - fast, cost-effective
    STANDARD = "standard"  # Sonnet models - balanced performance
    PREMIUM = "premium"   # Opus models - maximum capability


class TaskComplexity(Enum):
    """Task complexity levels"""
    LOW = "low"          # Simple tasks, basic analysis
    MEDIUM = "medium"    # Moderate complexity, standard analysis
    HIGH = "high"        # Complex tasks, advanced reasoning
    CRITICAL = "critical"  # Mission-critical, maximum accuracy needed


@dataclass
class ModelSelection:
    """Model selection result"""
    model_name: str
    model_tier: ModelTier
    agent_type: AgentType
    estimated_cost: float
    estimated_performance: float
    reasoning: str


class ModelSelectionService:
    """Service for intelligent model selection"""
    
    # Model mappings by tier
    MODEL_MAPPINGS = {
        ModelTier.BASIC: "anthropic.claude-3-haiku-20240307-v1:0",
        ModelTier.STANDARD: "anthropic.claude-3-sonnet-20240229-v1:0", 
        ModelTier.PREMIUM: "anthropic.claude-3-opus-20240229-v1:0"
    }
    
    # Agent-specific model preferences
    AGENT_PREFERENCES = {
        AgentType.REGULATORY_COMPLIANCE: {
            "preferred_tier": ModelTier.BASIC,
            "min_tier": ModelTier.BASIC,
            "reasoning": "Regulatory compliance requires speed and accuracy for real-time monitoring"
        },
        AgentType.FRAUD_DETECTION: {
            "preferred_tier": ModelTier.STANDARD,
            "min_tier": ModelTier.STANDARD,
            "reasoning": "Fraud detection needs balanced performance for pattern recognition"
        },
        AgentType.RISK_ASSESSMENT: {
            "preferred_tier": ModelTier.PREMIUM,
            "min_tier": ModelTier.STANDARD,
            "reasoning": "Risk assessment requires sophisticated reasoning for complex scenarios"
        },
        AgentType.MARKET_ANALYSIS: {
            "preferred_tier": ModelTier.STANDARD,
            "min_tier": ModelTier.BASIC,
            "reasoning": "Market analysis benefits from balanced performance and cost"
        },
        AgentType.KYC_VERIFICATION: {
            "preferred_tier": ModelTier.BASIC,
            "min_tier": ModelTier.BASIC,
            "reasoning": "KYC verification prioritizes speed and cost-effectiveness"
        },
        AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: {
            "preferred_tier": ModelTier.STANDARD,
            "min_tier": ModelTier.BASIC,
            "reasoning": "Customer behavior analysis needs good pattern recognition"
        }
    }
    
    # Cost estimates per 1K tokens (input/output)
    COST_ESTIMATES = {
        ModelTier.BASIC: {"input": 0.00025, "output": 0.00125},
        ModelTier.STANDARD: {"input": 0.003, "output": 0.015},
        ModelTier.PREMIUM: {"input": 0.015, "output": 0.075}
    }
    
    def __init__(self):
        self.selection_cache: Dict[str, ModelSelection] = {}
    
    def select_model(
        self,
        agent_type: AgentType,
        complexity_score: float = 1.0,
        budget_constraint: Optional[float] = None,
        performance_requirement: Optional[float] = None
    ) -> ModelSelection:
        """
        Select optimal model for agent based on requirements
        
        Args:
            agent_type: Type of agent requesting model
            complexity_score: Task complexity (0.0-3.0)
            budget_constraint: Maximum cost per request
            performance_requirement: Minimum performance score (0.0-1.0)
        """
        
        # Get agent preferences
        preferences = self.AGENT_PREFERENCES.get(agent_type)
        if not preferences:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Start with preferred tier
        selected_tier = preferences["preferred_tier"]
        
        # Adjust based on complexity
        if complexity_score > 2.0 and selected_tier != ModelTier.PREMIUM:
            selected_tier = ModelTier.PREMIUM
        elif complexity_score > 1.5 and selected_tier == ModelTier.BASIC:
            selected_tier = ModelTier.STANDARD
        
        # Check budget constraints
        if budget_constraint:
            estimated_cost = self._estimate_cost(selected_tier, complexity_score)
            if estimated_cost > budget_constraint:
                # Try lower tiers
                for tier in [ModelTier.STANDARD, ModelTier.BASIC]:
                    if self._estimate_cost(tier, complexity_score) <= budget_constraint:
                        selected_tier = tier
                        break
        
        # Check performance requirements
        if performance_requirement:
            performance_score = self._estimate_performance(selected_tier, agent_type)
            if performance_score < performance_requirement:
                # Try higher tiers
                for tier in [ModelTier.STANDARD, ModelTier.PREMIUM]:
                    if self._estimate_performance(tier, agent_type) >= performance_requirement:
                        selected_tier = tier
                        break
        
        # Ensure minimum tier requirement
        min_tier = preferences["min_tier"]
        if self._tier_rank(selected_tier) < self._tier_rank(min_tier):
            selected_tier = min_tier
        
        # Create selection result
        model_name = self.MODEL_MAPPINGS[selected_tier]
        estimated_cost = self._estimate_cost(selected_tier, complexity_score)
        estimated_performance = self._estimate_performance(selected_tier, agent_type)
        
        reasoning = self._generate_reasoning(
            agent_type, selected_tier, complexity_score, 
            budget_constraint, performance_requirement
        )
        
        return ModelSelection(
            model_name=model_name,
            model_tier=selected_tier,
            agent_type=agent_type,
            estimated_cost=estimated_cost,
            estimated_performance=estimated_performance,
            reasoning=reasoning
        )
    
    def _tier_rank(self, tier: ModelTier) -> int:
        """Get numeric rank for tier comparison"""
        ranks = {
            ModelTier.BASIC: 1,
            ModelTier.STANDARD: 2,
            ModelTier.PREMIUM: 3
        }
        return ranks[tier]
    
    def _estimate_cost(self, tier: ModelTier, complexity_score: float) -> float:
        """Estimate cost for model tier and complexity"""
        base_tokens = 1000 * complexity_score  # Scale tokens with complexity
        costs = self.COST_ESTIMATES[tier]
        
        # Assume 70% input, 30% output tokens
        input_tokens = base_tokens * 0.7
        output_tokens = base_tokens * 0.3
        
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def _estimate_performance(self, tier: ModelTier, agent_type: AgentType) -> float:
        """Estimate performance score for model tier and agent type"""
        base_performance = {
            ModelTier.BASIC: 0.75,
            ModelTier.STANDARD: 0.85,
            ModelTier.PREMIUM: 0.95
        }
        
        # Agent-specific performance modifiers
        agent_modifiers = {
            AgentType.REGULATORY_COMPLIANCE: {
                ModelTier.BASIC: 0.05,    # Haiku is good for regulatory
                ModelTier.STANDARD: 0.0,
                ModelTier.PREMIUM: -0.05  # Overkill for regulatory
            },
            AgentType.FRAUD_DETECTION: {
                ModelTier.BASIC: -0.1,    # Basic may miss patterns
                ModelTier.STANDARD: 0.05, # Sweet spot
                ModelTier.PREMIUM: 0.0
            },
            AgentType.RISK_ASSESSMENT: {
                ModelTier.BASIC: -0.15,   # Complex reasoning needed
                ModelTier.STANDARD: 0.0,
                ModelTier.PREMIUM: 0.1    # Excels at complex reasoning
            }
        }
        
        performance = base_performance[tier]
        modifier = agent_modifiers.get(agent_type, {}).get(tier, 0.0)
        
        return min(1.0, max(0.0, performance + modifier))
    
    def _generate_reasoning(
        self,
        agent_type: AgentType,
        selected_tier: ModelTier,
        complexity_score: float,
        budget_constraint: Optional[float],
        performance_requirement: Optional[float]
    ) -> str:
        """Generate human-readable reasoning for model selection"""
        
        reasons = []
        
        # Base agent preference
        preferences = self.AGENT_PREFERENCES[agent_type]
        reasons.append(preferences["reasoning"])
        
        # Complexity adjustment
        if complexity_score > 2.0:
            reasons.append("High complexity task requires advanced reasoning capabilities")
        elif complexity_score < 1.0:
            reasons.append("Low complexity allows for cost-optimized model selection")
        
        # Budget consideration
        if budget_constraint:
            estimated_cost = self._estimate_cost(selected_tier, complexity_score)
            if estimated_cost <= budget_constraint * 0.8:
                reasons.append(f"Selected model is well within budget (${estimated_cost:.4f} vs ${budget_constraint:.4f})")
            else:
                reasons.append(f"Selected model optimized for budget constraint (${estimated_cost:.4f})")
        
        # Performance consideration
        if performance_requirement:
            estimated_performance = self._estimate_performance(selected_tier, agent_type)
            if estimated_performance >= performance_requirement:
                reasons.append(f"Model meets performance requirement ({estimated_performance:.2f} vs {performance_requirement:.2f})")
        
        # Final tier selection
        tier_names = {
            ModelTier.BASIC: "Claude-3 Haiku (fast, cost-effective)",
            ModelTier.STANDARD: "Claude-3 Sonnet (balanced performance)",
            ModelTier.PREMIUM: "Claude-3 Opus (maximum capability)"
        }
        reasons.append(f"Selected {tier_names[selected_tier]} for optimal balance")
        
        return ". ".join(reasons)
    
    def get_model_for_agent(self, agent_type: AgentType) -> str:
        """Get default model name for agent type"""
        selection = self.select_model(agent_type)
        return selection.model_name
    
    def clear_cache(self):
        """Clear selection cache"""
        self.selection_cache.clear()
    
    async def get_optimal_models(self, cost_profile=None, **kwargs) -> Dict[str, str]:
        """Get optimal models for all agent types based on cost profile"""
        from .cost_management import CostProfile
        
        # Default profile mappings
        profile_mappings = {
            CostProfile.DEMO: {
                AgentType.REGULATORY_COMPLIANCE: ModelTier.BASIC,
                AgentType.FRAUD_DETECTION: ModelTier.BASIC,
                AgentType.RISK_ASSESSMENT: ModelTier.STANDARD,
                AgentType.MARKET_ANALYSIS: ModelTier.BASIC,
                AgentType.KYC_VERIFICATION: ModelTier.BASIC,
                AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: ModelTier.BASIC
            },
            CostProfile.DEVELOPMENT: {
                AgentType.REGULATORY_COMPLIANCE: ModelTier.BASIC,
                AgentType.FRAUD_DETECTION: ModelTier.STANDARD,
                AgentType.RISK_ASSESSMENT: ModelTier.STANDARD,
                AgentType.MARKET_ANALYSIS: ModelTier.STANDARD,
                AgentType.KYC_VERIFICATION: ModelTier.BASIC,
                AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: ModelTier.STANDARD
            },
            CostProfile.PRODUCTION: {
                AgentType.REGULATORY_COMPLIANCE: ModelTier.STANDARD,
                AgentType.FRAUD_DETECTION: ModelTier.PREMIUM,
                AgentType.RISK_ASSESSMENT: ModelTier.PREMIUM,
                AgentType.MARKET_ANALYSIS: ModelTier.STANDARD,
                AgentType.KYC_VERIFICATION: ModelTier.BASIC,
                AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: ModelTier.STANDARD
            }
        }
        
        # Use development as default
        profile = cost_profile or CostProfile.DEVELOPMENT
        tier_mapping = profile_mappings.get(profile, profile_mappings[CostProfile.DEVELOPMENT])
        
        # Convert to model names with test-compatible keys
        result = {}
        key_mapping = {
            AgentType.REGULATORY_COMPLIANCE: "regulatory_compliance",
            AgentType.FRAUD_DETECTION: "fraud_detection", 
            AgentType.RISK_ASSESSMENT: "risk_assessment",
            AgentType.MARKET_ANALYSIS: "market_analysis",  # Test expects this key
            AgentType.KYC_VERIFICATION: "kyc_verification",
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: "customer_behavior_intelligence"  # Test expects this key
        }
        
        for agent_type, tier in tier_mapping.items():
            model_name = self.MODEL_MAPPINGS[tier]
            key = key_mapping.get(agent_type, agent_type.value)
            result[key] = model_name
        
        return result


# Global service instance
model_selection_service = ModelSelectionService()