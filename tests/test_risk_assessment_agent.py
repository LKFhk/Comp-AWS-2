"""
Unit tests for Risk Assessment Agent
Tests risk evaluation, compliance checking, and barrier analysis functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, UTC

from riskintel360.agents.risk_assessment_agent import (
    RiskAssessmentAgent,
    BusinessRisk,
    MarketEntryBarrier,
    RegulatoryCompliance,
    RiskAssessmentResult
)
from riskintel360.agents.base_agent import AgentConfig
from riskintel360.models.agent_models import AgentType
from riskintel360.services.bedrock_client import BedrockClient, BedrockResponse


class TestRiskAssessmentAgent:
    """Test suite for Risk Assessment Agent"""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Create mock Bedrock client"""
        client = Mock(spec=BedrockClient)
        client.invoke_for_agent = AsyncMock()
        return client
    
    @pytest.fixture
    def agent_config(self, mock_bedrock_client):
        """Create agent configuration"""
        return AgentConfig(
            agent_id="test-risk-agent",
            agent_type=AgentType.RISK_ASSESSMENT,
            bedrock_client=mock_bedrock_client,
            max_retries=3,
            timeout_seconds=300
        )
    
    @pytest.fixture
    def risk_agent(self, agent_config):
        """Create Risk Assessment Agent instance"""
        with patch('boto3.client'):
            agent = RiskAssessmentAgent(agent_config)
        return agent
    
    def test_agent_initialization(self, risk_agent):
        """Test agent initialization"""
        assert risk_agent.agent_type == AgentType.RISK_ASSESSMENT
        assert risk_agent.agent_id == "test-risk-agent"
        assert 'sec_edgar' in risk_agent.data_sources
        assert 'regulatory_news' in risk_agent.data_sources
        assert 'compliance_db' in risk_agent.data_sources
    
    def test_get_capabilities(self, risk_agent):
        """Test agent capabilities"""
        capabilities = risk_agent.get_capabilities()
        
        expected_capabilities = [
            "business_risk_assessment",
            "market_entry_barrier_analysis",
            "regulatory_compliance_check",
            "risk_mitigation_planning",
            "risk_monitoring_setup",
            "compliance_cost_estimation",
            "risk_factor_identification"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, risk_agent):
        """Test agent start and stop functionality"""
        # Test start
        await risk_agent.start()
        assert risk_agent.http_session is not None
        
        # Test stop
        await risk_agent.stop()
        # Session should be closed but we can't easily test that
    
    @pytest.mark.asyncio
    async def test_business_risk_evaluation(self, risk_agent):
        """Test business risk evaluation"""
        # Mock LLM response
        mock_response = {
            "risks": [
                {
                    "risk_category": "market",
                    "risk_level": "high",
                    "probability": 0.7,
                    "impact_score": 8.0,
                    "description": "Market competition risk",
                    "mitigation_strategies": ["Market research", "Competitive analysis"],
                    "monitoring_indicators": ["Market share", "Customer acquisition"]
                },
                {
                    "risk_category": "operational",
                    "risk_level": "medium",
                    "probability": 0.5,
                    "impact_score": 6.0,
                    "description": "Operational scaling risk",
                    "mitigation_strategies": ["Process automation", "Team training"],
                    "monitoring_indicators": ["Efficiency metrics", "Error rates"]
                }
            ]
        }
        
        risk_agent.bedrock_client.invoke_for_agent.return_value = BedrockResponse(
            content=json.dumps(mock_response),
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            input_tokens=100,
            output_tokens=200,
            stop_reason="end_turn",
            raw_response={}
        )
        
        # Execute business risk evaluation
        parameters = {
            'business_model': 'saas',
            'industry': 'technology'
        }
        
        risks = await risk_agent._evaluate_business_risks(parameters)
        
        # Verify results
        assert len(risks) == 2
        
        # Check first risk
        assert risks[0].risk_category == "market"
        assert risks[0].risk_level == "high"
        assert risks[0].probability == 0.7
        assert risks[0].impact_score == 8.0
        assert risks[0].risk_score == 5.6  # 0.7 * 8.0
        assert "Market competition risk" in risks[0].description
        assert "Market research" in risks[0].mitigation_strategies
        
        # Check second risk
        assert risks[1].risk_category == "operational"
        assert risks[1].risk_level == "medium"
        assert risks[1].probability == 0.5
        assert risks[1].impact_score == 6.0
        assert risks[1].risk_score == 3.0  # 0.5 * 6.0
    
    @pytest.mark.asyncio
    async def test_market_entry_barrier_analysis(self, risk_agent):
        """Test market entry barrier analysis"""
        # Mock LLM response
        mock_response = {
            "barriers": [
                {
                    "barrier_type": "regulatory",
                    "severity": "high",
                    "description": "Complex regulatory approval process",
                    "estimated_cost": 500000,
                    "time_to_overcome_months": 12,
                    "regulatory_requirements": ["FDA approval", "State licensing"],
                    "competitive_factors": ["Established players", "High switching costs"]
                },
                {
                    "barrier_type": "capital",
                    "severity": "medium",
                    "description": "High initial capital requirements",
                    "estimated_cost": 1000000,
                    "time_to_overcome_months": 6,
                    "regulatory_requirements": [],
                    "competitive_factors": ["Economies of scale"]
                }
            ]
        }
        
        risk_agent.bedrock_client.invoke_for_agent.return_value = BedrockResponse(
            content=json.dumps(mock_response),
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            input_tokens=150,
            output_tokens=250,
            stop_reason="end_turn",
            raw_response={}
        )
        
        # Execute barrier analysis
        parameters = {
            'industry': 'healthcare',
            'target_markets': ['US', 'EU'],
            'business_model': 'medical_device'
        }
        
        barriers = await risk_agent._analyze_market_entry_barriers(parameters)
        
        # Verify results
        assert len(barriers) == 2
        
        # Check regulatory barrier
        assert barriers[0].barrier_type == "regulatory"
        assert barriers[0].severity == "high"
        assert barriers[0].estimated_cost == 500000
        assert barriers[0].time_to_overcome_months == 12
        assert "FDA approval" in barriers[0].regulatory_requirements
        
        # Check capital barrier
        assert barriers[1].barrier_type == "capital"
        assert barriers[1].severity == "medium"
        assert barriers[1].estimated_cost == 1000000
        assert barriers[1].time_to_overcome_months == 6
    
    @pytest.mark.asyncio
    async def test_regulatory_compliance_assessment(self, risk_agent):
        """Test regulatory compliance assessment"""
        # Mock LLM response
        mock_response = {
            "compliance_areas": [
                {
                    "regulation_type": "data_privacy",
                    "compliance_level": "partial",
                    "requirements": ["GDPR compliance", "Data encryption", "Privacy policy"],
                    "compliance_cost": 75000,
                    "implementation_timeline_months": 4,
                    "penalties_for_non_compliance": "Fines up to 4% of revenue",
                    "monitoring_requirements": ["Regular audits", "Data breach reporting"]
                },
                {
                    "regulation_type": "financial",
                    "compliance_level": "non_compliant",
                    "requirements": ["SOX compliance", "Financial reporting", "Audit requirements"],
                    "compliance_cost": 150000,
                    "implementation_timeline_months": 8,
                    "penalties_for_non_compliance": "Criminal liability and fines",
                    "monitoring_requirements": ["Quarterly reporting", "External audits"]
                }
            ]
        }
        
        risk_agent.bedrock_client.invoke_for_agent.return_value = BedrockResponse(
            content=json.dumps(mock_response),
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            input_tokens=120,
            output_tokens=300,
            stop_reason="end_turn",
            raw_response={}
        )
        
        # Execute compliance assessment
        parameters = {
            'industry': 'fintech',
            'target_markets': ['US'],
            'business_model': 'payment_processor'
        }
        
        compliance_results = await risk_agent._assess_regulatory_compliance(parameters)
        
        # Verify results
        assert len(compliance_results) == 2
        
        # Check data privacy compliance
        assert compliance_results[0].jurisdiction == "US"
        assert compliance_results[0].regulation_type == "data_privacy"
        assert compliance_results[0].compliance_level == "partial"
        assert compliance_results[0].compliance_cost == 75000
        assert "GDPR compliance" in compliance_results[0].requirements
        
        # Check financial compliance
        assert compliance_results[1].regulation_type == "financial"
        assert compliance_results[1].compliance_level == "non_compliant"
        assert compliance_results[1].compliance_cost == 150000
        assert compliance_results[1].implementation_timeline_months == 8
    
    @pytest.mark.asyncio
    async def test_comprehensive_risk_assessment(self, risk_agent):
        """Test comprehensive risk assessment workflow"""
        # Mock multiple LLM responses for different assessment phases
        risk_response = {
            "risks": [
                {
                    "risk_category": "market",
                    "risk_level": "medium",
                    "probability": 0.6,
                    "impact_score": 7.0,
                    "description": "Market volatility risk",
                    "mitigation_strategies": ["Diversification", "Market monitoring"],
                    "monitoring_indicators": ["Market trends", "Volatility index"]
                }
            ]
        }
        
        barrier_response = {
            "barriers": [
                {
                    "barrier_type": "technology",
                    "severity": "medium",
                    "description": "Technical complexity barrier",
                    "estimated_cost": 200000,
                    "time_to_overcome_months": 8,
                    "regulatory_requirements": [],
                    "competitive_factors": ["Technical expertise required"]
                }
            ]
        }
        
        compliance_response = {
            "compliance_areas": [
                {
                    "regulation_type": "industry_specific",
                    "compliance_level": "unknown",
                    "requirements": ["Industry certification"],
                    "compliance_cost": 50000,
                    "implementation_timeline_months": 3,
                    "penalties_for_non_compliance": "Business license revocation",
                    "monitoring_requirements": ["Annual certification renewal"]
                }
            ]
        }
        
        mitigation_response = [
            "Implement comprehensive market monitoring system",
            "Develop technical expertise through hiring and training",
            "Establish compliance management framework"
        ]
        
        # Set up mock responses in sequence (need 2 compliance responses for US and CA)
        risk_agent.bedrock_client.invoke_for_agent.side_effect = [
            BedrockResponse(content=json.dumps(risk_response), model_id="test", input_tokens=100, output_tokens=200, stop_reason="end_turn", raw_response={}),
            BedrockResponse(content=json.dumps(barrier_response), model_id="test", input_tokens=120, output_tokens=180, stop_reason="end_turn", raw_response={}),
            BedrockResponse(content=json.dumps(compliance_response), model_id="test", input_tokens=110, output_tokens=190, stop_reason="end_turn", raw_response={}),  # US compliance
            BedrockResponse(content=json.dumps(compliance_response), model_id="test", input_tokens=110, output_tokens=190, stop_reason="end_turn", raw_response={}),  # CA compliance
            BedrockResponse(content=json.dumps(mitigation_response), model_id="test", input_tokens=80, output_tokens=150, stop_reason="end_turn", raw_response={})
        ]
        
        # Execute comprehensive risk assessment
        parameters = {
            'business_model': 'marketplace',
            'industry': 'e-commerce',
            'target_markets': ['US', 'CA']
        }
        
        result = await risk_agent.execute_task("risk_assessment", parameters)
        
        # Verify result structure
        assert 'assessment_result' in result
        assert 'metadata' in result
        
        assessment = result['assessment_result']
        
        # Check assessment components
        assert 'overall_risk_score' in assessment
        assert 'risk_level' in assessment
        assert 'business_risks' in assessment
        assert 'market_entry_barriers' in assessment
        assert 'regulatory_compliance' in assessment
        assert 'risk_mitigation_plan' in assessment
        
        # Verify metadata
        metadata = result['metadata']
        assert metadata['agent_id'] == "test-risk-agent"
        assert 'overall_risk_score' in metadata
        assert 'risk_level' in metadata
        assert 'recommendation' in metadata
    
    def test_risk_score_calculation(self, risk_agent):
        """Test overall risk score calculation"""
        # Create test data
        business_risks = [
            BusinessRisk(
                risk_category='market',
                risk_level='high',
                probability=0.8,
                impact_score=8.0,
                risk_score=6.4,
                description='High market risk',
                mitigation_strategies=[],
                monitoring_indicators=[]
            ),
            BusinessRisk(
                risk_category='operational',
                risk_level='medium',
                probability=0.5,
                impact_score=5.0,
                risk_score=2.5,
                description='Medium operational risk',
                mitigation_strategies=[],
                monitoring_indicators=[]
            )
        ]
        
        entry_barriers = [
            MarketEntryBarrier(
                barrier_type='regulatory',
                severity='high',
                description='High regulatory barrier',
                estimated_cost=100000,
                time_to_overcome_months=12,
                regulatory_requirements=[],
                competitive_factors=[]
            ),
            MarketEntryBarrier(
                barrier_type='capital',
                severity='medium',
                description='Medium capital barrier',
                estimated_cost=50000,
                time_to_overcome_months=6,
                regulatory_requirements=[],
                competitive_factors=[]
            )
        ]
        
        regulatory_compliance = [
            RegulatoryCompliance(
                jurisdiction='US',
                regulation_type='data_privacy',
                compliance_level='non_compliant',
                requirements=[],
                compliance_cost=25000,
                implementation_timeline_months=3,
                penalties_for_non_compliance='Fines',
                monitoring_requirements=[]
            )
        ]
        
        # Calculate risk score
        risk_score = risk_agent._calculate_overall_risk_score(
            business_risks, entry_barriers, regulatory_compliance
        )
        
        # Verify score is reasonable (should be > 0 and <= 100)
        assert 0 <= risk_score <= 100
        assert isinstance(risk_score, (int, float))
    
    def test_risk_level_determination(self, risk_agent):
        """Test risk level determination from score"""
        assert risk_agent._determine_risk_level(25.0) == 'low'
        assert risk_agent._determine_risk_level(45.0) == 'medium'
        assert risk_agent._determine_risk_level(70.0) == 'high'
        assert risk_agent._determine_risk_level(90.0) == 'critical'
    
    def test_risk_categorization(self, risk_agent):
        """Test risk factor categorization"""
        # Create test data
        business_risks = [
            BusinessRisk(
                risk_category='market',
                risk_level='high',
                probability=0.7,
                impact_score=8.0,
                risk_score=5.6,
                description='Market competition risk',
                mitigation_strategies=[],
                monitoring_indicators=[]
            ),
            BusinessRisk(
                risk_category='operational',
                risk_level='medium',
                probability=0.5,
                impact_score=6.0,
                risk_score=3.0,
                description='Operational efficiency risk',
                mitigation_strategies=[],
                monitoring_indicators=[]
            )
        ]
        
        entry_barriers = [
            MarketEntryBarrier(
                barrier_type='regulatory',
                severity='high',
                description='Regulatory approval barrier',
                estimated_cost=100000,
                time_to_overcome_months=12,
                regulatory_requirements=[],
                competitive_factors=[]
            )
        ]
        
        regulatory_compliance = [
            RegulatoryCompliance(
                jurisdiction='US',
                regulation_type='data_privacy',
                compliance_level='partial',
                requirements=[],
                compliance_cost=25000,
                implementation_timeline_months=3,
                penalties_for_non_compliance='Fines',
                monitoring_requirements=[]
            )
        ]
        
        # Test categorization
        categories = risk_agent._categorize_risk_factors(
            business_risks, entry_barriers, regulatory_compliance
        )
        
        # Verify categorization
        assert 'Market competition risk' in categories['market']
        assert 'Operational efficiency risk' in categories['operational']
        assert 'Regulatory approval barrier' in categories['regulatory']
        assert 'data_privacy in US' in categories['regulatory']
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_task(self, risk_agent):
        """Test error handling for invalid task type"""
        with pytest.raises(ValueError, match="Unknown task type"):
            await risk_agent.execute_task("invalid_task", {})
    
    @pytest.mark.asyncio
    async def test_llm_response_parsing_error(self, risk_agent):
        """Test handling of invalid LLM responses"""
        # Mock invalid JSON response
        risk_agent.bedrock_client.invoke_for_agent.return_value = BedrockResponse(
            content="Invalid JSON response",
            model_id="test",
            input_tokens=50,
            output_tokens=100,
            stop_reason="end_turn",
            raw_response={}
        )
        
        # Should fall back to default risks
        parameters = {'business_model': 'saas', 'industry': 'technology'}
        risks = await risk_agent._evaluate_business_risks(parameters)
        
        # Should return default risks
        assert len(risks) >= 1
        assert all(isinstance(risk, BusinessRisk) for risk in risks)
    
    def test_confidence_score_calculation(self, risk_agent):
        """Test confidence score calculation"""
        # Test with no data cache
        confidence = risk_agent._calculate_confidence_score({})
        assert 0.0 <= confidence <= 1.0
        
        # Test with data cache
        risk_agent.data_cache = {'test_data': 'value'}
        confidence_with_cache = risk_agent._calculate_confidence_score({})
        assert confidence_with_cache > confidence
    
    def test_risk_recommendation_generation(self, risk_agent):
        """Test risk recommendation generation"""
        assert "standard risk management" in risk_agent._generate_risk_recommendation('low')
        assert "enhanced risk monitoring" in risk_agent._generate_risk_recommendation('medium')
        assert "thorough risk mitigation" in risk_agent._generate_risk_recommendation('high')
        assert "Significant risk mitigation" in risk_agent._generate_risk_recommendation('critical')
    
    @pytest.mark.asyncio
    async def test_aws_service_initialization(self, agent_config):
        """Test AWS service initialization handling"""
        # Test with AWS services available
        with patch('boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client
            
            agent = RiskAssessmentAgent(agent_config)
            
            # Should have AWS clients
            assert 'comprehend' in agent.aws_clients
            assert 'cloudwatch' in agent.aws_clients
            assert 'sns' in agent.aws_clients
            assert 'sagemaker' in agent.aws_clients
        
        # Test with AWS services unavailable
        with patch('boto3.client', side_effect=Exception("No credentials")):
            with patch.object(RiskAssessmentAgent, '_initialize_aws_services') as mock_init:
                mock_init.return_value = None
                agent = RiskAssessmentAgent(agent_config)
                
                # Should handle gracefully
                assert isinstance(agent.aws_clients, dict)
    
    @pytest.mark.asyncio
    async def test_monitoring_framework_setup(self, risk_agent):
        """Test risk monitoring framework setup"""
        parameters = {'business_model': 'saas'}
        
        result = await risk_agent._setup_risk_monitoring_framework(parameters)
        
        # Verify framework structure
        assert 'framework_result' in result
        assert 'metadata' in result
        
        framework = result['framework_result']
        assert 'monitoring_setup' in framework
        assert framework['monitoring_setup'] == 'completed'
        
        metadata = result['metadata']
        assert metadata['agent_id'] == "test-risk-agent"
        assert metadata['setup_status'] == 'completed'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
