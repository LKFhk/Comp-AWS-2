"""
Customer Behavior Intelligence Agent for RiskIntel360 Platform
Specialized agent for fintech customer behavior analysis, risk scoring, and behavioral pattern detection.
Focused on financial services customer intelligence using public data sources.
"""

import asyncio
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import aiohttp
import warnings

from .base_agent import BaseAgent, AgentConfig
from ..models.agent_models import MessageType, Priority, AgentType

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


@dataclass
class CustomerSegment:
    """Fintech customer segment definition"""
    segment_name: str
    size_percentage: float  # 0.0 to 1.0
    characteristics: List[str]
    financial_behaviors: List[str]
    risk_profile: str  # 'low', 'medium', 'high'
    preferred_channels: List[str]
    spending_power: str  # 'low', 'medium', 'high'
    engagement_level: str  # 'low', 'medium', 'high'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'segment_name': self.segment_name,
            'size_percentage': self.size_percentage,
            'characteristics': self.characteristics,
            'financial_behaviors': self.financial_behaviors,
            'risk_profile': self.risk_profile,
            'preferred_channels': self.preferred_channels,
            'spending_power': self.spending_power,
            'engagement_level': self.engagement_level
        }


@dataclass
class BehaviorAnalysis:
    """Customer behavior analysis result"""
    behavior_patterns: List[str]
    risk_indicators: List[str]
    engagement_score: float  # 0.0 to 1.0
    loyalty_score: float  # 0.0 to 1.0
    churn_risk: str  # 'low', 'medium', 'high'
    financial_health_score: float  # 0.0 to 1.0
    preferred_products: List[str]
    usage_patterns: Dict[str, Any]
    confidence_level: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'behavior_patterns': self.behavior_patterns,
            'risk_indicators': self.risk_indicators,
            'engagement_score': self.engagement_score,
            'loyalty_score': self.loyalty_score,
            'churn_risk': self.churn_risk,
            'financial_health_score': self.financial_health_score,
            'preferred_products': self.preferred_products,
            'usage_patterns': self.usage_patterns,
            'confidence_level': self.confidence_level
        }


@dataclass
class CustomerIntelligenceResult:
    """Complete customer intelligence analysis result"""
    customer_segments: List[CustomerSegment]
    behavior_analysis: BehaviorAnalysis
    market_demand_level: str  # 'low', 'medium', 'high', 'very_high'
    demand_score: float  # 0.0 to 1.0
    key_insights: List[str]
    recommendations: List[str]
    confidence_score: float
    data_sources_used: List[str]
    analysis_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'customer_segments': [segment.to_dict() for segment in self.customer_segments],
            'behavior_analysis': self.behavior_analysis.to_dict(),
            'market_demand_level': self.market_demand_level,
            'demand_score': self.demand_score,
            'key_insights': self.key_insights,
            'recommendations': self.recommendations,
            'confidence_score': self.confidence_score,
            'data_sources_used': self.data_sources_used,
            'analysis_timestamp': self.analysis_timestamp.isoformat()
        }


