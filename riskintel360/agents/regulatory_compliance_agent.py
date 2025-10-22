"""
Regulatory Compliance Agent for RiskIntel360 Platform
Specialized agent for regulatory monitoring, compliance assessment, and remediation planning.
"""

import asyncio
import logging
import json
import aiohttp
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import warnings

from .base_agent import BaseAgent, AgentConfig
from ..models.agent_models import MessageType, Priority, AgentType

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


@dataclass
class RegulatoryComplianceAgentConfig(AgentConfig):
    """Configuration specific to Regulatory Compliance Agent"""
    regulatory_sources: List[str] = None
    jurisdiction: str = "US"
    compliance_frameworks: List[str] = None
    monitoring_interval_hours: int = 24
    alert_threshold: float = 0.8
    
    def __post_init__(self):
        if self.agent_type != AgentType.REGULATORY_COMPLIANCE:
            raise ValueError(f"Invalid agent type for RegulatoryComplianceAgentConfig: {self.agent_type}")
        
        # Set default regulatory sources if not provided
        if self.regulatory_sources is None:
            self.regulatory_sources = ["SEC", "FINRA", "CFPB"]
        
        # Set default compliance frameworks if not provided
        if self.compliance_frameworks is None:
            self.compliance_frameworks = ["SOX", "GDPR", "PCI-DSS", "CCPA"]


@dataclass
class RegulatoryDataSource:
    """Configuration for regulatory data sources"""
    name: str
    base_url: str
    api_endpoint: Optional[str] = None
    rate_limit: int = 10  # requests per minute
    timeout: int = 30
    requires_auth: bool = False


@dataclass
class ComplianceAssessment:
    """Compliance assessment result model"""
    regulation_id: str
    regulation_name: str
    compliance_status: str  # "compliant", "non_compliant", "requires_review", "unknown"
    risk_level: str  # "low", "medium", "high", "critical"
    requirements: List[str]
    gaps: List[str]
    remediation_plan: Dict[str, Any]
    confidence_score: float
    ai_reasoning: str
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'regulation_id': self.regulation_id,
            'regulation_name': self.regulation_name,
            'compliance_status': self.compliance_status,
            'risk_level': self.risk_level,
            'requirements': self.requirements,
            'gaps': self.gaps,
            'remediation_plan': self.remediation_plan,
            'confidence_score': self.confidence_score,
            'ai_reasoning': self.ai_reasoning,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class RegulatoryUpdate:
    """Regulatory update notification model"""
    update_id: str
    source: str
    title: str
    description: str
    effective_date: datetime
    impact_level: str  # "low", "medium", "high", "critical"
    affected_areas: List[str]
    action_required: bool
    deadline: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'update_id': self.update_id,
            'source': self.source,
            'title': self.title,
            'description': self.description,
            'effective_date': self.effective_date.isoformat(),
            'impact_level': self.impact_level,
            'affected_areas': self.affected_areas,
            'action_required': self.action_required,
            'deadline': self.deadline.isoformat() if self.deadline else None
        }


@dataclass
class RemediationPlan:
    """Compliance remediation plan"""
    plan_id: str
    regulation_id: str
    priority: str  # "low", "medium", "high", "critical"
    estimated_cost: float
    implementation_timeline_months: int
    required_actions: List[str]
    responsible_parties: List[str]
    success_metrics: List[str]
    risk_mitigation: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'plan_id': self.plan_id,
            'regulation_id': self.regulation_id,
            'priority': self.priority,
            'estimated_cost': self.estimated_cost,
            'implementation_timeline_months': self.implementation_timeline_months,
            'required_actions': self.required_actions,
            'responsible_parties': self.responsible_parties,
            'success_metrics': self.success_metrics,
            'risk_mitigation': self.risk_mitigation
        }


