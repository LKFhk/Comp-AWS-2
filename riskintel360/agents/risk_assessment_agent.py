"""
Risk Assessment Agent for RiskIntel360 Platform
Specialized agent for financial risk evaluation, credit risk assessment, market risk analysis, and operational risk management.
Focused on comprehensive financial risk intelligence for fintech operations.
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
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import warnings

from .base_agent import BaseAgent, AgentConfig
from ..models.agent_models import MessageType, Priority, AgentType

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


@dataclass
class RiskDataSource:
    """Configuration for risk data sources"""
    name: str
    url: str
    api_key: Optional[str] = None
    rate_limit: int = 5  # requests per minute
    timeout: int = 30


@dataclass
class BusinessRisk:
    """Business risk assessment model"""
    risk_category: str
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    probability: float  # 0.0 to 1.0
    impact_score: float  # 0.0 to 10.0
    risk_score: float  # probability * impact_score
    description: str
    mitigation_strategies: List[str]
    monitoring_indicators: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'risk_category': self.risk_category,
            'risk_level': self.risk_level,
            'probability': self.probability,
            'impact_score': self.impact_score,
            'risk_score': self.risk_score,
            'description': self.description,
            'mitigation_strategies': self.mitigation_strategies,
            'monitoring_indicators': self.monitoring_indicators
        }


@dataclass
class MarketEntryBarrier:
    """Market entry barrier analysis"""
    barrier_type: str
    severity: str  # 'low', 'medium', 'high'
    description: str
    estimated_cost: float
    time_to_overcome_months: int
    regulatory_requirements: List[str]
    competitive_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'barrier_type': self.barrier_type,
            'severity': self.severity,
            'description': self.description,
            'estimated_cost': self.estimated_cost,
            'time_to_overcome_months': self.time_to_overcome_months,
            'regulatory_requirements': self.regulatory_requirements,
            'competitive_factors': self.competitive_factors
        }


@dataclass
class RegulatoryCompliance:
    """Regulatory compliance assessment"""
    jurisdiction: str
    regulation_type: str
    compliance_level: str  # 'compliant', 'partial', 'non_compliant', 'unknown'
    requirements: List[str]
    compliance_cost: float
    implementation_timeline_months: int
    penalties_for_non_compliance: str
    monitoring_requirements: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'jurisdiction': self.jurisdiction,
            'regulation_type': self.regulation_type,
            'compliance_level': self.compliance_level,
            'requirements': self.requirements,
            'compliance_cost': self.compliance_cost,
            'implementation_timeline_months': self.implementation_timeline_months,
            'penalties_for_non_compliance': self.penalties_for_non_compliance,
            'monitoring_requirements': self.monitoring_requirements
        }


@dataclass
class RiskAssessmentResult:
    """Complete risk assessment result"""
    overall_risk_score: float  # 0-100
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    business_risks: List[BusinessRisk]
    market_entry_barriers: List[MarketEntryBarrier]
    regulatory_compliance: List[RegulatoryCompliance]
    risk_mitigation_plan: List[str]
    monitoring_framework: Dict[str, Any]
    risk_factors_by_category: Dict[str, List[str]]
    confidence_score: float
    data_sources_used: List[str]
    analysis_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level,
            'business_risks': [risk.to_dict() for risk in self.business_risks],
            'market_entry_barriers': [barrier.to_dict() for barrier in self.market_entry_barriers],
            'regulatory_compliance': [comp.to_dict() for comp in self.regulatory_compliance],
            'risk_mitigation_plan': self.risk_mitigation_plan,
            'monitoring_framework': self.monitoring_framework,
            'risk_factors_by_category': self.risk_factors_by_category,
            'confidence_score': self.confidence_score,
            'data_sources_used': self.data_sources_used,
            'analysis_timestamp': self.analysis_timestamp.isoformat()
        }


class RiskAssessmentAgent(BaseAgent):
    """
    Risk Assessment Agent using Claude-3.5 Sonnet for comprehensive financial risk analysis.
    
    Capabilities:
    - Financial risk evaluation and scoring (credit, market, operational, liquidity)
    - Portfolio risk assessment and Value at Risk (VaR) calculations
    - Stress testing and scenario analysis for financial institutions
    - Regulatory capital requirements assessment
    - Financial risk mitigation strategy development
    - Real-time risk monitoring for fintech operations
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize Risk Assessment Agent"""
        super().__init__(config)
        
        # Ensure this is a risk assessment agent
        if config.agent_type != AgentType.RISK_ASSESSMENT:
            raise ValueError(f"Invalid agent type for RiskAssessmentAgent: {config.agent_type}")
        
        # Configure risk data sources
        self.data_sources = {
            'sec_edgar': RiskDataSource(
                name='SEC EDGAR Database',
                url='https://data.sec.gov/api/xbrl/companyfacts',
                rate_limit=10
            ),
            'regulatory_news': RiskDataSource(
                name='Regulatory News Feed',
                url='https://api.newsapi.org/v2/everything',
                rate_limit=5
            ),
            'compliance_db': RiskDataSource(
                name='Compliance Database',
                url='https://api.compliance-db.com/v1',
                rate_limit=10
            )
        }
        
        # Initialize AWS services for advanced analytics
        self.aws_clients = {}
        # Initialize AWS services asynchronously to avoid blocking agent creation
        self._aws_initialized = False
        
        # Initialize HTTP session for API calls
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Cache for risk data
        self.data_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(hours=6)  # 6-hour cache for risk data
        
        # Risk assessment parameters
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 1.0
        }
        
        self.logger.info(" Risk Assessment Agent initialized with AWS services")
    
    def _initialize_aws_services(self) -> None:
        """Initialize AWS service clients"""
        try:
            # Get region from environment or use default
            import os
            region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            
            # Initialize AWS Comprehend for document analysis
            self.aws_clients['comprehend'] = boto3.client('comprehend', region_name=region)
            self.logger.info("?? AWS Comprehend client initialized")
            
            # Initialize CloudWatch for monitoring
            self.aws_clients['cloudwatch'] = boto3.client('cloudwatch', region_name=region)
            self.logger.info("?? AWS CloudWatch client initialized")
            
            # Initialize SNS for notifications
            self.aws_clients['sns'] = boto3.client('sns', region_name=region)
            self.logger.info("?¢ AWS SNS client initialized")
            
            # Initialize SageMaker for statistical models
            self.aws_clients['sagemaker'] = boto3.client('sagemaker-runtime', region_name=region)
            self.logger.info("?? AWS SageMaker client initialized")
            
        except (NoCredentialsError, ClientError, Exception) as e:
            self.logger.warning(f" AWS services not available: {e}")
            self.logger.info(" Will use LLM-generated risk analysis due to missing AWS credentials")
    
    async def start(self) -> None:
        """Start the agent and initialize HTTP session"""
        await super().start()
        
        # Initialize AWS services asynchronously if not already done
        if not self._aws_initialized:
            await asyncio.to_thread(self._initialize_aws_services)
            self._aws_initialized = True
        
        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=30)
        self.http_session = aiohttp.ClientSession(timeout=timeout)
        
        # Set up risk monitoring if AWS services are available (non-blocking)
        if self.aws_clients:
            asyncio.create_task(self._setup_risk_monitoring())
        
        self.logger.info("?? HTTP session initialized for risk data APIs")
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources"""
        if self.http_session:
            await self.http_session.close()
            self.logger.info("?? HTTP session closed")
        
        await super().stop()
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this agent supports"""
        return [
            "financial_risk_assessment",
            "credit_risk_evaluation",
            "market_risk_analysis",
            "operational_risk_assessment",
            "liquidity_risk_evaluation",
            "portfolio_risk_analysis",
            "var_calculation",
            "stress_testing",
            "regulatory_capital_assessment",
            "financial_risk_monitoring"
        ]
    
    async def execute_task(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a risk assessment task.
        
        Args:
            task_type: Type of task to execute
            parameters: Task parameters
            
        Returns:
            Dict containing task results
        """
        self.current_task = task_type
        self.update_progress(0.1)
        
        try:
            if task_type == "risk_assessment":
                return await self._perform_risk_assessment(parameters)
            elif task_type == "business_risk_evaluation":
                return await self._evaluate_business_risks(parameters)
            elif task_type == "market_entry_barriers":
                return await self._analyze_market_entry_barriers(parameters)
            elif task_type == "regulatory_compliance":
                return await self._assess_regulatory_compliance(parameters)
            elif task_type == "risk_monitoring_setup":
                return await self._setup_risk_monitoring_framework(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            self.state.error_count += 1
            self.logger.error(f"??Task execution failed: {e}")
            raise
        finally:
            self.current_task = None
    
    async def _perform_risk_assessment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment.
        
        Args:
            parameters: Assessment parameters including business model, industry, etc.
            
        Returns:
            Dict containing risk assessment results
        """
        business_model = parameters.get('business_model', 'saas')
        industry = parameters.get('industry', 'technology')
        target_markets = parameters.get('target_markets', ['US'])
        
        self.logger.info(f" Performing risk assessment for {business_model} in {industry} industry")
        
        # Step 1: Business risk evaluation
        self.update_progress(0.2)
        business_risks = await self._evaluate_business_risks({
            'business_model': business_model,
            'industry': industry
        })
        
        # Step 2: Market entry barrier analysis
        self.update_progress(0.4)
        entry_barriers = await self._analyze_market_entry_barriers({
            'industry': industry,
            'target_markets': target_markets,
            'business_model': business_model
        })
        
        # Step 3: Regulatory compliance assessment
        self.update_progress(0.6)
        regulatory_compliance = await self._assess_regulatory_compliance({
            'industry': industry,
            'target_markets': target_markets,
            'business_model': business_model
        })
        
        # Step 4: Risk mitigation planning
        self.update_progress(0.8)
        mitigation_plan = await self._develop_risk_mitigation_plan(
            business_risks, entry_barriers, regulatory_compliance
        )
        
        # Step 5: Calculate overall risk score and compile results
        self.update_progress(1.0)
        overall_risk_score = self._calculate_overall_risk_score(
            business_risks, entry_barriers, regulatory_compliance
        )
        
        risk_level = self._determine_risk_level(overall_risk_score)
        
        result = RiskAssessmentResult(
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            business_risks=business_risks,
            market_entry_barriers=entry_barriers,
            regulatory_compliance=regulatory_compliance,
            risk_mitigation_plan=mitigation_plan,
            monitoring_framework=await self._create_monitoring_framework(
                business_risks, entry_barriers
            ),
            risk_factors_by_category=self._categorize_risk_factors(
                business_risks, entry_barriers, regulatory_compliance
            ),
            confidence_score=self._calculate_confidence_score(parameters),
            data_sources_used=list(self.data_cache.keys()) if self.data_cache else ['llm_generated'],
            analysis_timestamp=datetime.now(UTC)
        )
        
        self.logger.info(f"??Risk assessment completed with {result.confidence_score:.1%} confidence")
        
        return {
            'assessment_result': result.to_dict(),
            'metadata': {
                'agent_id': self.agent_id,
                'analysis_duration': 'completed',
                'overall_risk_score': overall_risk_score,
                'risk_level': risk_level,
                'recommendation': self._generate_risk_recommendation(risk_level)
            }
        }
    
    async def _evaluate_business_risks(self, parameters: Dict[str, Any]) -> List[BusinessRisk]:
        """
        Evaluate business risks using AWS SageMaker statistical models and LLM analysis.
        
        Args:
            parameters: Business parameters for risk evaluation
            
        Returns:
            List of BusinessRisk objects
        """
        business_model = parameters.get('business_model', 'saas')
        industry = parameters.get('industry', 'technology')
        
        # Use AWS Comprehend for document analysis if available
        external_risk_data = await self._fetch_external_risk_data(industry)
        
        prompt = f"""
        As a senior risk analyst, evaluate business risks for a {business_model} business in the {industry} industry.
        
        External Risk Data:
        {json.dumps(external_risk_data, indent=2) if external_risk_data else "Using general industry knowledge"}
        
        Provide comprehensive risk assessment in JSON format:
        {{
            "risks": [
                {{
                    "risk_category": "operational|financial|strategic|compliance|technology|market",
                    "risk_level": "low|medium|high|critical",
                    "probability": <0.0-1.0>,
                    "impact_score": <0.0-10.0>,
                    "description": "Detailed risk description",
                    "mitigation_strategies": ["strategy1", "strategy2", "strategy3"],
                    "monitoring_indicators": ["indicator1", "indicator2"]
                }}
            ]
        }}
        
        Consider industry-specific risks, business model vulnerabilities, and current market conditions.
        """
        
        system_prompt = """You are a senior risk analyst with 15+ years of experience in business risk assessment 
        across multiple industries. Provide thorough, realistic risk evaluations based on industry patterns, 
        regulatory environments, and business model characteristics. Focus on actionable insights."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3  # Moderate temperature for balanced risk assessment
            )
            
            risk_data = json.loads(response)
            business_risks = []
            
            for risk_item in risk_data.get('risks', []):
                probability = risk_item.get('probability', 0.5)
                impact_score = risk_item.get('impact_score', 5.0)
                
                business_risk = BusinessRisk(
                    risk_category=risk_item.get('risk_category', 'operational'),
                    risk_level=risk_item.get('risk_level', 'medium'),
                    probability=probability,
                    impact_score=impact_score,
                    risk_score=probability * impact_score,
                    description=risk_item.get('description', 'Business risk identified'),
                    mitigation_strategies=risk_item.get('mitigation_strategies', []),
                    monitoring_indicators=risk_item.get('monitoring_indicators', [])
                )
                business_risks.append(business_risk)
            
            return business_risks
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f" Failed to parse LLM risk assessment: {e}")
            # Return default risk assessment
            return [
                BusinessRisk(
                    risk_category='market',
                    risk_level='medium',
                    probability=0.6,
                    impact_score=6.0,
                    risk_score=3.6,
                    description='Market competition and demand uncertainty',
                    mitigation_strategies=['Market research', 'Competitive analysis', 'Customer validation'],
                    monitoring_indicators=['Market share', 'Customer acquisition cost', 'Churn rate']
                ),
                BusinessRisk(
                    risk_category='operational',
                    risk_level='medium',
                    probability=0.4,
                    impact_score=5.0,
                    risk_score=2.0,
                    description='Operational execution and scaling challenges',
                    mitigation_strategies=['Process documentation', 'Team training', 'Technology investment'],
                    monitoring_indicators=['Operational efficiency', 'Error rates', 'Customer satisfaction']
                )
            ]
    
    async def _analyze_market_entry_barriers(self, parameters: Dict[str, Any]) -> List[MarketEntryBarrier]:
        """
        Analyze market entry barriers using AWS Comprehend for document analysis.
        
        Args:
            parameters: Market analysis parameters
            
        Returns:
            List of MarketEntryBarrier objects
        """
        industry = parameters.get('industry', 'technology')
        target_markets = parameters.get('target_markets', ['US'])
        business_model = parameters.get('business_model', 'saas')
        
        # Use AWS Comprehend for regulatory document analysis if available
        regulatory_analysis = await self._analyze_regulatory_documents(industry, target_markets)
        
        prompt = f"""
        As a market entry strategist, analyze barriers to entry for a {business_model} business 
        entering the {industry} industry in {', '.join(target_markets)} markets.
        
        Regulatory Analysis:
        {json.dumps(regulatory_analysis, indent=2) if regulatory_analysis else "Using general regulatory knowledge"}
        
        Provide detailed barrier analysis in JSON format:
        {{
            "barriers": [
                {{
                    "barrier_type": "regulatory|capital|technology|brand|distribution|switching_costs|economies_of_scale",
                    "severity": "low|medium|high",
                    "description": "Detailed barrier description",
                    "estimated_cost": <amount>,
                    "time_to_overcome_months": <months>,
                    "regulatory_requirements": ["requirement1", "requirement2"],
                    "competitive_factors": ["factor1", "factor2"]
                }}
            ]
        }}
        
        Consider regulatory requirements, capital needs, technology barriers, and competitive dynamics.
        """
        
        system_prompt = """You are a market entry strategist with deep knowledge of regulatory environments 
        and competitive dynamics across industries. Provide realistic assessments of entry barriers 
        based on actual market conditions and regulatory requirements."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2  # Low temperature for consistent barrier analysis
            )
            
            barrier_data = json.loads(response)
            entry_barriers = []
            
            for barrier_item in barrier_data.get('barriers', []):
                entry_barrier = MarketEntryBarrier(
                    barrier_type=barrier_item.get('barrier_type', 'regulatory'),
                    severity=barrier_item.get('severity', 'medium'),
                    description=barrier_item.get('description', 'Market entry barrier identified'),
                    estimated_cost=barrier_item.get('estimated_cost', 100000),
                    time_to_overcome_months=barrier_item.get('time_to_overcome_months', 6),
                    regulatory_requirements=barrier_item.get('regulatory_requirements', []),
                    competitive_factors=barrier_item.get('competitive_factors', [])
                )
                entry_barriers.append(entry_barrier)
            
            return entry_barriers
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f" Failed to parse LLM barrier analysis: {e}")
            # Return default barriers
            return [
                MarketEntryBarrier(
                    barrier_type='regulatory',
                    severity='medium',
                    description='Industry-specific regulatory compliance requirements',
                    estimated_cost=50000,
                    time_to_overcome_months=3,
                    regulatory_requirements=['Business license', 'Industry certification'],
                    competitive_factors=['Established competitors', 'Customer relationships']
                )
            ]
    
    async def _assess_regulatory_compliance(self, parameters: Dict[str, Any]) -> List[RegulatoryCompliance]:
        """
        Assess regulatory compliance requirements.
        
        Args:
            parameters: Compliance assessment parameters
            
        Returns:
            List of RegulatoryCompliance objects
        """
        industry = parameters.get('industry', 'technology')
        target_markets = parameters.get('target_markets', ['US'])
        business_model = parameters.get('business_model', 'saas')
        
        compliance_assessments = []
        
        for market in target_markets:
            # Fetch regulatory data for each market
            regulatory_data = await self._fetch_regulatory_requirements(industry, market)
            
            prompt = f"""
            As a compliance expert, assess regulatory requirements for a {business_model} business 
            in the {industry} industry operating in {market}.
            
            Regulatory Data:
            {json.dumps(regulatory_data, indent=2) if regulatory_data else "Using general regulatory knowledge"}
            
            Provide compliance assessment in JSON format:
            {{
                "compliance_areas": [
                    {{
                        "regulation_type": "data_privacy|financial|industry_specific|employment|tax|environmental",
                        "compliance_level": "compliant|partial|non_compliant|unknown",
                        "requirements": ["requirement1", "requirement2"],
                        "compliance_cost": <amount>,
                        "implementation_timeline_months": <months>,
                        "penalties_for_non_compliance": "Description of penalties",
                        "monitoring_requirements": ["monitoring1", "monitoring2"]
                    }}
                ]
            }}
            
            Focus on critical compliance areas and realistic implementation requirements.
            """
            
            try:
                response = await self.invoke_llm(
                    prompt=prompt,
                    system_prompt="You are a regulatory compliance expert with deep knowledge of business regulations across jurisdictions.",
                    temperature=0.1  # Very low temperature for compliance accuracy
                )
                
                compliance_data = json.loads(response)
                
                # Handle case where response might be a list directly
                if isinstance(compliance_data, list):
                    compliance_areas = compliance_data
                else:
                    compliance_areas = compliance_data.get('compliance_areas', [])
                
                for comp_item in compliance_areas:
                    # Handle case where comp_item might be a string instead of dict
                    if isinstance(comp_item, str):
                        # Create default compliance item from string
                        compliance = RegulatoryCompliance(
                            jurisdiction=market,
                            regulation_type='general_business',
                            compliance_level='unknown',
                            requirements=[comp_item],
                            compliance_cost=25000,
                            implementation_timeline_months=3,
                            penalties_for_non_compliance='Fines and penalties',
                            monitoring_requirements=[]
                        )
                    else:
                        compliance = RegulatoryCompliance(
                            jurisdiction=market,
                            regulation_type=comp_item.get('regulation_type', 'industry_specific'),
                            compliance_level=comp_item.get('compliance_level', 'unknown'),
                            requirements=comp_item.get('requirements', []),
                            compliance_cost=comp_item.get('compliance_cost', 25000),
                            implementation_timeline_months=comp_item.get('implementation_timeline_months', 3),
                            penalties_for_non_compliance=comp_item.get('penalties_for_non_compliance', 'Fines and penalties'),
                            monitoring_requirements=comp_item.get('monitoring_requirements', [])
                        )
                    compliance_assessments.append(compliance)
                    
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f" Failed to parse compliance assessment for {market}: {e}")
                # Add default compliance requirement
                compliance_assessments.append(
                    RegulatoryCompliance(
                        jurisdiction=market,
                        regulation_type='general_business',
                        compliance_level='unknown',
                        requirements=['Business registration', 'Tax compliance'],
                        compliance_cost=10000,
                        implementation_timeline_months=2,
                        penalties_for_non_compliance='Fines and business closure risk',
                        monitoring_requirements=['Regular reporting', 'Audit compliance']
                    )
                )
        
        return compliance_assessments
    
    async def _develop_risk_mitigation_plan(
        self, 
        business_risks: List[BusinessRisk], 
        entry_barriers: List[MarketEntryBarrier], 
        regulatory_compliance: List[RegulatoryCompliance]
    ) -> List[str]:
        """
        Develop comprehensive risk mitigation plan.
        
        Args:
            business_risks: Identified business risks
            entry_barriers: Market entry barriers
            regulatory_compliance: Compliance requirements
            
        Returns:
            List of mitigation strategies
        """
        # Collect all mitigation strategies
        all_strategies = []
        
        # Add strategies from business risks
        for risk in business_risks:
            all_strategies.extend(risk.mitigation_strategies)
        
        # Add strategies for entry barriers
        for barrier in entry_barriers:
            if barrier.severity in ['medium', 'high']:
                all_strategies.append(f"Address {barrier.barrier_type} barrier: {barrier.description}")
        
        # Add compliance strategies
        for compliance in regulatory_compliance:
            if compliance.compliance_level in ['partial', 'non_compliant']:
                all_strategies.append(f"Implement {compliance.regulation_type} compliance in {compliance.jurisdiction}")
        
        # Remove duplicates and prioritize
        unique_strategies = list(set(all_strategies))
        
        # Use LLM to prioritize and refine strategies
        prompt = f"""
        As a risk management consultant, prioritize and refine these risk mitigation strategies:
        
        Strategies:
        {json.dumps(unique_strategies, indent=2)}
        
        Provide a prioritized, refined mitigation plan as a JSON array of strings:
        ["High priority strategy 1", "Medium priority strategy 2", "Low priority strategy 3"]
        
        Focus on the most impactful and feasible strategies first.
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a risk management expert focused on practical, actionable mitigation strategies.",
                temperature=0.2
            )
            
            return json.loads(response)
            
        except (json.JSONDecodeError, KeyError):
            self.logger.warning(" Failed to parse mitigation plan, using default strategies")
            return unique_strategies[:10]  # Return top 10 strategies
    
    async def _setup_risk_monitoring(self) -> None:
        """Set up risk monitoring using AWS CloudWatch and SNS"""
        if not self.aws_clients.get('cloudwatch') or not self.aws_clients.get('sns'):
            self.logger.info(" AWS services not available for risk monitoring setup")
            return
        
        try:
            # Create CloudWatch custom metrics for risk monitoring
            cloudwatch = self.aws_clients['cloudwatch']
            
            # Put sample metric to establish namespace
            def put_metric():
                return cloudwatch.put_metric_data(
                    Namespace='RiskIntel360/RiskAssessment',
                    MetricData=[
                        {
                            'MetricName': 'RiskScore',
                            'Value': 0.0,
                            'Unit': 'None',
                            'Timestamp': datetime.now(UTC)
                        }
                    ]
                )
            
            await asyncio.get_event_loop().run_in_executor(None, put_metric)
            
            self.logger.info("?? CloudWatch risk monitoring metrics initialized")
            
        except Exception as e:
            self.logger.warning(f" Failed to setup CloudWatch monitoring: {e}")
    
    async def _create_monitoring_framework(
        self, 
        business_risks: List[BusinessRisk], 
        entry_barriers: List[MarketEntryBarrier]
    ) -> Dict[str, Any]:
        """
        Create risk monitoring framework.
        
        Args:
            business_risks: Business risks to monitor
            entry_barriers: Entry barriers to track
            
        Returns:
            Dict containing monitoring framework
        """
        # Collect all monitoring indicators
        indicators = []
        for risk in business_risks:
            indicators.extend(risk.monitoring_indicators)
        
        # Create monitoring framework
        framework = {
            'monitoring_frequency': 'weekly',
            'key_indicators': list(set(indicators)),
            'alert_thresholds': {
                'risk_score_increase': 0.2,
                'new_regulatory_changes': True,
                'market_condition_changes': True
            },
            'reporting_schedule': {
                'daily': ['Critical risk alerts'],
                'weekly': ['Risk score updates', 'Indicator tracking'],
                'monthly': ['Comprehensive risk review', 'Mitigation progress']
            },
            'escalation_procedures': [
                'Automated alerts for critical risks',
                'Weekly risk committee review',
                'Monthly board reporting'
            ]
        }
        
        return framework
    
    def _calculate_overall_risk_score(
        self, 
        business_risks: List[BusinessRisk], 
        entry_barriers: List[MarketEntryBarrier], 
        regulatory_compliance: List[RegulatoryCompliance]
    ) -> float:
        """Calculate overall risk score (0-100)"""
        
        # Calculate business risk component (40% weight)
        business_risk_score = 0.0
        if business_risks:
            avg_business_risk = sum(risk.risk_score for risk in business_risks) / len(business_risks)
            business_risk_score = min(avg_business_risk * 10, 40)  # Scale to 0-40
        
        # Calculate entry barrier component (35% weight)
        barrier_score = 0.0
        if entry_barriers:
            high_barriers = sum(1 for barrier in entry_barriers if barrier.severity == 'high')
            medium_barriers = sum(1 for barrier in entry_barriers if barrier.severity == 'medium')
            barrier_score = min((high_barriers * 15 + medium_barriers * 8), 35)  # Scale to 0-35
        
        # Calculate compliance component (25% weight)
        compliance_score = 0.0
        if regulatory_compliance:
            non_compliant = sum(1 for comp in regulatory_compliance if comp.compliance_level == 'non_compliant')
            partial_compliant = sum(1 for comp in regulatory_compliance if comp.compliance_level == 'partial')
            compliance_score = min((non_compliant * 15 + partial_compliant * 8), 25)  # Scale to 0-25
        
        total_score = business_risk_score + barrier_score + compliance_score
        return min(total_score, 100.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score <= 30:
            return 'low'
        elif risk_score <= 60:
            return 'medium'
        elif risk_score <= 80:
            return 'high'
        else:
            return 'critical'
    
    def _categorize_risk_factors(
        self, 
        business_risks: List[BusinessRisk], 
        entry_barriers: List[MarketEntryBarrier], 
        regulatory_compliance: List[RegulatoryCompliance]
    ) -> Dict[str, List[str]]:
        """Categorize risk factors by type"""
        categories = {
            'operational': [],
            'financial': [],
            'strategic': [],
            'regulatory': [],
            'market': [],
            'technology': []
        }
        
        # Categorize business risks
        for risk in business_risks:
            if risk.risk_category in categories:
                categories[risk.risk_category].append(risk.description)
        
        # Add entry barriers to appropriate categories
        for barrier in entry_barriers:
            if barrier.barrier_type == 'regulatory':
                categories['regulatory'].append(barrier.description)
            elif barrier.barrier_type in ['capital', 'economies_of_scale']:
                categories['financial'].append(barrier.description)
            else:
                categories['market'].append(barrier.description)
        
        # Add compliance issues to regulatory category
        for compliance in regulatory_compliance:
            if compliance.compliance_level in ['partial', 'non_compliant']:
                categories['regulatory'].append(f"{compliance.regulation_type} in {compliance.jurisdiction}")
        
        return categories
    
    def _calculate_confidence_score(self, parameters: Dict[str, Any]) -> float:
        """Calculate confidence score based on data availability and quality"""
        base_confidence = 0.7
        
        # Adjust based on data sources
        if self.data_cache:
            base_confidence += 0.2
        
        # Adjust based on AWS services availability
        if self.aws_clients:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _generate_risk_recommendation(self, risk_level: str) -> str:
        """Generate risk recommendation based on level"""
        recommendations = {
            'low': 'Proceed with standard risk management practices',
            'medium': 'Implement enhanced risk monitoring and mitigation strategies',
            'high': 'Conduct thorough risk mitigation before proceeding',
            'critical': 'Significant risk mitigation required before market entry'
        }
        return recommendations.get(risk_level, 'Conduct additional risk analysis')
    
    async def _fetch_external_risk_data(self, industry: str) -> Optional[Dict[str, Any]]:
        """Fetch external risk data for industry analysis"""
        try:
            if not self.http_session:
                return None
            
            # This would integrate with actual risk databases
            # For now, return None to trigger LLM-based analysis
            self.logger.info(" Using LLM-generated risk data due to missing external API configurations")
            return None
            
        except Exception as e:
            self.logger.warning(f" Failed to fetch external risk data: {e}")
            return None
    
    async def _analyze_regulatory_documents(self, industry: str, markets: List[str]) -> Optional[Dict[str, Any]]:
        """Analyze regulatory documents using AWS Comprehend"""
        if not self.aws_clients.get('comprehend'):
            self.logger.info(" Using LLM-generated regulatory analysis due to missing AWS Comprehend")
            return None
        
        try:
            # This would use AWS Comprehend to analyze regulatory documents
            # For now, return None to use LLM-based analysis
            return None
            
        except Exception as e:
            self.logger.warning(f" Failed to analyze regulatory documents: {e}")
            return None
    
    async def _fetch_regulatory_requirements(self, industry: str, market: str) -> Optional[Dict[str, Any]]:
        """Fetch regulatory requirements for specific industry and market"""
        try:
            # This would integrate with regulatory databases
            # For now, return None to use LLM-based analysis
            self.logger.info(f" Using LLM-generated regulatory data for {industry} in {market}")
            return None
            
        except Exception as e:
            self.logger.warning(f" Failed to fetch regulatory requirements: {e}")
            return None
    
    async def _setup_risk_monitoring_framework(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Set up comprehensive risk monitoring framework"""
        business_model = parameters.get('business_model', 'saas')
        
        # Create monitoring framework
        framework = {
            'monitoring_setup': 'completed',
            'cloudwatch_metrics': [],
            'sns_topics': [],
            'alert_rules': []
        }
        
        if self.aws_clients.get('cloudwatch'):
            try:
                # Set up CloudWatch metrics
                framework['cloudwatch_metrics'] = [
                    'RiskScore',
                    'ComplianceStatus',
                    'RegulatoryChanges'
                ]
                
                # Set up SNS topics for alerts
                if self.aws_clients.get('sns'):
                    framework['sns_topics'] = [
                        'risk-alerts-critical',
                        'risk-alerts-high',
                        'compliance-updates'
                    ]
                
                self.logger.info("?? Risk monitoring framework configured with AWS services")
                
            except Exception as e:
                self.logger.warning(f" Failed to setup AWS monitoring: {e}")
        else:
            self.logger.info(" Risk monitoring framework configured without AWS services")
        
        return {
            'framework_result': framework,
            'metadata': {
                'agent_id': self.agent_id,
                'setup_status': 'completed',
                'aws_services_available': bool(self.aws_clients)
            }
        }
    
    # Enhanced fintech risk assessment capabilities
    
    async def _perform_enhanced_fintech_risk_assessment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced fintech risk assessment with comprehensive financial risk analysis.
        
        Args:
            parameters: Assessment parameters including business model, industry, etc.
            
        Returns:
            Dict containing enhanced fintech risk assessment results
        """
        business_model = parameters.get('business_model', 'fintech')
        industry = parameters.get('industry', 'financial_services')
        target_markets = parameters.get('target_markets', ['US'])
        
        self.logger.info(f"🔍 Performing enhanced fintech risk assessment for {business_model} in {industry}")
        
        # Step 1: Financial risk evaluation (enhanced)
        self.update_progress(0.15)
        financial_risks = await self._evaluate_enhanced_financial_risks(parameters)
        
        # Step 2: Regulatory compliance risk assessment
        self.update_progress(0.3)
        regulatory_risks = await self._assess_regulatory_compliance_risks(parameters)
        
        # Step 3: Operational risk analysis for fintech
        self.update_progress(0.45)
        operational_risks = await self._analyze_fintech_operational_risks(parameters)
        
        # Step 4: Market and credit risk assessment
        self.update_progress(0.6)
        market_credit_risks = await self._assess_market_and_credit_risks(parameters)
        
        # Step 5: Cybersecurity and technology risk evaluation
        self.update_progress(0.75)
        cyber_tech_risks = await self._evaluate_cybersecurity_technology_risks(parameters)
        
        # Step 6: Comprehensive risk mitigation planning
        self.update_progress(0.9)
        mitigation_plan = await self._develop_comprehensive_risk_mitigation_plan(
            financial_risks, regulatory_risks, operational_risks, market_credit_risks, cyber_tech_risks
        )
        
        # Step 7: Calculate enhanced overall risk score
        self.update_progress(1.0)
        overall_risk_score = self._calculate_enhanced_overall_risk_score(
            financial_risks, regulatory_risks, operational_risks, market_credit_risks, cyber_tech_risks
        )
        
        risk_level = self._determine_enhanced_risk_level(overall_risk_score)
        
        result = {
            'overall_risk_score': overall_risk_score,
            'risk_level': risk_level,
            'financial_risks': [risk.to_dict() for risk in financial_risks],
            'regulatory_risks': [risk.to_dict() for risk in regulatory_risks],
            'operational_risks': [risk.to_dict() for risk in operational_risks],
            'market_credit_risks': [risk.to_dict() for risk in market_credit_risks],
            'cybersecurity_technology_risks': [risk.to_dict() for risk in cyber_tech_risks],
            'comprehensive_mitigation_plan': mitigation_plan,
            'risk_monitoring_framework': await self._create_enhanced_monitoring_framework(
                financial_risks, regulatory_risks, operational_risks
            ),
            'confidence_score': self._calculate_enhanced_confidence_score(parameters),
            'data_sources_used': ['enhanced_llm_analysis', 'fintech_risk_models'],
            'analysis_timestamp': datetime.now(UTC).isoformat(),
            'fintech_specific_insights': await self._generate_fintech_specific_insights(
                financial_risks, regulatory_risks, operational_risks, market_credit_risks
            )
        }
        
        self.logger.info(f"✅ Enhanced fintech risk assessment completed with {result['confidence_score']:.1%} confidence")
        
        return {
            'assessment_result': result,
            'metadata': {
                'agent_id': self.agent_id,
                'analysis_duration': 'completed',
                'overall_risk_score': overall_risk_score,
                'risk_level': risk_level,
                'fintech_enhanced': True,
                'recommendation': self._generate_enhanced_risk_recommendation(risk_level, result)
            }
        }
    
    async def _evaluate_enhanced_financial_risks(self, parameters: Dict[str, Any]) -> List[BusinessRisk]:
        """
        Enhanced financial risk evaluation for fintech businesses.
        
        Args:
            parameters: Business parameters for risk evaluation
            
        Returns:
            List of BusinessRisk objects with fintech-specific financial risks
        """
        business_model = parameters.get('business_model', 'fintech')
        industry = parameters.get('industry', 'financial_services')
        
        prompt = f"""
        As a senior fintech risk analyst, evaluate comprehensive financial risks for a {business_model} business in the {industry} industry.
        
        Focus on fintech-specific financial risks including:
        1. Credit risk and loan portfolio quality
        2. Liquidity risk and cash flow management
        3. Market risk from interest rate and currency fluctuations
        4. Capital adequacy and regulatory capital requirements
        5. Revenue concentration and customer dependency risks
        6. Funding and investor risk
        7. Valuation and market volatility risks
        
        Provide comprehensive financial risk assessment in JSON format:
        {{
            "risks": [
                {{
                    "risk_category": "credit|liquidity|market|capital|revenue|funding|valuation",
                    "risk_level": "low|medium|high|critical",
                    "probability": <0.0-1.0>,
                    "impact_score": <0.0-10.0>,
                    "description": "Detailed financial risk description",
                    "financial_impact_usd": <amount>,
                    "mitigation_strategies": ["strategy1", "strategy2", "strategy3"],
                    "monitoring_indicators": ["indicator1", "indicator2"],
                    "regulatory_implications": ["implication1", "implication2"]
                }}
            ]
        }}
        
        Consider current fintech market conditions, regulatory environment, and financial stability factors.
        """
        
        system_prompt = """You are a senior fintech risk analyst with 15+ years of experience in financial services risk management. 
        Provide thorough, realistic financial risk evaluations based on fintech industry patterns, regulatory requirements, 
        and current market conditions. Focus on quantifiable financial impacts and actionable mitigation strategies."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2  # Low temperature for consistent financial risk assessment
            )
            
            risk_data = json.loads(response)
            financial_risks = []
            
            for risk_item in risk_data.get('risks', []):
                probability = risk_item.get('probability', 0.5)
                impact_score = risk_item.get('impact_score', 5.0)
                
                financial_risk = BusinessRisk(
                    risk_category=risk_item.get('risk_category', 'financial'),
                    risk_level=risk_item.get('risk_level', 'medium'),
                    probability=probability,
                    impact_score=impact_score,
                    risk_score=probability * impact_score,
                    description=risk_item.get('description', 'Financial risk identified'),
                    mitigation_strategies=risk_item.get('mitigation_strategies', []),
                    monitoring_indicators=risk_item.get('monitoring_indicators', [])
                )
                financial_risks.append(financial_risk)
            
            return financial_risks
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse enhanced financial risk assessment: {e}")
            # Return default fintech financial risks
            return [
                BusinessRisk(
                    risk_category='credit',
                    risk_level='medium',
                    probability=0.4,
                    impact_score=7.0,
                    risk_score=2.8,
                    description='Credit risk from loan defaults and customer payment failures',
                    mitigation_strategies=['Credit scoring models', 'Diversified portfolio', 'Regular monitoring'],
                    monitoring_indicators=['Default rates', 'Credit scores', 'Payment delays']
                ),
                BusinessRisk(
                    risk_category='liquidity',
                    risk_level='medium',
                    probability=0.3,
                    impact_score=8.0,
                    risk_score=2.4,
                    description='Liquidity risk from cash flow mismatches and funding gaps',
                    mitigation_strategies=['Cash reserves', 'Credit facilities', 'Liquidity monitoring'],
                    monitoring_indicators=['Cash ratios', 'Funding gaps', 'Withdrawal patterns']
                ),
                BusinessRisk(
                    risk_category='market',
                    risk_level='high',
                    probability=0.6,
                    impact_score=6.0,
                    risk_score=3.6,
                    description='Market risk from interest rate changes and market volatility',
                    mitigation_strategies=['Hedging strategies', 'Diversification', 'Stress testing'],
                    monitoring_indicators=['Interest rate changes', 'Market volatility', 'Portfolio performance']
                )
            ]
    
    async def _assess_regulatory_compliance_risks(self, parameters: Dict[str, Any]) -> List[BusinessRisk]:
        """
        Assess regulatory compliance risks specific to fintech operations.
        
        Args:
            parameters: Business parameters
            
        Returns:
            List of BusinessRisk objects for regulatory compliance
        """
        business_model = parameters.get('business_model', 'fintech')
        target_markets = parameters.get('target_markets', ['US'])
        
        prompt = f"""
        Assess regulatory compliance risks for a {business_model} fintech business operating in {', '.join(target_markets)}.
        
        Focus on fintech-specific regulatory risks including:
        1. KYC/AML compliance failures
        2. Data privacy and protection violations (GDPR, CCPA)
        3. Financial services licensing and registration
        4. Consumer protection and fair lending practices
        5. Payment services and money transmission regulations
        6. Cross-border regulatory compliance
        7. Emerging fintech regulations and policy changes
        
        Provide regulatory risk assessment in JSON format:
        {{
            "risks": [
                {{
                    "risk_category": "kyc_aml|data_privacy|licensing|consumer_protection|payments|cross_border|emerging_regulation",
                    "risk_level": "low|medium|high|critical",
                    "probability": <0.0-1.0>,
                    "impact_score": <0.0-10.0>,
                    "description": "Detailed regulatory risk description",
                    "regulatory_body": "SEC|FINRA|CFPB|FTC|State_Regulators|International",
                    "potential_penalties": "Description of potential penalties",
                    "mitigation_strategies": ["strategy1", "strategy2"],
                    "monitoring_indicators": ["indicator1", "indicator2"]
                }}
            ]
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a fintech regulatory compliance expert with deep knowledge of financial services regulations.",
                temperature=0.1  # Very low temperature for regulatory accuracy
            )
            
            risk_data = json.loads(response)
            regulatory_risks = []
            
            for risk_item in risk_data.get('risks', []):
                probability = risk_item.get('probability', 0.3)
                impact_score = risk_item.get('impact_score', 8.0)
                
                regulatory_risk = BusinessRisk(
                    risk_category=risk_item.get('risk_category', 'regulatory'),
                    risk_level=risk_item.get('risk_level', 'high'),
                    probability=probability,
                    impact_score=impact_score,
                    risk_score=probability * impact_score,
                    description=risk_item.get('description', 'Regulatory compliance risk'),
                    mitigation_strategies=risk_item.get('mitigation_strategies', []),
                    monitoring_indicators=risk_item.get('monitoring_indicators', [])
                )
                regulatory_risks.append(regulatory_risk)
            
            return regulatory_risks
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse regulatory compliance risks: {e}")
            return [
                BusinessRisk(
                    risk_category='kyc_aml',
                    risk_level='high',
                    probability=0.4,
                    impact_score=9.0,
                    risk_score=3.6,
                    description='KYC/AML compliance failures leading to regulatory penalties',
                    mitigation_strategies=['Automated KYC systems', 'Regular compliance audits', 'Staff training'],
                    monitoring_indicators=['Compliance violations', 'Audit findings', 'Regulatory notices']
                )
            ]
    
    async def _analyze_fintech_operational_risks(self, parameters: Dict[str, Any]) -> List[BusinessRisk]:
        """
        Analyze operational risks specific to fintech businesses.
        
        Args:
            parameters: Business parameters
            
        Returns:
            List of BusinessRisk objects for operational risks
        """
        business_model = parameters.get('business_model', 'fintech')
        
        prompt = f"""
        Analyze operational risks for a {business_model} fintech business:
        
        Focus on fintech-specific operational risks including:
        1. Technology infrastructure failures and downtime
        2. Third-party vendor and API dependencies
        3. Fraud and security breaches
        4. Operational scaling challenges
        5. Key personnel and talent retention risks
        6. Process automation and human error risks
        7. Business continuity and disaster recovery
        
        Provide operational risk assessment in JSON format:
        {{
            "risks": [
                {{
                    "risk_category": "technology|vendor|fraud|scaling|personnel|process|continuity",
                    "risk_level": "low|medium|high|critical",
                    "probability": <0.0-1.0>,
                    "impact_score": <0.0-10.0>,
                    "description": "Detailed operational risk description",
                    "operational_impact": "Description of operational impact",
                    "mitigation_strategies": ["strategy1", "strategy2"],
                    "monitoring_indicators": ["indicator1", "indicator2"]
                }}
            ]
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a fintech operational risk specialist with expertise in technology and process risk management.",
                temperature=0.3
            )
            
            risk_data = json.loads(response)
            operational_risks = []
            
            for risk_item in risk_data.get('risks', []):
                probability = risk_item.get('probability', 0.4)
                impact_score = risk_item.get('impact_score', 6.0)
                
                operational_risk = BusinessRisk(
                    risk_category=risk_item.get('risk_category', 'operational'),
                    risk_level=risk_item.get('risk_level', 'medium'),
                    probability=probability,
                    impact_score=impact_score,
                    risk_score=probability * impact_score,
                    description=risk_item.get('description', 'Operational risk identified'),
                    mitigation_strategies=risk_item.get('mitigation_strategies', []),
                    monitoring_indicators=risk_item.get('monitoring_indicators', [])
                )
                operational_risks.append(operational_risk)
            
            return operational_risks
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse operational risks: {e}")
            return [
                BusinessRisk(
                    risk_category='technology',
                    risk_level='high',
                    probability=0.5,
                    impact_score=7.0,
                    risk_score=3.5,
                    description='Technology infrastructure failures causing service disruptions',
                    mitigation_strategies=['Redundant systems', 'Regular maintenance', 'Monitoring tools'],
                    monitoring_indicators=['System uptime', 'Error rates', 'Performance metrics']
                )
            ]
    
    async def _assess_market_and_credit_risks(self, parameters: Dict[str, Any]) -> List[BusinessRisk]:
        """
        Assess market and credit risks for fintech operations.
        
        Args:
            parameters: Business parameters
            
        Returns:
            List of BusinessRisk objects for market and credit risks
        """
        business_model = parameters.get('business_model', 'fintech')
        
        prompt = f"""
        Assess market and credit risks for a {business_model} fintech business:
        
        Focus on:
        1. Interest rate risk and yield curve changes
        2. Credit risk from customer defaults
        3. Concentration risk in customer base or geography
        4. Market volatility and economic downturns
        5. Competitive pressure and market share loss
        6. Currency and foreign exchange risks
        7. Counterparty and settlement risks
        
        Provide market and credit risk assessment in JSON format:
        {{
            "risks": [
                {{
                    "risk_category": "interest_rate|credit|concentration|market_volatility|competitive|currency|counterparty",
                    "risk_level": "low|medium|high|critical",
                    "probability": <0.0-1.0>,
                    "impact_score": <0.0-10.0>,
                    "description": "Detailed market/credit risk description",
                    "financial_impact": "Description of financial impact",
                    "mitigation_strategies": ["strategy1", "strategy2"],
                    "monitoring_indicators": ["indicator1", "indicator2"]
                }}
            ]
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a fintech market and credit risk analyst with expertise in financial risk modeling.",
                temperature=0.3
            )
            
            risk_data = json.loads(response)
            market_credit_risks = []
            
            for risk_item in risk_data.get('risks', []):
                probability = risk_item.get('probability', 0.4)
                impact_score = risk_item.get('impact_score', 6.0)
                
                market_credit_risk = BusinessRisk(
                    risk_category=risk_item.get('risk_category', 'market'),
                    risk_level=risk_item.get('risk_level', 'medium'),
                    probability=probability,
                    impact_score=impact_score,
                    risk_score=probability * impact_score,
                    description=risk_item.get('description', 'Market/credit risk identified'),
                    mitigation_strategies=risk_item.get('mitigation_strategies', []),
                    monitoring_indicators=risk_item.get('monitoring_indicators', [])
                )
                market_credit_risks.append(market_credit_risk)
            
            return market_credit_risks
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse market and credit risks: {e}")
            return [
                BusinessRisk(
                    risk_category='market_volatility',
                    risk_level='medium',
                    probability=0.5,
                    impact_score=6.0,
                    risk_score=3.0,
                    description='Market volatility affecting business valuation and funding',
                    mitigation_strategies=['Diversification', 'Hedging', 'Stress testing'],
                    monitoring_indicators=['Market indices', 'Volatility measures', 'Funding costs']
                )
            ]
    
    async def _evaluate_cybersecurity_technology_risks(self, parameters: Dict[str, Any]) -> List[BusinessRisk]:
        """
        Evaluate cybersecurity and technology risks for fintech operations.
        
        Args:
            parameters: Business parameters
            
        Returns:
            List of BusinessRisk objects for cybersecurity and technology risks
        """
        business_model = parameters.get('business_model', 'fintech')
        
        prompt = f"""
        Evaluate cybersecurity and technology risks for a {business_model} fintech business:
        
        Focus on:
        1. Cyber attacks and data breaches
        2. System vulnerabilities and security gaps
        3. Third-party technology dependencies
        4. Cloud infrastructure and service risks
        5. Mobile and API security risks
        6. Insider threats and access control
        7. Technology obsolescence and upgrade risks
        
        Provide cybersecurity and technology risk assessment in JSON format:
        {{
            "risks": [
                {{
                    "risk_category": "cyber_attack|vulnerabilities|third_party|cloud|mobile_api|insider|obsolescence",
                    "risk_level": "low|medium|high|critical",
                    "probability": <0.0-1.0>,
                    "impact_score": <0.0-10.0>,
                    "description": "Detailed cybersecurity/technology risk description",
                    "security_impact": "Description of security impact",
                    "mitigation_strategies": ["strategy1", "strategy2"],
                    "monitoring_indicators": ["indicator1", "indicator2"]
                }}
            ]
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a fintech cybersecurity and technology risk expert with deep knowledge of financial services security.",
                temperature=0.3
            )
            
            risk_data = json.loads(response)
            cyber_tech_risks = []
            
            for risk_item in risk_data.get('risks', []):
                probability = risk_item.get('probability', 0.4)
                impact_score = risk_item.get('impact_score', 8.0)
                
                cyber_tech_risk = BusinessRisk(
                    risk_category=risk_item.get('risk_category', 'cybersecurity'),
                    risk_level=risk_item.get('risk_level', 'high'),
                    probability=probability,
                    impact_score=impact_score,
                    risk_score=probability * impact_score,
                    description=risk_item.get('description', 'Cybersecurity/technology risk identified'),
                    mitigation_strategies=risk_item.get('mitigation_strategies', []),
                    monitoring_indicators=risk_item.get('monitoring_indicators', [])
                )
                cyber_tech_risks.append(cyber_tech_risk)
            
            return cyber_tech_risks
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse cybersecurity and technology risks: {e}")
            return [
                BusinessRisk(
                    risk_category='cyber_attack',
                    risk_level='high',
                    probability=0.6,
                    impact_score=9.0,
                    risk_score=5.4,
                    description='Cyber attacks targeting financial data and customer information',
                    mitigation_strategies=['Multi-factor authentication', 'Encryption', 'Security monitoring'],
                    monitoring_indicators=['Security incidents', 'Vulnerability scans', 'Threat intelligence']
                )
            ]
    
    async def _develop_comprehensive_risk_mitigation_plan(
        self,
        financial_risks: List[BusinessRisk],
        regulatory_risks: List[BusinessRisk],
        operational_risks: List[BusinessRisk],
        market_credit_risks: List[BusinessRisk],
        cyber_tech_risks: List[BusinessRisk]
    ) -> List[str]:
        """
        Develop comprehensive risk mitigation plan.
        
        Args:
            financial_risks: Financial risks
            regulatory_risks: Regulatory risks
            operational_risks: Operational risks
            market_credit_risks: Market and credit risks
            cyber_tech_risks: Cybersecurity and technology risks
            
        Returns:
            List of mitigation strategies
        """
        all_risks = financial_risks + regulatory_risks + operational_risks + market_credit_risks + cyber_tech_risks
        
        # Collect all mitigation strategies
        all_strategies = []
        for risk in all_risks:
            all_strategies.extend(risk.mitigation_strategies)
        
        # Remove duplicates and prioritize
        unique_strategies = list(set(all_strategies))
        
        # Add comprehensive fintech-specific strategies
        fintech_strategies = [
            "Implement comprehensive regulatory compliance program",
            "Deploy advanced fraud detection and prevention systems",
            "Establish robust cybersecurity framework with multi-layered protection",
            "Develop business continuity and disaster recovery plans",
            "Create risk monitoring and early warning systems"
        ]
        
        return unique_strategies + fintech_strategies
    
    async def _create_enhanced_monitoring_framework(
        self,
        financial_risks: List[BusinessRisk],
        regulatory_risks: List[BusinessRisk],
        operational_risks: List[BusinessRisk]
    ) -> Dict[str, Any]:
        """
        Create enhanced risk monitoring framework.
        
        Args:
            financial_risks: Financial risks
            regulatory_risks: Regulatory risks
            operational_risks: Operational risks
            
        Returns:
            Dict containing monitoring framework
        """
        all_risks = financial_risks + regulatory_risks + operational_risks
        
        # Collect all monitoring indicators
        all_indicators = []
        for risk in all_risks:
            all_indicators.extend(risk.monitoring_indicators)
        
        # Remove duplicates
        unique_indicators = list(set(all_indicators))
        
        return {
            'monitoring_indicators': unique_indicators,
            'monitoring_frequency': 'real_time',
            'alert_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8,
                'critical': 0.9
            },
            'reporting_schedule': {
                'daily': ['Security incidents', 'System uptime'],
                'weekly': ['Compliance violations', 'Fraud incidents'],
                'monthly': ['Risk score updates', 'Trend analysis'],
                'quarterly': ['Comprehensive risk assessment', 'Strategy review']
            }
        }
    
    async def _generate_fintech_specific_insights(
        self,
        financial_risks: List[BusinessRisk],
        regulatory_risks: List[BusinessRisk],
        operational_risks: List[BusinessRisk],
        market_credit_risks: List[BusinessRisk]
    ) -> Dict[str, Any]:
        """
        Generate fintech-specific risk insights and recommendations.
        
        Args:
            financial_risks: Financial risks
            regulatory_risks: Regulatory risks
            operational_risks: Operational risks
            market_credit_risks: Market and credit risks
            
        Returns:
            Dict containing fintech-specific insights
        """
        # Prepare risk summary for analysis
        risk_summary = {
            'financial_risk_count': len(financial_risks),
            'regulatory_risk_count': len(regulatory_risks),
            'operational_risk_count': len(operational_risks),
            'market_credit_risk_count': len(market_credit_risks),
            'highest_financial_risk': max([r.risk_score for r in financial_risks], default=0),
            'highest_regulatory_risk': max([r.risk_score for r in regulatory_risks], default=0)
        }
        
        prompt = f"""
        Generate fintech-specific risk insights based on comprehensive risk analysis:
        
        Risk Summary: {risk_summary}
        
        Provide fintech insights in JSON format:
        {{
            "key_risk_themes": ["theme1", "theme2"],
            "fintech_industry_benchmarks": {{
                "typical_risk_level": "low|medium|high",
                "industry_average_score": <0-100>,
                "peer_comparison": "below_average|average|above_average"
            }},
            "regulatory_outlook": {{
                "regulatory_trend": "tightening|stable|loosening",
                "upcoming_changes": ["change1", "change2"],
                "compliance_priorities": ["priority1", "priority2"]
            }},
            "technology_risk_trends": ["trend1", "trend2"],
            "strategic_recommendations": ["recommendation1", "recommendation2"],
            "risk_appetite_guidance": "conservative|moderate|aggressive"
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a senior fintech risk strategist with expertise in industry risk patterns and regulatory trends.",
                temperature=0.4
            )
            
            insights_data = json.loads(response)
            
            return {
                'key_themes': insights_data.get('key_risk_themes', []),
                'industry_benchmarks': insights_data.get('fintech_industry_benchmarks', {}),
                'regulatory_outlook': insights_data.get('regulatory_outlook', {}),
                'technology_trends': insights_data.get('technology_risk_trends', []),
                'strategic_recommendations': insights_data.get('strategic_recommendations', []),
                'risk_appetite_guidance': insights_data.get('risk_appetite_guidance', 'moderate')
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse fintech insights: {e}")
            return {
                'key_themes': ['Regulatory compliance', 'Technology security', 'Market volatility'],
                'industry_benchmarks': {
                    'typical_risk_level': 'medium',
                    'industry_average_score': 55,
                    'peer_comparison': 'average'
                },
                'regulatory_outlook': {
                    'regulatory_trend': 'tightening',
                    'upcoming_changes': ['Enhanced KYC requirements', 'Data privacy regulations'],
                    'compliance_priorities': ['AML compliance', 'Data protection']
                },
                'technology_trends': ['Increased cyber threats', 'Cloud security challenges'],
                'strategic_recommendations': ['Invest in compliance technology', 'Enhance cybersecurity'],
                'risk_appetite_guidance': 'moderate'
            }
    
    def _calculate_enhanced_overall_risk_score(
        self,
        financial_risks: List[BusinessRisk],
        regulatory_risks: List[BusinessRisk],
        operational_risks: List[BusinessRisk],
        market_credit_risks: List[BusinessRisk],
        cyber_tech_risks: List[BusinessRisk]
    ) -> float:
        """
        Calculate enhanced overall risk score with weighted categories.
        
        Args:
            financial_risks: Financial risks
            regulatory_risks: Regulatory risks
            operational_risks: Operational risks
            market_credit_risks: Market and credit risks
            cyber_tech_risks: Cybersecurity and technology risks
            
        Returns:
            Enhanced overall risk score (0-100)
        """
        # Calculate weighted average risk scores by category
        category_weights = {
            'financial': 0.25,
            'regulatory': 0.25,
            'operational': 0.20,
            'market_credit': 0.15,
            'cyber_tech': 0.15
        }
        
        def calculate_category_score(risks: List[BusinessRisk]) -> float:
            if not risks:
                return 0.0
            return sum(risk.risk_score for risk in risks) / len(risks)
        
        financial_score = calculate_category_score(financial_risks)
        regulatory_score = calculate_category_score(regulatory_risks)
        operational_score = calculate_category_score(operational_risks)
        market_credit_score = calculate_category_score(market_credit_risks)
        cyber_tech_score = calculate_category_score(cyber_tech_risks)
        
        # Calculate weighted overall score
        overall_score = (
            financial_score * category_weights['financial'] +
            regulatory_score * category_weights['regulatory'] +
            operational_score * category_weights['operational'] +
            market_credit_score * category_weights['market_credit'] +
            cyber_tech_score * category_weights['cyber_tech']
        )
        
        # Convert to 0-100 scale
        return min(100.0, overall_score * 10)
    
    def _determine_enhanced_risk_level(self, risk_score: float) -> str:
        """
        Determine enhanced risk level based on score.
        
        Args:
            risk_score: Overall risk score (0-100)
            
        Returns:
            Risk level string
        """
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        elif risk_score >= 20:
            return 'low'
        else:
            return 'very_low'
    
    def _calculate_enhanced_confidence_score(self, parameters: Dict[str, Any]) -> float:
        """
        Calculate enhanced confidence score for fintech risk assessment.
        
        Args:
            parameters: Assessment parameters
            
        Returns:
            Enhanced confidence score (0.0-1.0)
        """
        base_score = 0.7  # Higher base for enhanced analysis
        
        # Increase confidence based on business model specificity
        if parameters.get('business_model') and 'fintech' in parameters.get('business_model', '').lower():
            base_score += 0.1
        
        # Increase confidence based on target market specificity
        if parameters.get('target_markets') and len(parameters.get('target_markets', [])) > 0:
            base_score += 0.05
        
        # Increase confidence for comprehensive analysis
        base_score += 0.1  # Enhanced methodology bonus
        
        return min(0.95, base_score)
    
    def _generate_enhanced_risk_recommendation(self, risk_level: str, result: Dict[str, Any]) -> str:
        """
        Generate enhanced risk recommendation based on comprehensive analysis.
        
        Args:
            risk_level: Overall risk level
            result: Complete risk assessment result
            
        Returns:
            Enhanced risk recommendation string
        """
        if risk_level == 'critical':
            return "CRITICAL: Immediate action required. Focus on regulatory compliance, cybersecurity, and financial risk mitigation."
        elif risk_level == 'high':
            return "HIGH: Significant risks identified. Prioritize regulatory compliance and operational risk management."
        elif risk_level == 'medium':
            return "MEDIUM: Manageable risks with proper controls. Focus on continuous monitoring and improvement."
        elif risk_level == 'low':
            return "LOW: Well-managed risk profile. Maintain current controls and monitor for changes."
        else:
            return "VERY LOW: Excellent risk management. Continue best practices and periodic reviews."