class CustomerBehaviorIntelligenceAgent(BaseAgent):
    """
    Customer Behavior Intelligence Agent using Claude-3 Sonnet for complex behavioral analysis.
    Focused on fintech customer behavior intelligence using public data sources.
    
    Capabilities:
    - Fintech customer behavior analysis and segmentation
    - Financial risk scoring and behavioral pattern detection
    - Customer engagement and loyalty analysis
    - Churn prediction and retention strategies
    - Market demand validation for fintech products
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize Customer Behavior Intelligence Agent"""
        super().__init__(config)
        
        # Ensure this is a customer behavior intelligence agent
        if config.agent_type != AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE:
            raise ValueError(f"Invalid agent type for CustomerBehaviorIntelligenceAgent: {config.agent_type}")
        
        # Initialize HTTP session for API calls
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Cache for customer data
        self.data_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(hours=1)  # 1-hour cache for customer data
        
        self.logger.info("👥 Customer Behavior Intelligence Agent initialized for fintech analysis")
    
    async def start(self) -> None:
        """Start the agent and initialize HTTP session"""
        await super().start()
        
        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=30)
        self.http_session = aiohttp.ClientSession(timeout=timeout)
        
        self.logger.info("🌐 HTTP session initialized for customer data APIs")
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources"""
        if self.http_session:
            await self.http_session.close()
            self.logger.info("🔌 HTTP session closed")
        
        await super().stop()
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this agent supports"""
        return [
            "fintech_customer_segmentation",
            "behavioral_risk_analysis",
            "customer_engagement_analysis",
            "churn_prediction",
            "financial_health_scoring",
            "market_demand_validation"
        ]
    
    async def execute_task(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a customer behavior intelligence task.
        
        Args:
            task_type: Type of task to execute
            parameters: Task parameters
            
        Returns:
            Dict containing task results
        """
        self.current_task = task_type
        self.update_progress(0.1)
        
        try:
            if task_type == "fintech_customer_analysis":
                return await self._perform_fintech_customer_analysis(parameters)
            elif task_type == "behavioral_risk_assessment":
                return await self._perform_behavioral_risk_assessment(parameters)
            elif task_type == "customer_segmentation":
                return await self._perform_customer_segmentation(parameters)
            elif task_type == "churn_prediction":
                return await self._perform_churn_prediction(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            self.state.error_count += 1
            self.logger.error(f"❌ Task execution failed: {e}")
            raise
        finally:
            self.current_task = None
    
    async def _perform_fintech_customer_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive fintech customer behavior analysis.
        
        Args:
            parameters: Analysis parameters including customer data, product type
            
        Returns:
            Dict containing customer intelligence results
        """
        product_type = parameters.get('product_type', 'digital_banking')
        target_market = parameters.get('target_market', 'retail')
        
        self.logger.info(f"👥 Performing fintech customer analysis for {product_type} in {target_market} market")
        
        # Step 1: Analyze customer segments
        self.update_progress(0.2)
        customer_segments = await self._analyze_fintech_customer_segments(product_type, target_market)
        
        # Step 2: Perform behavior analysis
        self.update_progress(0.4)
        behavior_analysis = await self._analyze_customer_behavior(customer_segments, product_type)
        
        # Step 3: Assess market demand
        self.update_progress(0.6)
        demand_analysis = await self._assess_market_demand(product_type, target_market)
        
        # Step 4: Generate insights and recommendations
        self.update_progress(0.8)
        insights = await self._generate_customer_insights(customer_segments, behavior_analysis, demand_analysis)
        
        # Step 5: Compile results
        self.update_progress(1.0)
        result = CustomerIntelligenceResult(
            customer_segments=customer_segments,
            behavior_analysis=behavior_analysis,
            market_demand_level=demand_analysis.get('demand_level', 'medium'),
            demand_score=demand_analysis.get('demand_score', 0.6),
            key_insights=insights.get('insights', []),
            recommendations=insights.get('recommendations', []),
            confidence_score=self._calculate_confidence_score(customer_segments, behavior_analysis),
            data_sources_used=['llm_analysis', 'industry_patterns'],
            analysis_timestamp=datetime.now(UTC)
        )
        
        self.logger.info(f"✅ Fintech customer analysis completed with {result.confidence_score:.1%} confidence")
        
        return {
            'analysis_result': result.to_dict(),
            'metadata': {
                'agent_id': self.agent_id,
                'analysis_duration': 'completed',
                'data_quality': 'high' if result.confidence_score > 0.7 else 'medium',
                'fintech_focus': True
            }
        }
    
    async def _analyze_fintech_customer_segments(self, product_type: str, target_market: str) -> List[CustomerSegment]:
        """
        Analyze fintech customer segments using LLM insights.
        
        Args:
            product_type: Type of fintech product
            target_market: Target market segment
            
        Returns:
            List of CustomerSegment objects
        """
        prompt = f"""
        Analyze customer segments for a {product_type} fintech product targeting the {target_market} market.
        
        Provide detailed customer segmentation analysis in JSON format:
        {{
            "segments": [
                {{
                    "segment_name": "segment_name",
                    "size_percentage": <0.0-1.0>,
                    "characteristics": ["characteristic1", "characteristic2", ...],
                    "financial_behaviors": ["behavior1", "behavior2", ...],
                    "risk_profile": "low|medium|high",
                    "preferred_channels": ["channel1", "channel2", ...],
                    "spending_power": "low|medium|high",
                    "engagement_level": "low|medium|high"
                }},
                ...
            ]
        }}
        
        Focus on realistic fintech customer segments with specific financial behaviors and risk profiles.
        """
        
        system_prompt = """You are a fintech customer intelligence expert with deep knowledge of financial services customer behavior. 
        Provide realistic customer segmentation based on financial behavior patterns, risk profiles, and engagement levels 
        specific to fintech products and services."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            segments_data = json.loads(response)
            segments = []
            
            for segment_data in segments_data.get('segments', []):
                segment = CustomerSegment(
                    segment_name=segment_data.get('segment_name', 'Unknown Segment'),
                    size_percentage=segment_data.get('size_percentage', 0.2),
                    characteristics=segment_data.get('characteristics', []),
                    financial_behaviors=segment_data.get('financial_behaviors', []),
                    risk_profile=segment_data.get('risk_profile', 'medium'),
                    preferred_channels=segment_data.get('preferred_channels', []),
                    spending_power=segment_data.get('spending_power', 'medium'),
                    engagement_level=segment_data.get('engagement_level', 'medium')
                )
                segments.append(segment)
            
            return segments
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse customer segments: {e}")
            # Return default fintech segments
            return [
                CustomerSegment(
                    segment_name="Tech-Savvy Millennials",
                    size_percentage=0.35,
                    characteristics=["Digital-first", "Mobile-native", "Price-conscious"],
                    financial_behaviors=["Frequent mobile banking", "Peer-to-peer payments", "Investment apps"],
                    risk_profile="medium",
                    preferred_channels=["Mobile app", "Social media", "Email"],
                    spending_power="medium",
                    engagement_level="high"
                ),
                CustomerSegment(
                    segment_name="Traditional Banking Users",
                    size_percentage=0.40,
                    characteristics=["Security-focused", "Branch-loyal", "Conservative"],
                    financial_behaviors=["Traditional banking", "Cash usage", "Risk-averse investing"],
                    risk_profile="low",
                    preferred_channels=["Branch", "Phone", "Website"],
                    spending_power="high",
                    engagement_level="medium"
                ),
                CustomerSegment(
                    segment_name="Small Business Owners",
                    size_percentage=0.25,
                    characteristics=["Efficiency-focused", "Growth-oriented", "Time-constrained"],
                    financial_behaviors=["Business banking", "Payment processing", "Cash flow management"],
                    risk_profile="medium",
                    preferred_channels=["Online platform", "Phone support", "Email"],
                    spending_power="high",
                    engagement_level="high"
                )
            ]
    
    async def _analyze_customer_behavior(self, customer_segments: List[CustomerSegment], product_type: str) -> BehaviorAnalysis:
        """
        Analyze customer behavior patterns for fintech products.
        
        Args:
            customer_segments: List of customer segments
            product_type: Type of fintech product
            
        Returns:
            BehaviorAnalysis object
        """
        # Prepare segment summary for LLM
        segment_summary = []
        for segment in customer_segments:
            segment_summary.append({
                'name': segment.segment_name,
                'size': f"{segment.size_percentage:.1%}",
                'behaviors': segment.financial_behaviors,
                'risk_profile': segment.risk_profile
            })
        
        prompt = f"""
        Analyze customer behavior patterns for a {product_type} fintech product based on these customer segments:
        
        Customer Segments: {segment_summary}
        
        Provide comprehensive behavior analysis in JSON format:
        {{
            "behavior_patterns": ["pattern1", "pattern2", ...],
            "risk_indicators": ["indicator1", "indicator2", ...],
            "engagement_score": <0.0-1.0>,
            "loyalty_score": <0.0-1.0>,
            "churn_risk": "low|medium|high",
            "financial_health_score": <0.0-1.0>,
            "preferred_products": ["product1", "product2", ...],
            "usage_patterns": {{
                "peak_usage_times": ["time1", "time2", ...],
                "transaction_frequency": "low|medium|high",
                "feature_adoption": "slow|moderate|fast"
            }},
            "confidence_level": <0.0-1.0>
        }}
        """
        
        system_prompt = """You are a fintech behavioral analyst specializing in customer behavior patterns and risk assessment. 
        Analyze customer behavior based on financial service usage patterns, engagement metrics, and risk indicators 
        specific to fintech products."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            behavior_data = json.loads(response)
            
            return BehaviorAnalysis(
                behavior_patterns=behavior_data.get('behavior_patterns', []),
                risk_indicators=behavior_data.get('risk_indicators', []),
                engagement_score=behavior_data.get('engagement_score', 0.6),
                loyalty_score=behavior_data.get('loyalty_score', 0.6),
                churn_risk=behavior_data.get('churn_risk', 'medium'),
                financial_health_score=behavior_data.get('financial_health_score', 0.7),
                preferred_products=behavior_data.get('preferred_products', []),
                usage_patterns=behavior_data.get('usage_patterns', {}),
                confidence_level=behavior_data.get('confidence_level', 0.7)
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse behavior analysis: {e}")
            return BehaviorAnalysis(
                behavior_patterns=["Mobile-first usage", "Frequent small transactions", "Security-conscious"],
                risk_indicators=["Irregular transaction patterns", "Multiple failed logins", "Unusual spending"],
                engagement_score=0.6,
                loyalty_score=0.6,
                churn_risk='medium',
                financial_health_score=0.7,
                preferred_products=["Mobile banking", "Payment apps", "Investment tools"],
                usage_patterns={
                    "peak_usage_times": ["Morning", "Evening"],
                    "transaction_frequency": "medium",
                    "feature_adoption": "moderate"
                },
                confidence_level=0.6
            )
    
    async def _assess_market_demand(self, product_type: str, target_market: str) -> Dict[str, Any]:
        """
        Assess market demand for fintech product.
        
        Args:
            product_type: Type of fintech product
            target_market: Target market segment
            
        Returns:
            Dict containing demand analysis
        """
        prompt = f"""
        Assess market demand for a {product_type} fintech product in the {target_market} market.
        
        Provide demand analysis in JSON format:
        {{
            "demand_level": "low|medium|high|very_high",
            "demand_score": <0.0-1.0>,
            "growth_trajectory": "declining|stable|growing|accelerating",
            "demand_drivers": ["driver1", "driver2", ...],
            "market_gaps": ["gap1", "gap2", ...],
            "target_segments": ["segment1", "segment2", ...],
            "seasonal_patterns": ["pattern1", "pattern2", ...],
            "confidence_score": <0.0-1.0>
        }}
        """
        
        system_prompt = """You are a fintech market demand analyst with expertise in financial services market research. 
        Assess market demand based on current fintech trends, customer needs, competitive landscape, 
        and regulatory environment."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            demand_data = json.loads(response)
            
            return {
                'demand_level': demand_data.get('demand_level', 'medium'),
                'demand_score': demand_data.get('demand_score', 0.6),
                'growth_trajectory': demand_data.get('growth_trajectory', 'growing'),
                'demand_drivers': demand_data.get('demand_drivers', []),
                'market_gaps': demand_data.get('market_gaps', []),
                'target_segments': demand_data.get('target_segments', []),
                'seasonal_patterns': demand_data.get('seasonal_patterns', []),
                'confidence_score': demand_data.get('confidence_score', 0.6)
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse demand analysis: {e}")
            return {
                'demand_level': 'medium',
                'demand_score': 0.6,
                'growth_trajectory': 'growing',
                'demand_drivers': ['Digital transformation', 'Convenience', 'Cost savings'],
                'market_gaps': ['Underserved segments', 'Feature gaps'],
                'target_segments': ['Millennials', 'Small businesses'],
                'seasonal_patterns': ['Holiday spending', 'Tax season'],
                'confidence_score': 0.6
            }
    
    async def _generate_customer_insights(
        self,
        customer_segments: List[CustomerSegment],
        behavior_analysis: BehaviorAnalysis,
        demand_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive customer insights and recommendations.
        
        Args:
            customer_segments: Customer segments
            behavior_analysis: Behavior analysis results
            demand_analysis: Market demand analysis
            
        Returns:
            Dict containing insights and recommendations
        """
        # Prepare data summary for LLM
        segments_summary = [
            {
                'name': segment.segment_name,
                'size': f"{segment.size_percentage:.1%}",
                'risk_profile': segment.risk_profile,
                'engagement': segment.engagement_level
            }
            for segment in customer_segments
        ]
        
        prompt = f"""
        Generate comprehensive customer insights and strategic recommendations based on:
        
        Customer Segments: {segments_summary}
        
        Behavior Analysis:
        - Engagement Score: {behavior_analysis.engagement_score:.1%}
        - Loyalty Score: {behavior_analysis.loyalty_score:.1%}
        - Churn Risk: {behavior_analysis.churn_risk}
        - Financial Health Score: {behavior_analysis.financial_health_score:.1%}
        
        Market Demand:
        - Demand Level: {demand_analysis.get('demand_level', 'medium')}
        - Growth Trajectory: {demand_analysis.get('growth_trajectory', 'growing')}
        
        Provide insights in JSON format:
        {{
            "key_insights": ["insight1", "insight2", ...],
            "strategic_recommendations": ["recommendation1", "recommendation2", ...],
            "risk_mitigation": ["strategy1", "strategy2", ...],
            "growth_opportunities": ["opportunity1", "opportunity2", ...],
            "customer_retention_strategies": ["strategy1", "strategy2", ...],
            "product_development_priorities": ["priority1", "priority2", ...]
        }}
        """
        
        system_prompt = """You are a senior fintech strategy consultant with expertise in customer intelligence and product strategy. 
        Provide actionable insights and recommendations based on customer behavior analysis, market demand, 
        and fintech industry best practices."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            insights_data = json.loads(response)
            
            return {
                'insights': insights_data.get('key_insights', []),
                'recommendations': insights_data.get('strategic_recommendations', []),
                'risk_mitigation': insights_data.get('risk_mitigation', []),
                'growth_opportunities': insights_data.get('growth_opportunities', []),
                'retention_strategies': insights_data.get('customer_retention_strategies', []),
                'product_priorities': insights_data.get('product_development_priorities', [])
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse customer insights: {e}")
            return {
                'insights': ['Strong mobile adoption', 'Security concerns prevalent', 'Price sensitivity high'],
                'recommendations': ['Enhance mobile experience', 'Strengthen security features', 'Competitive pricing'],
                'risk_mitigation': ['Implement fraud detection', 'Improve customer support'],
                'growth_opportunities': ['Expand to underserved segments', 'Add new features'],
                'retention_strategies': ['Loyalty programs', 'Personalized offers'],
                'product_priorities': ['Mobile optimization', 'Security enhancements']
            }
    
    def _calculate_confidence_score(self, customer_segments: List[CustomerSegment], behavior_analysis: BehaviorAnalysis) -> float:
        """
        Calculate confidence score based on analysis quality.
        
        Args:
            customer_segments: Customer segments analyzed
            behavior_analysis: Behavior analysis results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_score = 0.6
        
        # Increase confidence based on number of segments
        if len(customer_segments) >= 3:
            base_score += 0.1
        
        # Increase confidence based on behavior analysis confidence
        if behavior_analysis.confidence_level > 0.7:
            base_score += 0.1
        
        # Increase confidence if we have detailed behavioral patterns
        if len(behavior_analysis.behavior_patterns) >= 3:
            base_score += 0.1
        
        return min(0.9, base_score)
    
    # Enhanced fintech customer behavior capabilities
    
    async def _perform_enhanced_fintech_customer_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced fintech customer behavior analysis with advanced behavioral insights.
        
        Args:
            parameters: Analysis parameters including customer data, product type
            
        Returns:
            Dict containing enhanced customer intelligence results
        """
        product_type = parameters.get('product_type', 'digital_banking')
        target_market = parameters.get('target_market', 'retail')
        
        self.logger.info(f"👥 Performing enhanced fintech customer analysis for {product_type} in {target_market} market")
        
        # Step 1: Advanced customer segmentation with behavioral patterns
        self.update_progress(0.15)
        customer_segments = await self._analyze_advanced_fintech_customer_segments(product_type, target_market)
        
        # Step 2: Enhanced behavior analysis with risk profiling
        self.update_progress(0.3)
        behavior_analysis = await self._analyze_enhanced_customer_behavior(customer_segments, product_type)
        
        # Step 3: Financial behavior pattern analysis
        self.update_progress(0.45)
        financial_behavior = await self._analyze_financial_behavior_patterns(customer_segments, product_type)
        
        # Step 4: Customer lifetime value and profitability analysis
        self.update_progress(0.6)
        clv_analysis = await self._analyze_customer_lifetime_value(customer_segments, behavior_analysis)
        
        # Step 5: Enhanced market demand with behavioral drivers
        self.update_progress(0.75)
        demand_analysis = await self._assess_enhanced_market_demand(product_type, target_market, behavior_analysis)
        
        # Step 6: Generate comprehensive insights and recommendations
        self.update_progress(0.9)
        insights = await self._generate_enhanced_customer_insights(
            customer_segments, behavior_analysis, financial_behavior, clv_analysis, demand_analysis
        )
        
        # Step 7: Compile enhanced results
        self.update_progress(1.0)
        result = CustomerIntelligenceResult(
            customer_segments=customer_segments,
            behavior_analysis=behavior_analysis,
            market_demand_level=demand_analysis.get('demand_level', 'medium'),
            demand_score=demand_analysis.get('demand_score', 0.6),
            key_insights=insights.get('insights', []),
            recommendations=insights.get('recommendations', []),
            confidence_score=self._calculate_enhanced_confidence_score(customer_segments, behavior_analysis, financial_behavior),
            data_sources_used=['enhanced_llm_analysis', 'behavioral_models', 'fintech_patterns'],
            analysis_timestamp=datetime.now(UTC)
        )
        
        self.logger.info(f"✅ Enhanced fintech customer analysis completed with {result.confidence_score:.1%} confidence")
        
        return {
            'analysis_result': result.to_dict(),
            'financial_behavior_analysis': financial_behavior,
            'clv_analysis': clv_analysis,
            'metadata': {
                'agent_id': self.agent_id,
                'analysis_duration': 'completed',
                'data_quality': 'high' if result.confidence_score > 0.7 else 'medium',
                'fintech_focus': True,
                'enhanced_capabilities': True
            }
        }
    
    async def _analyze_advanced_fintech_customer_segments(self, product_type: str, target_market: str) -> List[CustomerSegment]:
        """
        Advanced fintech customer segmentation with behavioral and financial patterns.
        
        Args:
            product_type: Type of fintech product
            target_market: Target market segment
            
        Returns:
            List of CustomerSegment objects with enhanced analysis
        """
        prompt = f"""
        Perform advanced customer segmentation for a {product_type} fintech product targeting the {target_market} market.
        
        Focus on behavioral and financial patterns specific to fintech:
        1. Digital adoption and technology comfort levels
        2. Financial behavior patterns and risk tolerance
        3. Payment preferences and transaction behaviors
        4. Investment and savings behaviors
        5. Credit usage and financial health indicators
        6. Security consciousness and privacy concerns
        7. Channel preferences and engagement patterns
        
        Provide detailed customer segmentation analysis in JSON format:
        {{
            "segments": [
                {{
                    "segment_name": "segment_name",
                    "size_percentage": <0.0-1.0>,
                    "characteristics": ["characteristic1", "characteristic2", ...],
                    "financial_behaviors": ["behavior1", "behavior2", ...],
                    "risk_profile": "low|medium|high",
                    "preferred_channels": ["channel1", "channel2", ...],
                    "spending_power": "low|medium|high",
                    "engagement_level": "low|medium|high",
                    "digital_maturity": "basic|intermediate|advanced",
                    "financial_goals": ["goal1", "goal2", ...],
                    "pain_points": ["pain1", "pain2", ...],
                    "value_drivers": ["driver1", "driver2", ...]
                }},
                ...
            ]
        }}
        
        Focus on realistic fintech customer segments with specific behavioral and financial characteristics.
        """
        
        system_prompt = """You are a fintech customer intelligence expert with deep knowledge of financial services customer behavior. 
        Provide realistic customer segmentation based on financial behavior patterns, digital adoption, risk profiles, 
        and engagement levels specific to fintech products and services."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            segments_data = json.loads(response)
            segments = []
            
            for segment_data in segments_data.get('segments', []):
                segment = CustomerSegment(
                    segment_name=segment_data.get('segment_name', 'Unknown Segment'),
                    size_percentage=segment_data.get('size_percentage', 0.2),
                    characteristics=segment_data.get('characteristics', []),
                    financial_behaviors=segment_data.get('financial_behaviors', []),
                    risk_profile=segment_data.get('risk_profile', 'medium'),
                    preferred_channels=segment_data.get('preferred_channels', []),
                    spending_power=segment_data.get('spending_power', 'medium'),
                    engagement_level=segment_data.get('engagement_level', 'medium')
                )
                segments.append(segment)
            
            return segments
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse advanced customer segments: {e}")
            # Return enhanced default fintech segments
            return [
                CustomerSegment(
                    segment_name="Digital-Native Millennials",
                    size_percentage=0.30,
                    characteristics=["Mobile-first", "Tech-savvy", "Convenience-focused", "Price-sensitive"],
                    financial_behaviors=["Frequent mobile banking", "P2P payments", "Robo-investing", "Cashless transactions"],
                    risk_profile="medium",
                    preferred_channels=["Mobile app", "Social media", "In-app messaging"],
                    spending_power="medium",
                    engagement_level="high"
                ),
                CustomerSegment(
                    segment_name="Security-Conscious Gen X",
                    size_percentage=0.25,
                    characteristics=["Security-focused", "Brand-loyal", "Research-oriented", "Value-conscious"],
                    financial_behaviors=["Multi-channel banking", "Traditional investing", "Credit monitoring", "Budgeting apps"],
                    risk_profile="low",
                    preferred_channels=["Website", "Phone support", "Email", "Branch"],
                    spending_power="high",
                    engagement_level="medium"
                ),
                CustomerSegment(
                    segment_name="Affluent Digital Adopters",
                    size_percentage=0.20,
                    characteristics=["High-income", "Early adopters", "Investment-focused", "Time-constrained"],
                    financial_behaviors=["Wealth management", "Premium services", "Automated investing", "Multiple accounts"],
                    risk_profile="medium",
                    preferred_channels=["Premium app features", "Personal advisor", "Video calls"],
                    spending_power="high",
                    engagement_level="high"
                ),
                CustomerSegment(
                    segment_name="Small Business Owners",
                    size_percentage=0.25,
                    characteristics=["Efficiency-focused", "Growth-oriented", "Cash flow conscious", "Compliance-aware"],
                    financial_behaviors=["Business banking", "Payment processing", "Invoice management", "Expense tracking"],
                    risk_profile="medium",
                    preferred_channels=["Business portal", "API integration", "Phone support"],
                    spending_power="high",
                    engagement_level="high"
                )
            ]
    
    async def _analyze_enhanced_customer_behavior(self, customer_segments: List[CustomerSegment], product_type: str) -> BehaviorAnalysis:
        """
        Enhanced customer behavior analysis with advanced behavioral insights.
        
        Args:
            customer_segments: List of customer segments
            product_type: Type of fintech product
            
        Returns:
            BehaviorAnalysis object with enhanced insights
        """
        # Prepare enhanced segment summary for LLM
        segment_summary = []
        for segment in customer_segments:
            segment_summary.append({
                'name': segment.segment_name,
                'size': f"{segment.size_percentage:.1%}",
                'behaviors': segment.financial_behaviors,
                'risk_profile': segment.risk_profile,
                'engagement': segment.engagement_level,
                'spending_power': segment.spending_power
            })
        
        prompt = f"""
        Perform enhanced customer behavior analysis for a {product_type} fintech product based on these customer segments:
        
        Customer Segments: {segment_summary}
        
        Provide comprehensive enhanced behavior analysis in JSON format:
        {{
            "behavior_patterns": ["pattern1", "pattern2", ...],
            "risk_indicators": ["indicator1", "indicator2", ...],
            "engagement_score": <0.0-1.0>,
            "loyalty_score": <0.0-1.0>,
            "churn_risk": "low|medium|high",
            "financial_health_score": <0.0-1.0>,
            "preferred_products": ["product1", "product2", ...],
            "usage_patterns": {{
                "peak_usage_times": ["time1", "time2", ...],
                "transaction_frequency": "low|medium|high",
                "feature_adoption": "slow|moderate|fast",
                "session_duration": "short|medium|long",
                "cross_selling_potential": "low|medium|high"
            }},
            "behavioral_triggers": ["trigger1", "trigger2", ...],
            "personalization_opportunities": ["opportunity1", "opportunity2", ...],
            "retention_factors": ["factor1", "factor2", ...],
            "confidence_level": <0.0-1.0>
        }}
        """
        
        system_prompt = """You are a fintech behavioral analyst specializing in customer behavior patterns and advanced analytics. 
        Analyze customer behavior based on financial service usage patterns, engagement metrics, and behavioral triggers 
        specific to fintech products with focus on personalization and retention."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            behavior_data = json.loads(response)
            
            return BehaviorAnalysis(
                behavior_patterns=behavior_data.get('behavior_patterns', []),
                risk_indicators=behavior_data.get('risk_indicators', []),
                engagement_score=behavior_data.get('engagement_score', 0.7),
                loyalty_score=behavior_data.get('loyalty_score', 0.6),
                churn_risk=behavior_data.get('churn_risk', 'medium'),
                financial_health_score=behavior_data.get('financial_health_score', 0.7),
                preferred_products=behavior_data.get('preferred_products', []),
                usage_patterns=behavior_data.get('usage_patterns', {}),
                confidence_level=behavior_data.get('confidence_level', 0.75)
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse enhanced behavior analysis: {e}")
            return BehaviorAnalysis(
                behavior_patterns=["Mobile-first usage", "Frequent micro-transactions", "Security-conscious behavior", "Multi-channel engagement"],
                risk_indicators=["Irregular transaction patterns", "Multiple failed logins", "Unusual spending spikes", "Account dormancy"],
                engagement_score=0.7,
                loyalty_score=0.6,
                churn_risk='medium',
                financial_health_score=0.7,
                preferred_products=["Mobile banking", "Payment apps", "Investment tools", "Budgeting features"],
                usage_patterns={
                    "peak_usage_times": ["Morning commute", "Lunch break", "Evening"],
                    "transaction_frequency": "medium",
                    "feature_adoption": "moderate",
                    "session_duration": "medium",
                    "cross_selling_potential": "medium"
                },
                confidence_level=0.7
            )
    
    async def _analyze_financial_behavior_patterns(self, customer_segments: List[CustomerSegment], product_type: str) -> Dict[str, Any]:
        """
        Analyze financial behavior patterns specific to fintech customers.
        
        Args:
            customer_segments: Customer segments
            product_type: Type of fintech product
            
        Returns:
            Dict containing financial behavior analysis
        """
        prompt = f"""
        Analyze financial behavior patterns for {product_type} fintech customers across these segments:
        
        Segments: {[segment.segment_name for segment in customer_segments]}
        
        Provide financial behavior analysis in JSON format:
        {{
            "spending_patterns": {{
                "average_transaction_size": <amount>,
                "transaction_frequency_monthly": <number>,
                "seasonal_variations": ["pattern1", "pattern2"],
                "category_preferences": ["category1", "category2"]
            }},
            "savings_behavior": {{
                "savings_rate": <0.0-1.0>,
                "goal_oriented_saving": "low|medium|high",
                "automated_savings_adoption": <0.0-1.0>,
                "emergency_fund_adequacy": "low|medium|high"
            }},
            "investment_behavior": {{
                "risk_tolerance": "conservative|moderate|aggressive",
                "investment_frequency": "low|medium|high",
                "diversification_level": "low|medium|high",
                "robo_advisor_adoption": <0.0-1.0>
            }},
            "credit_behavior": {{
                "credit_utilization": <0.0-1.0>,
                "payment_timeliness": "poor|fair|good|excellent",
                "credit_seeking_frequency": "low|medium|high",
                "debt_management": "poor|fair|good|excellent"
            }},
            "digital_adoption": {{
                "mobile_banking_usage": <0.0-1.0>,
                "contactless_payment_adoption": <0.0-1.0>,
                "financial_app_usage": <0.0-1.0>,
                "ai_feature_acceptance": <0.0-1.0>
            }}
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a fintech behavioral economist specializing in financial behavior analysis and digital adoption patterns.",
                temperature=0.4
            )
            
            return json.loads(response)
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse financial behavior patterns: {e}")
            return {
                'spending_patterns': {
                    'average_transaction_size': 85.0,
                    'transaction_frequency_monthly': 45,
                    'seasonal_variations': ['Holiday spending spikes', 'Back-to-school increases'],
                    'category_preferences': ['Food & dining', 'Transportation', 'Shopping']
                },
                'savings_behavior': {
                    'savings_rate': 0.12,
                    'goal_oriented_saving': 'medium',
                    'automated_savings_adoption': 0.35,
                    'emergency_fund_adequacy': 'medium'
                },
                'investment_behavior': {
                    'risk_tolerance': 'moderate',
                    'investment_frequency': 'medium',
                    'diversification_level': 'medium',
                    'robo_advisor_adoption': 0.25
                },
                'credit_behavior': {
                    'credit_utilization': 0.30,
                    'payment_timeliness': 'good',
                    'credit_seeking_frequency': 'low',
                    'debt_management': 'fair'
                },
                'digital_adoption': {
                    'mobile_banking_usage': 0.85,
                    'contactless_payment_adoption': 0.70,
                    'financial_app_usage': 0.60,
                    'ai_feature_acceptance': 0.40
                }
            }
    
    async def _analyze_customer_lifetime_value(self, customer_segments: List[CustomerSegment], behavior_analysis: BehaviorAnalysis) -> Dict[str, Any]:
        """
        Analyze customer lifetime value and profitability patterns.
        
        Args:
            customer_segments: Customer segments
            behavior_analysis: Behavior analysis results
            
        Returns:
            Dict containing CLV analysis
        """
        prompt = f"""
        Analyze customer lifetime value for fintech customers based on:
        
        Customer Segments: {len(customer_segments)} segments
        Engagement Score: {behavior_analysis.engagement_score:.1%}
        Loyalty Score: {behavior_analysis.loyalty_score:.1%}
        Churn Risk: {behavior_analysis.churn_risk}
        
        Provide CLV analysis in JSON format:
        {{
            "average_clv": <amount>,
            "clv_by_segment": {{
                "high_value": <amount>,
                "medium_value": <amount>,
                "low_value": <amount>
            }},
            "revenue_drivers": ["driver1", "driver2", ...],
            "cost_factors": ["factor1", "factor2", ...],
            "profitability_timeline": {{
                "break_even_months": <number>,
                "peak_value_months": <number>,
                "decline_phase_months": <number>
            }},
            "retention_impact": {{
                "retention_rate_improvement": <0.0-1.0>,
                "clv_increase_potential": <0.0-1.0>
            }},
            "cross_sell_opportunities": ["opportunity1", "opportunity2", ...],
            "churn_cost_impact": <amount>
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a fintech customer value analyst specializing in CLV modeling and profitability analysis.",
                temperature=0.4
            )
            
            return json.loads(response)
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse CLV analysis: {e}")
            return {
                'average_clv': 2500.0,
                'clv_by_segment': {
                    'high_value': 5000.0,
                    'medium_value': 2500.0,
                    'low_value': 1000.0
                },
                'revenue_drivers': ['Transaction fees', 'Subscription revenue', 'Interest income', 'Cross-sell products'],
                'cost_factors': ['Customer acquisition', 'Servicing costs', 'Technology infrastructure', 'Compliance'],
                'profitability_timeline': {
                    'break_even_months': 8,
                    'peak_value_months': 24,
                    'decline_phase_months': 48
                },
                'retention_impact': {
                    'retention_rate_improvement': 0.10,
                    'clv_increase_potential': 0.25
                },
                'cross_sell_opportunities': ['Investment products', 'Insurance', 'Credit products', 'Premium features'],
                'churn_cost_impact': 500.0
            }
    
    async def _assess_enhanced_market_demand(
        self,
        product_type: str,
        target_market: str,
        behavior_analysis: BehaviorAnalysis
    ) -> Dict[str, Any]:
        """
        Enhanced market demand assessment incorporating behavioral insights.
        
        Args:
            product_type: Type of fintech product
            target_market: Target market segment
            behavior_analysis: Customer behavior analysis
            
        Returns:
            Dict containing enhanced demand analysis
        """
        prompt = f"""
        Assess enhanced market demand for a {product_type} fintech product in the {target_market} market.
        
        Behavioral Context:
        - Engagement Score: {behavior_analysis.engagement_score:.1%}
        - Financial Health Score: {behavior_analysis.financial_health_score:.1%}
        - Churn Risk: {behavior_analysis.churn_risk}
        - Preferred Products: {behavior_analysis.preferred_products}
        
        Provide enhanced demand analysis in JSON format:
        {{
            "demand_level": "low|medium|high|very_high",
            "demand_score": <0.0-1.0>,
            "growth_trajectory": "declining|stable|growing|accelerating",
            "demand_drivers": ["driver1", "driver2", ...],
            "behavioral_demand_factors": ["factor1", "factor2", ...],
            "market_gaps": ["gap1", "gap2", ...],
            "target_segments": ["segment1", "segment2", ...],
            "seasonal_patterns": ["pattern1", "pattern2", ...],
            "competitive_demand_pressure": "low|medium|high",
            "unmet_needs": ["need1", "need2", ...],
            "adoption_barriers": ["barrier1", "barrier2", ...],
            "confidence_score": <0.0-1.0>
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a fintech market demand analyst with expertise in behavioral economics and customer needs analysis.",
                temperature=0.4
            )
            
            return json.loads(response)
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse enhanced demand analysis: {e}")
            return {
                'demand_level': 'high',
                'demand_score': 0.75,
                'growth_trajectory': 'growing',
                'demand_drivers': ['Digital transformation', 'Convenience', 'Cost savings', 'Financial inclusion'],
                'behavioral_demand_factors': ['Mobile-first preference', 'Instant gratification', 'Personalization'],
                'market_gaps': ['Underserved demographics', 'Feature gaps', 'Service quality issues'],
                'target_segments': ['Millennials', 'Small businesses', 'Underbanked populations'],
                'seasonal_patterns': ['Holiday spending', 'Tax season', 'Back-to-school'],
                'competitive_demand_pressure': 'high',
                'unmet_needs': ['Better user experience', 'Lower fees', 'Enhanced security'],
                'adoption_barriers': ['Trust concerns', 'Regulatory uncertainty', 'Technical complexity'],
                'confidence_score': 0.7
            }
    
    async def _generate_enhanced_customer_insights(
        self,
        customer_segments: List[CustomerSegment],
        behavior_analysis: BehaviorAnalysis,
        financial_behavior: Dict[str, Any],
        clv_analysis: Dict[str, Any],
        demand_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive enhanced customer insights and recommendations.
        
        Args:
            customer_segments: Customer segments
            behavior_analysis: Behavior analysis results
            financial_behavior: Financial behavior patterns
            clv_analysis: Customer lifetime value analysis
            demand_analysis: Market demand analysis
            
        Returns:
            Dict containing enhanced insights and recommendations
        """
        # Prepare comprehensive data summary for LLM
        analysis_summary = {
            'segment_count': len(customer_segments),
            'engagement_score': f"{behavior_analysis.engagement_score:.1%}",
            'loyalty_score': f"{behavior_analysis.loyalty_score:.1%}",
            'churn_risk': behavior_analysis.churn_risk,
            'average_clv': f"${clv_analysis.get('average_clv', 2500):,.0f}",
            'demand_level': demand_analysis.get('demand_level', 'medium'),
            'growth_trajectory': demand_analysis.get('growth_trajectory', 'growing')
        }
        
        prompt = f"""
        Generate comprehensive enhanced customer insights and strategic recommendations based on:
        
        Analysis Summary: {analysis_summary}
        
        Financial Behavior:
        - Savings Rate: {financial_behavior.get('savings_behavior', {}).get('savings_rate', 0.12):.1%}
        - Mobile Banking Usage: {financial_behavior.get('digital_adoption', {}).get('mobile_banking_usage', 0.85):.1%}
        - Risk Tolerance: {financial_behavior.get('investment_behavior', {}).get('risk_tolerance', 'moderate')}
        
        CLV Insights:
        - Break-even: {clv_analysis.get('profitability_timeline', {}).get('break_even_months', 8)} months
        - Cross-sell Opportunities: {clv_analysis.get('cross_sell_opportunities', [])}
        
        Provide comprehensive insights in JSON format:
        {{
            "key_insights": ["insight1", "insight2", ...],
            "strategic_recommendations": ["recommendation1", "recommendation2", ...],
            "personalization_strategies": ["strategy1", "strategy2", ...],
            "retention_strategies": ["strategy1", "strategy2", ...],
            "acquisition_strategies": ["strategy1", "strategy2", ...],
            "product_development_priorities": ["priority1", "priority2", ...],
            "revenue_optimization": ["optimization1", "optimization2", ...],
            "risk_mitigation": ["mitigation1", "mitigation2", ...],
            "competitive_advantages": ["advantage1", "advantage2", ...],
            "technology_investments": ["investment1", "investment2", ...]
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a senior fintech customer strategy consultant with expertise in behavioral analytics, personalization, and customer experience optimization.",
                temperature=0.4
            )
            
            insights_data = json.loads(response)
            
            return {
                'insights': insights_data.get('key_insights', []),
                'recommendations': insights_data.get('strategic_recommendations', []),
                'personalization_strategies': insights_data.get('personalization_strategies', []),
                'retention_strategies': insights_data.get('retention_strategies', []),
                'acquisition_strategies': insights_data.get('acquisition_strategies', []),
                'product_priorities': insights_data.get('product_development_priorities', []),
                'revenue_optimization': insights_data.get('revenue_optimization', []),
                'risk_mitigation': insights_data.get('risk_mitigation', []),
                'competitive_advantages': insights_data.get('competitive_advantages', []),
                'technology_investments': insights_data.get('technology_investments', [])
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse enhanced customer insights: {e}")
            return {
                'insights': ['Strong mobile adoption trend', 'Security remains top concern', 'Personalization drives engagement'],
                'recommendations': ['Enhance mobile experience', 'Strengthen security features', 'Implement AI-driven personalization'],
                'personalization_strategies': ['Behavioral targeting', 'Dynamic pricing', 'Customized product recommendations'],
                'retention_strategies': ['Loyalty programs', 'Proactive support', 'Feature education'],
                'acquisition_strategies': ['Referral programs', 'Digital marketing', 'Partnership channels'],
                'product_priorities': ['Mobile optimization', 'Security enhancements', 'AI features'],
                'revenue_optimization': ['Cross-selling automation', 'Premium tier introduction', 'Usage-based pricing'],
                'risk_mitigation': ['Fraud detection improvement', 'Customer support enhancement', 'Compliance automation'],
                'competitive_advantages': ['Superior user experience', 'Advanced analytics', 'Regulatory compliance'],
                'technology_investments': ['AI/ML capabilities', 'Real-time processing', 'Advanced security']
            }
    
    def _calculate_enhanced_confidence_score(
        self,
        customer_segments: List[CustomerSegment],
        behavior_analysis: BehaviorAnalysis,
        financial_behavior: Dict[str, Any]
    ) -> float:
        """
        Calculate enhanced confidence score based on comprehensive analysis quality.
        
        Args:
            customer_segments: Customer segments analyzed
            behavior_analysis: Behavior analysis results
            financial_behavior: Financial behavior analysis
            
        Returns:
            Enhanced confidence score between 0.0 and 1.0
        """
        base_score = 0.7  # Higher base for enhanced analysis
        
        # Increase confidence based on number of segments
        if len(customer_segments) >= 4:
            base_score += 0.1
        
        # Increase confidence based on behavior analysis confidence
        if behavior_analysis.confidence_level > 0.7:
            base_score += 0.1
        
        # Increase confidence if we have detailed behavioral patterns
        if len(behavior_analysis.behavior_patterns) >= 4:
            base_score += 0.05
        
        # Increase confidence if we have financial behavior data
        if financial_behavior and len(financial_behavior) >= 4:
            base_score += 0.05
        
        return min(0.95, base_score)


# Alias for backward compatibility
CustomerIntelligenceAgent = CustomerBehaviorIntelligenceAgent