class RegulatoryComplianceAgent(BaseAgent):
    """
    Regulatory Compliance Agent using Amazon Bedrock Nova (Claude-3) for regulatory analysis.
    
    Capabilities:
    - Regulatory change monitoring from public sources (SEC, FINRA, CFPB)
    - Compliance gap analysis and assessment
    - Automated remediation plan generation
    - Real-time regulatory alert processing
    - Public-data-first approach for cost-effective compliance monitoring
    """
    
    def __init__(self, config: RegulatoryComplianceAgentConfig):
        """Initialize Regulatory Compliance Agent"""
        super().__init__(config)
        
        # Ensure this is a regulatory compliance agent
        if config.agent_type != AgentType.REGULATORY_COMPLIANCE:
            raise ValueError(f"Invalid agent type for RegulatoryComplianceAgent: {config.agent_type}")
        
        # Store configuration
        self.regulatory_sources = config.regulatory_sources
        self.jurisdiction = config.jurisdiction
        self.compliance_frameworks = config.compliance_frameworks
        self.monitoring_interval_hours = config.monitoring_interval_hours
        self.alert_threshold = config.alert_threshold
        
        # Configure public regulatory data sources
        self.data_sources = {
            'sec': RegulatoryDataSource(
                name='SEC EDGAR Database',
                base_url='https://www.sec.gov',
                api_endpoint='/edgar/searchedgar/companysearch.html',
                rate_limit=10,
                requires_auth=False
            ),
            'finra': RegulatoryDataSource(
                name='FINRA Regulatory Notices',
                base_url='https://www.finra.org',
                api_endpoint='/rules-guidance/notices',
                rate_limit=5,
                requires_auth=False
            ),
            'cfpb': RegulatoryDataSource(
                name='CFPB Compliance Resources',
                base_url='https://www.consumerfinance.gov',
                api_endpoint='/compliance',
                rate_limit=10,
                requires_auth=False
            ),
            'federal_register': RegulatoryDataSource(
                name='Federal Register',
                base_url='https://www.federalregister.gov',
                api_endpoint='/api/v1/documents',
                rate_limit=15,
                requires_auth=False
            )
        }
        
        # Initialize HTTP session for API calls
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Cache for regulatory data
        self.data_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(hours=6)  # 6-hour cache for regulatory data
        
        # Compliance assessment parameters
        self.compliance_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 1.0
        }
        
        self.logger.info("🏛️ Regulatory Compliance Agent initialized with public data sources")
    
    async def start(self) -> None:
        """Start the agent and initialize HTTP session"""
        await super().start()
        
        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=30)
        self.http_session = aiohttp.ClientSession(timeout=timeout)
        
        # Start regulatory monitoring task
        asyncio.create_task(self._start_regulatory_monitoring())
        
        self.logger.info("🌐 HTTP session initialized for regulatory data APIs")
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources"""
        if self.http_session:
            await self.http_session.close()
            self.logger.info("🔌 HTTP session closed")
        
        await super().stop()
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this agent supports"""
        return [
            "regulatory_analysis",
            "compliance_assessment",
            "risk_evaluation",
            "remediation_planning",
            "regulatory_monitoring",
            "gap_analysis",
            "public_data_integration"
        ]
    
    async def execute_task(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a regulatory compliance task.
        
        Args:
            task_type: Type of task to execute
            parameters: Task parameters
            
        Returns:
            Dict containing task results
        """
        self.current_task = task_type
        self.update_progress(0.1)
        
        try:
            if task_type == "regulatory_analysis":
                return await self._perform_regulatory_analysis(parameters)
            elif task_type == "compliance_assessment":
                return await self._assess_compliance(parameters)
            elif task_type == "gap_analysis":
                return await self._perform_gap_analysis(parameters)
            elif task_type == "remediation_planning":
                return await self._generate_remediation_plan(parameters)
            elif task_type == "regulatory_monitoring":
                return await self._monitor_regulatory_changes(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            self.state.error_count += 1
            self.logger.error(f"❌ Task execution failed: {e}")
            raise
        finally:
            self.current_task = None
    
    async def _perform_regulatory_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive regulatory analysis using public data sources.
        
        Args:
            parameters: Analysis parameters including business type, jurisdiction, etc.
            
        Returns:
            Dict containing regulatory analysis results
        """
        business_type = parameters.get('business_type', 'fintech')
        jurisdiction = parameters.get('jurisdiction', self.jurisdiction)
        analysis_scope = parameters.get('analysis_scope', ['regulatory', 'compliance'])
        
        self.logger.info(f"🔍 Performing regulatory analysis for {business_type} in {jurisdiction}")
        
        # Step 1: Fetch regulatory data from public sources
        self.update_progress(0.2)
        regulatory_data = await self._fetch_regulatory_data(business_type, jurisdiction)
        
        # Step 2: Analyze regulatory requirements using LLM
        self.update_progress(0.5)
        analysis_result = await self._analyze_regulatory_requirements(
            business_type, jurisdiction, regulatory_data
        )
        
        # Step 3: Generate compliance recommendations
        self.update_progress(0.8)
        recommendations = await self._generate_compliance_recommendations(
            analysis_result, parameters
        )
        
        self.update_progress(1.0)
        
        return {
            'analysis_result': analysis_result,
            'recommendations': recommendations,
            'data_sources_used': list(self.data_cache.keys()) if self.data_cache else ['public_sources'],
            'confidence_score': analysis_result.get('confidence_score', 0.8),
            'metadata': {
                'agent_id': self.agent_id,
                'analysis_timestamp': datetime.now(UTC).isoformat(),
                'jurisdiction': jurisdiction,
                'business_type': business_type
            }
        }
    
    async def _assess_compliance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess compliance status against regulatory requirements.
        
        Args:
            parameters: Compliance assessment parameters
            
        Returns:
            Dict containing compliance assessment results
        """
        business_type = parameters.get('business_type', 'fintech')
        current_practices = parameters.get('current_practices', [])
        regulations_to_check = parameters.get('regulations', self.compliance_frameworks)
        
        self.logger.info(f"📋 Assessing compliance for {business_type} against {len(regulations_to_check)} regulations")
        
        compliance_assessments = []
        
        for regulation in regulations_to_check:
            self.update_progress(0.2 + (0.6 * len(compliance_assessments) / len(regulations_to_check)))
            
            # Fetch regulation details from public sources
            regulation_data = await self._fetch_regulation_details(regulation)
            
            # Perform compliance assessment using LLM
            assessment = await self._perform_single_compliance_assessment(
                regulation, regulation_data, current_practices, business_type
            )
            
            compliance_assessments.append(assessment)
        
        # Calculate overall compliance score
        overall_score = self._calculate_overall_compliance_score(compliance_assessments)
        risk_level = self._determine_compliance_risk_level(overall_score)
        
        self.update_progress(1.0)
        
        return {
            'overall_compliance_score': overall_score,
            'risk_level': risk_level,
            'assessments': [assessment.to_dict() for assessment in compliance_assessments],
            'summary': {
                'total_regulations_checked': len(regulations_to_check),
                'compliant_count': len([a for a in compliance_assessments if a.compliance_status == 'compliant']),
                'non_compliant_count': len([a for a in compliance_assessments if a.compliance_status == 'non_compliant']),
                'requires_review_count': len([a for a in compliance_assessments if a.compliance_status == 'requires_review'])
            },
            'metadata': {
                'agent_id': self.agent_id,
                'assessment_timestamp': datetime.now(UTC).isoformat(),
                'business_type': business_type
            }
        }
    
    async def _perform_gap_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform compliance gap analysis.
        
        Args:
            parameters: Gap analysis parameters
            
        Returns:
            Dict containing gap analysis results
        """
        current_state = parameters.get('current_state', {})
        target_regulations = parameters.get('target_regulations', self.compliance_frameworks)
        business_type = parameters.get('business_type', 'fintech')
        
        self.logger.info(f"🔍 Performing gap analysis for {business_type}")
        
        # First assess current compliance
        compliance_result = await self._assess_compliance({
            'business_type': business_type,
            'current_practices': current_state.get('practices', []),
            'regulations': target_regulations
        })
        
        # Identify gaps using LLM analysis
        gaps = await self._identify_compliance_gaps(compliance_result, current_state)
        
        # Prioritize gaps by risk and impact
        prioritized_gaps = await self._prioritize_compliance_gaps(gaps)
        
        return {
            'compliance_assessment': compliance_result,
            'identified_gaps': gaps,
            'prioritized_gaps': prioritized_gaps,
            'gap_summary': {
                'total_gaps': len(gaps),
                'critical_gaps': len([g for g in gaps if g.get('priority') == 'critical']),
                'high_priority_gaps': len([g for g in gaps if g.get('priority') == 'high']),
                'estimated_remediation_cost': sum(g.get('estimated_cost', 0) for g in gaps)
            },
            'metadata': {
                'agent_id': self.agent_id,
                'analysis_timestamp': datetime.now(UTC).isoformat(),
                'business_type': business_type
            }
        }
    
    async def _generate_remediation_plan(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate compliance remediation plan.
        
        Args:
            parameters: Remediation planning parameters
            
        Returns:
            Dict containing remediation plan
        """
        gaps = parameters.get('gaps', [])
        budget_constraints = parameters.get('budget', {})
        timeline_constraints = parameters.get('timeline_months', 12)
        business_type = parameters.get('business_type', 'fintech')
        
        self.logger.info(f"📋 Generating remediation plan for {len(gaps)} compliance gaps")
        
        # Generate remediation plan using LLM
        remediation_plan = await self._create_remediation_plan(
            gaps, budget_constraints, timeline_constraints, business_type
        )
        
        return {
            'remediation_plan': remediation_plan,
            'implementation_roadmap': remediation_plan.get('roadmap', []),
            'cost_analysis': remediation_plan.get('cost_analysis', {}),
            'timeline': remediation_plan.get('timeline', {}),
            'success_metrics': remediation_plan.get('success_metrics', []),
            'metadata': {
                'agent_id': self.agent_id,
                'plan_generated': datetime.now(UTC).isoformat(),
                'business_type': business_type,
                'total_gaps_addressed': len(gaps)
            }
        }
    
    async def _monitor_regulatory_changes(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor regulatory changes from public sources.
        
        Args:
            parameters: Monitoring parameters
            
        Returns:
            Dict containing monitoring results
        """
        sources_to_monitor = parameters.get('sources', list(self.data_sources.keys()))
        lookback_days = parameters.get('lookback_days', 30)
        
        self.logger.info(f"👀 Monitoring regulatory changes from {len(sources_to_monitor)} sources")
        
        regulatory_updates = []
        
        for source in sources_to_monitor:
            try:
                updates = await self._fetch_recent_regulatory_updates(source, lookback_days)
                regulatory_updates.extend(updates)
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to fetch updates from {source}: {e}")
        
        # Analyze impact of updates using LLM
        impact_analysis = await self._analyze_regulatory_impact(regulatory_updates)
        
        return {
            'regulatory_updates': [update.to_dict() for update in regulatory_updates],
            'impact_analysis': impact_analysis,
            'summary': {
                'total_updates': len(regulatory_updates),
                'high_impact_updates': len([u for u in regulatory_updates if u.impact_level in ['high', 'critical']]),
                'action_required_updates': len([u for u in regulatory_updates if u.action_required])
            },
            'metadata': {
                'agent_id': self.agent_id,
                'monitoring_timestamp': datetime.now(UTC).isoformat(),
                'sources_monitored': sources_to_monitor,
                'lookback_days': lookback_days
            }
        }
    
    async def _fetch_regulatory_data(self, business_type: str, jurisdiction: str) -> Dict[str, Any]:
        """
        Fetch regulatory data from public sources.
        
        Args:
            business_type: Type of business
            jurisdiction: Regulatory jurisdiction
            
        Returns:
            Dict containing regulatory data
        """
        # Check cache first
        cache_key = f"regulatory_data_{business_type}_{jurisdiction}"
        if cache_key in self.data_cache:
            cached_data, timestamp = self.data_cache[cache_key]
            if datetime.now(UTC) - timestamp < self.cache_ttl:
                self.logger.info("📦 Using cached regulatory data")
                return cached_data
        
        regulatory_data = {}
        
        # Fetch from each configured source
        for source_name, source_config in self.data_sources.items():
            try:
                if source_name == 'sec':
                    data = await self._fetch_sec_data(business_type)
                elif source_name == 'finra':
                    data = await self._fetch_finra_data(business_type)
                elif source_name == 'cfpb':
                    data = await self._fetch_cfpb_data(business_type)
                elif source_name == 'federal_register':
                    data = await self._fetch_federal_register_data(business_type)
                else:
                    data = {}
                
                regulatory_data[source_name] = data
                
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to fetch data from {source_name}: {e}")
                regulatory_data[source_name] = {}
        
        # Cache the results
        self.data_cache[cache_key] = (regulatory_data, datetime.now(UTC))
        
        return regulatory_data
    
    async def _analyze_regulatory_requirements(
        self, business_type: str, jurisdiction: str, regulatory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze regulatory requirements using LLM.
        
        Args:
            business_type: Type of business
            jurisdiction: Regulatory jurisdiction
            regulatory_data: Fetched regulatory data
            
        Returns:
            Dict containing analysis results
        """
        prompt = f"""
        As a regulatory compliance expert, analyze the regulatory requirements for a {business_type} business operating in {jurisdiction}.
        
        Available Regulatory Data:
        {json.dumps(regulatory_data, indent=2, default=str)}
        
        Provide comprehensive regulatory analysis in JSON format:
        {{
            "applicable_regulations": [
                {{
                    "regulation_name": "Name of regulation",
                    "regulatory_body": "Issuing authority",
                    "applicability": "high|medium|low",
                    "key_requirements": ["requirement1", "requirement2"],
                    "compliance_deadline": "YYYY-MM-DD or ongoing",
                    "penalties_for_non_compliance": "Description of penalties"
                }}
            ],
            "compliance_priorities": [
                {{
                    "priority": "critical|high|medium|low",
                    "regulation": "Regulation name",
                    "rationale": "Why this is prioritized",
                    "immediate_actions": ["action1", "action2"]
                }}
            ],
            "risk_assessment": {{
                "overall_risk_level": "low|medium|high|critical",
                "key_risk_factors": ["factor1", "factor2"],
                "potential_impact": "Description of potential impact"
            }},
            "confidence_score": <0.0-1.0>
        }}
        
        Focus on fintech-specific regulations and public data sources.
        """
        
        system_prompt = """You are a senior regulatory compliance expert with 15+ years of experience in fintech regulations. 
        Provide thorough, accurate regulatory analysis based on current requirements from SEC, FINRA, CFPB, and other regulatory bodies. 
        Focus on actionable insights and practical compliance guidance."""
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2  # Low temperature for regulatory accuracy
            )
            
            analysis_result = json.loads(response)
            return analysis_result
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse LLM regulatory analysis: {e}")
            # Return default analysis
            return {
                'applicable_regulations': [
                    {
                        'regulation_name': 'General Business Compliance',
                        'regulatory_body': 'Multiple agencies',
                        'applicability': 'high',
                        'key_requirements': ['Business registration', 'Tax compliance', 'Data protection'],
                        'compliance_deadline': 'ongoing',
                        'penalties_for_non_compliance': 'Fines and business closure risk'
                    }
                ],
                'compliance_priorities': [
                    {
                        'priority': 'high',
                        'regulation': 'General Business Compliance',
                        'rationale': 'Fundamental business requirements',
                        'immediate_actions': ['Review current practices', 'Identify gaps', 'Create action plan']
                    }
                ],
                'risk_assessment': {
                    'overall_risk_level': 'medium',
                    'key_risk_factors': ['Regulatory changes', 'Compliance gaps', 'Enforcement actions'],
                    'potential_impact': 'Fines, penalties, and operational disruption'
                },
                'confidence_score': 0.6
            }
    
    async def _generate_compliance_recommendations(
        self, analysis_result: Dict[str, Any], parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate compliance recommendations based on analysis.
        
        Args:
            analysis_result: Regulatory analysis results
            parameters: Additional parameters
            
        Returns:
            List of compliance recommendations
        """
        prompt = f"""
        Based on the regulatory analysis, provide specific compliance recommendations:
        
        Analysis Results:
        {json.dumps(analysis_result, indent=2, default=str)}
        
        Business Context:
        {json.dumps(parameters, indent=2, default=str)}
        
        Provide actionable recommendations in JSON format:
        {{
            "recommendations": [
                {{
                    "category": "immediate|short_term|long_term",
                    "priority": "critical|high|medium|low",
                    "title": "Recommendation title",
                    "description": "Detailed description",
                    "action_items": ["action1", "action2"],
                    "estimated_cost": <amount>,
                    "timeline_months": <months>,
                    "success_metrics": ["metric1", "metric2"],
                    "regulatory_basis": "Which regulation this addresses"
                }}
            ]
        }}
        
        Focus on cost-effective solutions using public data sources.
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a compliance consultant focused on practical, cost-effective solutions for fintech companies.",
                temperature=0.3
            )
            
            recommendations_data = json.loads(response)
            return recommendations_data.get('recommendations', [])
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse compliance recommendations: {e}")
            return [
                {
                    'category': 'immediate',
                    'priority': 'high',
                    'title': 'Conduct Compliance Assessment',
                    'description': 'Perform comprehensive review of current compliance status',
                    'action_items': ['Review current practices', 'Identify regulatory requirements', 'Document gaps'],
                    'estimated_cost': 25000,
                    'timeline_months': 2,
                    'success_metrics': ['Compliance assessment completed', 'Gap analysis documented'],
                    'regulatory_basis': 'General regulatory compliance'
                }
            ]
    
    async def _perform_single_compliance_assessment(
        self, regulation: str, regulation_data: Dict[str, Any], 
        current_practices: List[str], business_type: str
    ) -> ComplianceAssessment:
        """
        Perform compliance assessment for a single regulation.
        
        Args:
            regulation: Regulation name
            regulation_data: Regulation details
            current_practices: Current business practices
            business_type: Type of business
            
        Returns:
            ComplianceAssessment object
        """
        prompt = f"""
        Assess compliance with {regulation} for a {business_type} business.
        
        Regulation Details:
        {json.dumps(regulation_data, indent=2, default=str)}
        
        Current Business Practices:
        {json.dumps(current_practices, indent=2, default=str)}
        
        Provide compliance assessment in JSON format:
        {{
            "compliance_status": "compliant|non_compliant|requires_review|unknown",
            "risk_level": "low|medium|high|critical",
            "requirements": ["requirement1", "requirement2"],
            "gaps": ["gap1", "gap2"],
            "remediation_plan": {{
                "priority_actions": ["action1", "action2"],
                "estimated_cost": <amount>,
                "timeline_months": <months>
            }},
            "confidence_score": <0.0-1.0>,
            "reasoning": "Detailed explanation of assessment"
        }}
        """
        
        try:
            response = await self.invoke_llm(
                prompt=prompt,
                system_prompt="You are a compliance auditor with expertise in fintech regulations.",
                temperature=0.1  # Very low temperature for compliance accuracy
            )
            
            assessment_data = json.loads(response)
            
            return ComplianceAssessment(
                regulation_id=regulation.lower().replace(' ', '_'),
                regulation_name=regulation,
                compliance_status=assessment_data.get('compliance_status', 'unknown'),
                risk_level=assessment_data.get('risk_level', 'medium'),
                requirements=assessment_data.get('requirements', []),
                gaps=assessment_data.get('gaps', []),
                remediation_plan=assessment_data.get('remediation_plan', {}),
                confidence_score=assessment_data.get('confidence_score', 0.7),
                ai_reasoning=assessment_data.get('reasoning', 'Compliance assessment completed'),
                last_updated=datetime.now(UTC)
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"⚠️ Failed to parse compliance assessment for {regulation}: {e}")
            return ComplianceAssessment(
                regulation_id=regulation.lower().replace(' ', '_'),
                regulation_name=regulation,
                compliance_status='unknown',
                risk_level='medium',
                requirements=['Review regulatory requirements'],
                gaps=['Assessment needed'],
                remediation_plan={'priority_actions': ['Conduct detailed review'], 'estimated_cost': 10000, 'timeline_months': 3},
                confidence_score=0.5,
                ai_reasoning='Unable to complete detailed assessment',
                last_updated=datetime.now(UTC)
            )
    
    # Placeholder methods for data fetching (to be implemented with actual API calls)
    async def _fetch_sec_data(self, business_type: str) -> Dict[str, Any]:
        """Fetch SEC regulatory data"""
        # Placeholder implementation - would integrate with SEC EDGAR API
        return {'source': 'SEC', 'data': f'SEC regulations for {business_type}'}
    
    async def _fetch_finra_data(self, business_type: str) -> Dict[str, Any]:
        """Fetch FINRA regulatory data"""
        # Placeholder implementation - would integrate with FINRA API
        return {'source': 'FINRA', 'data': f'FINRA regulations for {business_type}'}
    
    async def _fetch_cfpb_data(self, business_type: str) -> Dict[str, Any]:
        """Fetch CFPB regulatory data"""
        # Placeholder implementation - would integrate with CFPB API
        return {'source': 'CFPB', 'data': f'CFPB regulations for {business_type}'}
    
    async def _fetch_federal_register_data(self, business_type: str) -> Dict[str, Any]:
        """Fetch Federal Register data"""
        # Placeholder implementation - would integrate with Federal Register API
        return {'source': 'Federal Register', 'data': f'Federal regulations for {business_type}'}
    
    async def _fetch_regulation_details(self, regulation: str) -> Dict[str, Any]:
        """Fetch details for a specific regulation"""
        # Placeholder implementation
        return {'regulation': regulation, 'details': 'Regulation details from public sources'}
    
    async def _fetch_recent_regulatory_updates(self, source: str, lookback_days: int) -> List[RegulatoryUpdate]:
        """Fetch recent regulatory updates from a source"""
        # Placeholder implementation
        return []
    
    # Helper methods
    def _calculate_overall_compliance_score(self, assessments: List[ComplianceAssessment]) -> float:
        """Calculate overall compliance score"""
        if not assessments:
            return 0.0
        
        compliant_count = len([a for a in assessments if a.compliance_status == 'compliant'])
        return compliant_count / len(assessments)
    
    def _determine_compliance_risk_level(self, score: float) -> str:
        """Determine risk level based on compliance score"""
        if score >= 0.8:
            return 'low'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'high'
        else:
            return 'critical'
    
    async def _identify_compliance_gaps(self, compliance_result: Dict[str, Any], current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify compliance gaps"""
        # Placeholder implementation
        return []
    
    async def _prioritize_compliance_gaps(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize compliance gaps by risk and impact"""
        # Placeholder implementation
        return gaps
    
    async def _create_remediation_plan(self, gaps: List[Dict[str, Any]], budget: Dict[str, Any], 
                                     timeline_months: int, business_type: str) -> Dict[str, Any]:
        """Create comprehensive remediation plan"""
        # Placeholder implementation
        return {
            'roadmap': [],
            'cost_analysis': {},
            'timeline': {},
            'success_metrics': []
        }
    
    async def _analyze_regulatory_impact(self, updates: List[RegulatoryUpdate]) -> Dict[str, Any]:
        """Analyze impact of regulatory updates"""
        # Placeholder implementation
        return {'impact_summary': 'Analysis of regulatory updates'}
    
    async def _start_regulatory_monitoring(self) -> None:
        """Start background regulatory monitoring task"""
        self.logger.info("🔄 Starting regulatory monitoring background task")
        # Placeholder for background monitoring implementation