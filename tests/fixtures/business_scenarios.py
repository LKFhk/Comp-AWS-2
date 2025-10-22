"""
Realistic Business Scenarios for Testing

This module provides comprehensive test data representing real-world business validation
scenarios that demonstrate the RiskIntel360 platform's capabilities across different
industries, market conditions, and business stages.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

from riskintel360.models import ValidationRequest, Priority


class IndustryType(Enum):
    """Industry classification for business scenarios"""
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    CONSULTING = "consulting"


class BusinessStage(Enum):
    """Business development stage"""
    STARTUP = "startup"
    GROWTH = "growth"
    EXPANSION = "expansion"
    MATURE = "mature"


class MarketSize(Enum):
    """Target market size classification"""
    NICHE = "niche"          # <$100M
    MEDIUM = "medium"        # $100M-$1B
    LARGE = "large"          # $1B-$10B
    MASSIVE = "massive"      # >$10B


@dataclass
class ExpectedResults:
    """Expected validation results for testing"""
    overall_score_range: tuple[float, float]  # Min, max expected score
    confidence_score_min: float
    market_size_estimate: str
    key_risks: List[str]
    success_factors: List[str]
    competitive_intensity: str  # low, medium, high
    financial_viability: str    # poor, fair, good, excellent
    recommendation: str         # proceed, caution, stop


@dataclass
class BusinessScenario:
    """Comprehensive business scenario for testing"""
    # Basic Information
    scenario_id: str
    name: str
    description: str
    industry: IndustryType
    business_stage: BusinessStage
    market_size: MarketSize
    
    # Validation Request Data
    business_concept: str
    target_market: str
    analysis_scope: List[str]
    priority: Priority
    custom_parameters: Dict[str, Any]
    
    # Expected Results
    expected_results: ExpectedResults
    
    # Test Configuration
    test_tags: List[str] = field(default_factory=list)
    complexity_level: str = "medium"  # simple, medium, complex
    execution_time_estimate: int = 120  # minutes
    
    def to_validation_request(self, user_id: str = "test-user") -> ValidationRequest:
        """Convert scenario to ValidationRequest for testing"""
        return ValidationRequest(
            id=f"test-{self.scenario_id}",
            user_id=user_id,
            business_concept=self.business_concept,
            target_market=self.target_market,
            analysis_scope=self.analysis_scope,
            priority=self.priority,
            custom_parameters=self.custom_parameters,
            created_at=datetime.now(timezone.utc)
        )


# =============================================================================
# STARTUP SCENARIOS
# =============================================================================

SAAS_PRODUCTIVITY_STARTUP = BusinessScenario(
    scenario_id="saas_001",
    name="SaaS Productivity Tool for Remote Teams",
    description="AI-powered project management and collaboration platform targeting remote-first companies",
    industry=IndustryType.SAAS,
    business_stage=BusinessStage.STARTUP,
    market_size=MarketSize.LARGE,
    
    business_concept="AI-powered project management tool that automatically tracks team productivity, predicts project delays, and optimizes resource allocation for remote teams",
    target_market="Small to medium businesses (10-500 employees) with distributed remote teams, particularly in tech, consulting, and creative industries",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.HIGH,
    custom_parameters={
        "budget_range": "500000-2000000",
        "timeline": "12-months",
        "team_size": "5-15",
        "target_revenue_year_1": "1000000",
        "key_features": ["AI productivity tracking", "Predictive analytics", "Resource optimization"],
        "pricing_model": "subscription",
        "target_price_per_user": "25-50"
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(70.0, 85.0),
        confidence_score_min=0.75,
        market_size_estimate="$2.5B - $5.0B",
        key_risks=[
            "High market competition from established players",
            "Customer acquisition cost challenges",
            "Privacy concerns with productivity tracking"
        ],
        success_factors=[
            "Strong AI differentiation",
            "Remote work trend acceleration",
            "Focus on SMB market segment"
        ],
        competitive_intensity="high",
        financial_viability="good",
        recommendation="proceed"
    ),
    
    test_tags=["startup", "saas", "high_competition", "ai_powered"],
    complexity_level="medium",
    execution_time_estimate=90
)

FINTECH_NEOBANK_STARTUP = BusinessScenario(
    scenario_id="fintech_001",
    name="Neobank for Gig Economy Workers",
    description="Digital banking platform designed specifically for freelancers, contractors, and gig workers",
    industry=IndustryType.FINTECH,
    business_stage=BusinessStage.STARTUP,
    market_size=MarketSize.LARGE,
    
    business_concept="Digital-first banking platform offering specialized financial services for gig economy workers including income smoothing, tax optimization, and business expense management",
    target_market="Freelancers, independent contractors, and gig workers in the US market, particularly those earning $30K-$150K annually",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.HIGH,
    custom_parameters={
        "budget_range": "10000000-50000000",
        "timeline": "24-months",
        "regulatory_requirements": ["Banking license", "FDIC insurance", "KYC/AML compliance"],
        "target_customers": "100000",
        "revenue_streams": ["Interchange fees", "Premium subscriptions", "Lending products"],
        "key_partnerships": ["Banking sponsor", "Payment processors", "Tax software"]
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(60.0, 75.0),
        confidence_score_min=0.70,
        market_size_estimate="$8.0B - $15.0B",
        key_risks=[
            "Heavy regulatory requirements and compliance costs",
            "High customer acquisition costs in competitive market",
            "Banking partnership dependencies",
            "Economic downturn impact on gig economy"
        ],
        success_factors=[
            "Growing gig economy market",
            "Underserved customer segment",
            "Specialized product-market fit"
        ],
        competitive_intensity="high",
        financial_viability="fair",
        recommendation="caution"
    ),
    
    test_tags=["startup", "fintech", "regulated", "high_risk"],
    complexity_level="complex",
    execution_time_estimate=150
)

HEALTHTECH_TELEMEDICINE_STARTUP = BusinessScenario(
    scenario_id="healthtech_001",
    name="Rural Telemedicine Platform",
    description="Telemedicine platform specifically designed for rural and underserved communities",
    industry=IndustryType.HEALTHTECH,
    business_stage=BusinessStage.STARTUP,
    market_size=MarketSize.MEDIUM,
    
    business_concept="Comprehensive telemedicine platform offering primary care, mental health, and specialist consultations to rural communities with limited healthcare access, including mobile health units integration",
    target_market="Rural communities in the US with populations under 50,000, focusing on areas with limited healthcare infrastructure",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.MEDIUM,
    custom_parameters={
        "budget_range": "5000000-15000000",
        "timeline": "18-months",
        "regulatory_requirements": ["HIPAA compliance", "State medical licensing", "FDA approvals"],
        "target_markets": ["Rural US", "Underserved urban areas"],
        "key_partnerships": ["Rural hospitals", "Mobile health units", "Insurance providers"],
        "technology_requirements": ["Low-bandwidth optimization", "Mobile-first design"]
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(75.0, 90.0),
        confidence_score_min=0.80,
        market_size_estimate="$1.2B - $3.0B",
        key_risks=[
            "Regulatory complexity across multiple states",
            "Reimbursement challenges with insurance providers",
            "Technology adoption barriers in rural communities",
            "Provider network development challenges"
        ],
        success_factors=[
            "Clear market need and underserved population",
            "Government support for rural healthcare",
            "Post-COVID telemedicine adoption",
            "Social impact potential"
        ],
        competitive_intensity="medium",
        financial_viability="good",
        recommendation="proceed"
    ),
    
    test_tags=["startup", "healthtech", "social_impact", "regulated"],
    complexity_level="complex",
    execution_time_estimate=120
)

# =============================================================================
# GROWTH STAGE SCENARIOS
# =============================================================================

ECOMMERCE_MARKETPLACE_GROWTH = BusinessScenario(
    scenario_id="ecommerce_001",
    name="Sustainable Products Marketplace Expansion",
    description="Existing sustainable products marketplace expanding to B2B segment",
    industry=IndustryType.ECOMMERCE,
    business_stage=BusinessStage.GROWTH,
    market_size=MarketSize.LARGE,
    
    business_concept="Expansion of successful B2C sustainable products marketplace into B2B segment, targeting corporate procurement for office supplies, employee gifts, and corporate social responsibility initiatives",
    target_market="Mid-market and enterprise companies (500+ employees) with established sustainability initiatives and corporate procurement budgets",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.MEDIUM,
    custom_parameters={
        "current_revenue": "25000000",
        "budget_range": "5000000-10000000",
        "timeline": "12-months",
        "existing_customers": "150000",
        "target_b2b_customers": "5000",
        "average_b2b_order_value": "2500",
        "key_differentiators": ["Sustainability verification", "Carbon footprint tracking", "Impact reporting"]
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(80.0, 95.0),
        confidence_score_min=0.85,
        market_size_estimate="$15.0B - $25.0B",
        key_risks=[
            "Longer B2B sales cycles",
            "Different customer acquisition strategies needed",
            "Supply chain complexity for B2B volumes",
            "Competition from established B2B marketplaces"
        ],
        success_factors=[
            "Existing brand recognition in sustainability",
            "Growing corporate ESG requirements",
            "Proven marketplace technology platform",
            "Strong supplier relationships"
        ],
        competitive_intensity="medium",
        financial_viability="excellent",
        recommendation="proceed"
    ),
    
    test_tags=["growth", "ecommerce", "b2b_expansion", "sustainability"],
    complexity_level="medium",
    execution_time_estimate=100
)

EDTECH_PLATFORM_INTERNATIONAL = BusinessScenario(
    scenario_id="edtech_001",
    name="Professional Development Platform International Expansion",
    description="Successful US-based professional development platform expanding to European markets",
    industry=IndustryType.EDTECH,
    business_stage=BusinessStage.EXPANSION,
    market_size=MarketSize.LARGE,
    
    business_concept="International expansion of proven professional development and certification platform into European markets, starting with UK, Germany, and France",
    target_market="Working professionals in Europe seeking career advancement through online learning and certification programs",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.HIGH,
    custom_parameters={
        "current_revenue": "50000000",
        "budget_range": "15000000-30000000",
        "timeline": "18-months",
        "target_markets": ["United Kingdom", "Germany", "France"],
        "localization_requirements": ["Multi-language support", "Local payment methods", "Regional compliance"],
        "existing_us_customers": "500000",
        "target_european_customers": "200000"
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(70.0, 85.0),
        confidence_score_min=0.75,
        market_size_estimate="$12.0B - $20.0B",
        key_risks=[
            "Cultural and educational system differences",
            "Local competition with established market presence",
            "Regulatory compliance across multiple countries",
            "Currency fluctuation and economic uncertainty"
        ],
        success_factors=[
            "Proven product-market fit in US",
            "Strong technology platform",
            "Growing demand for online professional development",
            "Post-COVID remote learning adoption"
        ],
        competitive_intensity="medium",
        financial_viability="good",
        recommendation="proceed"
    ),
    
    test_tags=["expansion", "edtech", "international", "localization"],
    complexity_level="complex",
    execution_time_estimate=140
)

# =============================================================================
# ENTERPRISE SCENARIOS
# =============================================================================

MANUFACTURING_DIGITAL_TRANSFORMATION = BusinessScenario(
    scenario_id="manufacturing_001",
    name="Smart Factory IoT Platform",
    description="Traditional manufacturer developing IoT platform for smart factory operations",
    industry=IndustryType.MANUFACTURING,
    business_stage=BusinessStage.MATURE,
    market_size=MarketSize.MASSIVE,
    
    business_concept="Development of comprehensive IoT platform for smart factory operations including predictive maintenance, quality control automation, and supply chain optimization",
    target_market="Mid-size to large manufacturing companies looking to modernize operations and improve efficiency through Industry 4.0 technologies",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.HIGH,
    custom_parameters={
        "current_revenue": "500000000",
        "budget_range": "50000000-100000000",
        "timeline": "36-months",
        "target_customers": "1000",
        "average_contract_value": "500000",
        "key_technologies": ["IoT sensors", "Machine learning", "Edge computing", "Digital twins"],
        "implementation_complexity": "high"
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(65.0, 80.0),
        confidence_score_min=0.70,
        market_size_estimate="$50.0B - $100.0B",
        key_risks=[
            "High technology development costs and complexity",
            "Long sales cycles and implementation timelines",
            "Competition from established tech companies",
            "Customer resistance to digital transformation"
        ],
        success_factors=[
            "Deep manufacturing industry expertise",
            "Existing customer relationships",
            "Growing Industry 4.0 adoption",
            "Potential for high-value, long-term contracts"
        ],
        competitive_intensity="high",
        financial_viability="good",
        recommendation="proceed"
    ),
    
    test_tags=["enterprise", "manufacturing", "iot", "digital_transformation"],
    complexity_level="complex",
    execution_time_estimate=180
)

# =============================================================================
# EDGE CASE AND STRESS TEST SCENARIOS
# =============================================================================

NICHE_MARKET_SCENARIO = BusinessScenario(
    scenario_id="niche_001",
    name="Specialized Pet Tech Device",
    description="IoT device for monitoring exotic pet health in very niche market",
    industry=IndustryType.SAAS,
    business_stage=BusinessStage.STARTUP,
    market_size=MarketSize.NICHE,
    
    business_concept="IoT health monitoring device specifically designed for exotic pets (reptiles, birds, small mammals) with accompanying mobile app and veterinary integration",
    target_market="Exotic pet owners and specialized veterinary clinics in North America",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.LOW,
    custom_parameters={
        "budget_range": "100000-500000",
        "timeline": "12-months",
        "target_market_size": "2000000",  # exotic pet owners
        "device_price": "199",
        "subscription_price": "9.99",
        "veterinary_partnerships": "specialized_exotic_vets"
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(40.0, 60.0),
        confidence_score_min=0.60,
        market_size_estimate="$50M - $200M",
        key_risks=[
            "Very small addressable market",
            "High customer acquisition costs",
            "Limited scalability potential",
            "Regulatory requirements for medical devices"
        ],
        success_factors=[
            "Passionate and underserved customer base",
            "Limited direct competition",
            "High customer loyalty potential"
        ],
        competitive_intensity="low",
        financial_viability="poor",
        recommendation="stop"
    ),
    
    test_tags=["niche", "hardware", "low_viability", "edge_case"],
    complexity_level="simple",
    execution_time_estimate=60
)

HIGHLY_REGULATED_SCENARIO = BusinessScenario(
    scenario_id="regulated_001",
    name="Cryptocurrency Trading Platform for Institutions",
    description="Institutional-grade cryptocurrency trading platform with full regulatory compliance",
    industry=IndustryType.FINTECH,
    business_stage=BusinessStage.STARTUP,
    market_size=MarketSize.LARGE,
    
    business_concept="Institutional-grade cryptocurrency trading platform offering advanced trading tools, custody services, and regulatory compliance for banks, hedge funds, and asset managers",
    target_market="Institutional investors including banks, hedge funds, asset managers, and family offices looking to trade cryptocurrencies",
    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
    priority=Priority.HIGH,
    custom_parameters={
        "budget_range": "50000000-200000000",
        "timeline": "36-months",
        "regulatory_requirements": [
            "SEC registration",
            "CFTC compliance",
            "State money transmitter licenses",
            "International regulatory approvals"
        ],
        "target_aum": "10000000000",  # $10B assets under management
        "fee_structure": "0.1-0.5%",
        "security_requirements": "institutional_grade"
    },
    
    expected_results=ExpectedResults(
        overall_score_range=(45.0, 70.0),
        confidence_score_min=0.65,
        market_size_estimate="$20.0B - $50.0B",
        key_risks=[
            "Extreme regulatory uncertainty and complexity",
            "Massive compliance and legal costs",
            "Market volatility and regulatory crackdowns",
            "High competition from established players",
            "Technology security requirements"
        ],
        success_factors=[
            "Growing institutional crypto adoption",
            "High-value customer segment",
            "Potential for significant revenue per client"
        ],
        competitive_intensity="high",
        financial_viability="fair",
        recommendation="caution"
    ),
    
    test_tags=["highly_regulated", "fintech", "crypto", "high_risk"],
    complexity_level="complex",
    execution_time_estimate=200
)

# =============================================================================
# SCENARIO COLLECTIONS
# =============================================================================

ALL_SCENARIOS = [
    SAAS_PRODUCTIVITY_STARTUP,
    FINTECH_NEOBANK_STARTUP,
    HEALTHTECH_TELEMEDICINE_STARTUP,
    ECOMMERCE_MARKETPLACE_GROWTH,
    EDTECH_PLATFORM_INTERNATIONAL,
    MANUFACTURING_DIGITAL_TRANSFORMATION,
    NICHE_MARKET_SCENARIO,
    HIGHLY_REGULATED_SCENARIO
]

STARTUP_SCENARIOS = [
    SAAS_PRODUCTIVITY_STARTUP,
    FINTECH_NEOBANK_STARTUP,
    HEALTHTECH_TELEMEDICINE_STARTUP,
    NICHE_MARKET_SCENARIO,
    HIGHLY_REGULATED_SCENARIO
]

GROWTH_SCENARIOS = [
    ECOMMERCE_MARKETPLACE_GROWTH,
    EDTECH_PLATFORM_INTERNATIONAL
]

ENTERPRISE_SCENARIOS = [
    MANUFACTURING_DIGITAL_TRANSFORMATION
]

HIGH_VIABILITY_SCENARIOS = [
    SAAS_PRODUCTIVITY_STARTUP,
    HEALTHTECH_TELEMEDICINE_STARTUP,
    ECOMMERCE_MARKETPLACE_GROWTH,
    EDTECH_PLATFORM_INTERNATIONAL
]

LOW_VIABILITY_SCENARIOS = [
    NICHE_MARKET_SCENARIO
]

HIGH_RISK_SCENARIOS = [
    FINTECH_NEOBANK_STARTUP,
    HIGHLY_REGULATED_SCENARIO
]

COMPLEX_SCENARIOS = [
    FINTECH_NEOBANK_STARTUP,
    HEALTHTECH_TELEMEDICINE_STARTUP,
    EDTECH_PLATFORM_INTERNATIONAL,
    MANUFACTURING_DIGITAL_TRANSFORMATION,
    HIGHLY_REGULATED_SCENARIO
]

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_scenario_by_id(scenario_id: str) -> Optional[BusinessScenario]:
    """Get a specific scenario by ID"""
    for scenario in ALL_SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None

def get_scenarios_by_industry(industry: IndustryType) -> List[BusinessScenario]:
    """Get all scenarios for a specific industry"""
    return [s for s in ALL_SCENARIOS if s.industry == industry]

def get_scenarios_by_stage(stage: BusinessStage) -> List[BusinessScenario]:
    """Get all scenarios for a specific business stage"""
    return [s for s in ALL_SCENARIOS if s.business_stage == stage]

def get_scenarios_by_complexity(complexity: str) -> List[BusinessScenario]:
    """Get all scenarios with specific complexity level"""
    return [s for s in ALL_SCENARIOS if s.complexity_level == complexity]

def get_scenarios_by_tags(tags: List[str]) -> List[BusinessScenario]:
    """Get scenarios that match any of the provided tags"""
    return [s for s in ALL_SCENARIOS if any(tag in s.test_tags for tag in tags)]

def create_test_validation_requests(scenarios: List[BusinessScenario] = None) -> List[ValidationRequest]:
    """Create ValidationRequest objects from scenarios for testing"""
    if scenarios is None:
        scenarios = ALL_SCENARIOS
    
    return [scenario.to_validation_request() for scenario in scenarios]
