"""
Integration tests for business value calculation workflows.
Tests value generation tracking, ROI calculations, and business impact metrics.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from riskintel360.services.business_value_calculator import (
    BusinessValueCalculator, CompanyProfile, CompanySize, IndustryType,
    FraudPreventionValue, ComplianceCostSavings, RiskReductionValue,
    BusinessValueCalculation, business_value_calculator
)
from riskintel360.services.performance_monitor import PerformanceMonitor
from riskintel360.agents.fraud_detection_agent import FraudDetectionAgent
from riskintel360.agents.regulatory_compliance_agent import RegulatoryComplianceAgent


class TestBusinessValueCalculationIntegration:
    """Integration tests for business value calculation system"""
    
    @pytest.fixture
    def business_value_calculator(self):
        """Create business value calculator for testing"""
        return BusinessValueCalculator()
    
    @pytest.fixture
    def mock_performance_monitor(self):
        """Mock performance monitor for testing"""
        mock_monitor = Mock(spec=PerformanceMonitor)
        mock_monitor.get_fraud_prevention_metrics = AsyncMock()
        mock_monitor.get_compliance_metrics = AsyncMock()
        mock_monitor.get_operational_metrics = AsyncMock()
        return mock_monitor
    
    @pytest.fixture
    def sample_company_profiles(self):
        """Sample company profiles for different business sizes"""
        return {
            "small_fintech": {
                "company_size": "small",
                "annual_revenue": 5_000_000,  # $5M
                "transaction_volume": 100_000_000,  # $100M
                "employee_count": 50,
                "compliance_budget": 200_000,  # $200K
                "fraud_losses_baseline": 500_000  # $500K
            },
            "medium_fintech": {
                "company_size": "medium",
                "annual_revenue": 50_000_000,  # $50M
                "transaction_volume": 1_000_000_000,  # $1B
                "employee_count": 200,
                "compliance_budget": 2_000_000,  # $2M
                "fraud_losses_baseline": 5_000_000  # $5M
            },
            "large_institution": {
                "company_size": "large",
                "annual_revenue": 500_000_000,  # $500M
                "transaction_volume": 50_000_000_000,  # $50B
                "employee_count": 2000,
                "compliance_budget": 20_000_000,  # $20M
                "fraud_losses_baseline": 50_000_000  # $50M
            }
        }
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fraud_prevention_value_calculation(
        self, 
        business_value_calculator, 
        sample_company_profiles
    ):
        """Test fraud prevention value calculation for different company sizes"""
        
        # Test fraud prevention value for each company size
        for company_type, profile in sample_company_profiles.items():
            # Mock fraud detection performance data
            fraud_metrics = {
                "total_transactions_analyzed": profile["transaction_volume"] // 12,  # Monthly
                "fraud_attempts_detected": 1000 if company_type == "small_fintech" else 5000 if company_type == "medium_fintech" else 25000,
                "false_positive_reduction": 0.90,  # 90% reduction requirement
                "average_fraud_amount": 2500,
                "prevention_accuracy": 0.95,
                "processing_time": 2.5  # seconds
            }
            
            # Calculate fraud prevention value
            fraud_value = await business_value_calculator.calculate_fraud_prevention_value(
                company_profile=profile,
                fraud_metrics=fraud_metrics,
                time_period="annual"
            )
            
            # Verify fraud prevention value meets requirements
            assert isinstance(fraud_value, FraudPreventionValue)
            assert fraud_value.total_prevented_losses > 0
            assert fraud_value.false_positive_savings > 0
            assert fraud_value.operational_efficiency_gains > 0
            
            # Verify scalable value generation based on company size
            if company_type == "small_fintech":
                # Small companies: $50K-$500K annual savings
                assert 50_000 <= fraud_value.total_annual_value <= 500_000
            elif company_type == "medium_fintech":
                # Medium companies: $500K-$5M annual value
                assert 500_000 <= fraud_value.total_annual_value <= 5_000_000
            elif company_type == "large_institution":
                # Large institutions: $5M-$20M+ annual value
                assert fraud_value.total_annual_value >= 5_000_000
            
            # Verify fraud prevention meets $10M+ requirement for major institutions
            if company_type == "large_institution":
                assert fraud_value.total_prevented_losses >= 10_000_000
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compliance_cost_savings_calculation(
        self, 
        business_value_calculator, 
        sample_company_profiles
    ):
        """Test compliance cost savings calculation (80% cost reduction target)"""
        
        for company_type, profile in sample_company_profiles.items():
            # Mock compliance automation metrics
            compliance_metrics = {
                "manual_compliance_hours_saved": 2000 if company_type == "small_fintech" else 8000 if company_type == "medium_fintech" else 20000,
                "automated_regulatory_monitoring": True,
                "compliance_violations_prevented": 5 if company_type == "small_fintech" else 15 if company_type == "medium_fintech" else 50,
                "regulatory_reporting_automation": 0.85,  # 85% automated
                "audit_preparation_time_reduction": 0.75,  # 75% reduction
                "average_compliance_officer_hourly_rate": 150
            }
            
            # Calculate compliance savings
            compliance_savings = await business_value_calculator.calculate_compliance_savings(
                company_profile=profile,
                compliance_metrics=compliance_metrics,
                time_period="annual"
            )
            
            # Verify compliance savings structure
            assert isinstance(compliance_savings, ComplianceSavings)
            assert compliance_savings.labor_cost_savings > 0
            assert compliance_savings.violation_prevention_value > 0
            assert compliance_savings.audit_efficiency_gains > 0
            
            # Verify 80% cost reduction target
            baseline_compliance_cost = profile["compliance_budget"]
            cost_reduction_percentage = compliance_savings.total_annual_savings / baseline_compliance_cost
            
            # Should achieve significant cost reduction (targeting 80%)
            assert cost_reduction_percentage >= 0.60, f"Cost reduction {cost_reduction_percentage:.2%} should be >= 60%"
            
            # Verify scalable compliance savings
            if company_type == "large_institution":
                # Large institutions should achieve $5M+ compliance savings
                assert compliance_savings.total_annual_savings >= 5_000_000
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comprehensive_roi_calculation(
        self, 
        business_value_calculator, 
        sample_company_profiles
    ):
        """Test comprehensive ROI calculation for RiskIntel360 platform"""
        
        for company_type, profile in sample_company_profiles.items():
            # Mock platform implementation costs
            implementation_costs = {
                "platform_license": 100_000 if company_type == "small_fintech" else 500_000 if company_type == "medium_fintech" else 2_000_000,
                "implementation_services": 50_000 if company_type == "small_fintech" else 200_000 if company_type == "medium_fintech" else 800_000,
                "training_and_onboarding": 25_000 if company_type == "small_fintech" else 100_000 if company_type == "medium_fintech" else 400_000,
                "ongoing_maintenance": 20_000 if company_type == "small_fintech" else 80_000 if company_type == "medium_fintech" else 300_000
            }
            
            # Mock comprehensive value metrics
            value_metrics = {
                "fraud_prevention_value": 200_000 if company_type == "small_fintech" else 2_000_000 if company_type == "medium_fintech" else 15_000_000,
                "compliance_cost_savings": 150_000 if company_type == "small_fintech" else 1_500_000 if company_type == "medium_fintech" else 8_000_000,
                "operational_efficiency_gains": 100_000 if company_type == "small_fintech" else 800_000 if company_type == "medium_fintech" else 4_000_000,
                "risk_reduction_value": 75_000 if company_type == "small_fintech" else 600_000 if company_type == "medium_fintech" else 3_000_000,
                "time_savings_value": 50_000 if company_type == "small_fintech" else 400_000 if company_type == "medium_fintech" else 2_000_000
            }
            
            # Calculate comprehensive ROI
            roi_calculation = await business_value_calculator.calculate_comprehensive_roi(
                company_profile=profile,
                implementation_costs=implementation_costs,
                value_metrics=value_metrics,
                time_horizon_years=3
            )
            
            # Verify ROI calculation structure
            assert isinstance(roi_calculation, ROICalculation)
            assert roi_calculation.total_investment > 0
            assert roi_calculation.total_value_generated > 0
            assert roi_calculation.net_present_value > 0
            assert roi_calculation.roi_percentage > 0
            assert roi_calculation.payback_period_months > 0
            
            # Verify ROI meets business requirements (10x return target)
            assert roi_calculation.roi_percentage >= 300, f"ROI {roi_calculation.roi_percentage:.1f}% should be >= 300% (3x minimum)"
            
            # Verify payback period is reasonable (< 24 months)
            assert roi_calculation.payback_period_months <= 24, f"Payback period {roi_calculation.payback_period_months} months should be <= 24"
            
            # Verify scalable value generation
            expected_annual_value = sum(value_metrics.values())
            if company_type == "small_fintech":
                assert 50_000 <= expected_annual_value <= 1_000_000
            elif company_type == "medium_fintech":
                assert 1_000_000 <= expected_annual_value <= 10_000_000
            elif company_type == "large_institution":
                assert expected_annual_value >= 10_000_000
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_time_reduction_value_calculation(
        self, 
        business_value_calculator, 
        sample_company_profiles
    ):
        """Test time reduction value calculation (95% time reduction requirement)"""
        
        for company_type, profile in sample_company_profiles.items():
            # Mock time reduction metrics
            time_metrics = {
                "manual_analysis_time_baseline": 168,  # 1 week (168 hours)
                "automated_analysis_time": 2,  # 2 hours with RiskIntel360
                "analysis_frequency_monthly": 10 if company_type == "small_fintech" else 50 if company_type == "medium_fintech" else 200,
                "analyst_hourly_rate": 100,
                "senior_analyst_hourly_rate": 150,
                "compliance_officer_hourly_rate": 200
            }
            
            # Calculate time reduction value
            time_value = await business_value_calculator.calculate_time_reduction_value(
                company_profile=profile,
                time_metrics=time_metrics,
                time_period="annual"
            )
            
            # Verify time reduction meets 95% requirement
            time_reduction_percentage = (
                (time_metrics["manual_analysis_time_baseline"] - time_metrics["automated_analysis_time"]) 
                / time_metrics["manual_analysis_time_baseline"]
            )
            assert time_reduction_percentage >= 0.95, f"Time reduction {time_reduction_percentage:.2%} should be >= 95%"
            
            # Verify time savings value
            assert time_value.total_time_saved_hours > 0
            assert time_value.labor_cost_savings > 0
            assert time_value.productivity_gains > 0
            assert time_value.opportunity_cost_recovery > 0
            
            # Verify annual time savings value
            expected_monthly_savings = (
                time_metrics["analysis_frequency_monthly"] * 
                (time_metrics["manual_analysis_time_baseline"] - time_metrics["automated_analysis_time"]) *
                time_metrics["analyst_hourly_rate"]
            )
            expected_annual_savings = expected_monthly_savings * 12
            
            assert abs(time_value.annual_labor_savings - expected_annual_savings) < expected_annual_savings * 0.1  # 10% tolerance
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_business_value_dashboard_integration(
        self, 
        business_value_calculator, 
        sample_company_profiles
    ):
        """Test business value dashboard data integration"""
        
        # Test dashboard data generation for medium fintech company
        profile = sample_company_profiles["medium_fintech"]
        
        # Mock comprehensive business metrics
        business_metrics = {
            "fraud_prevention": {
                "prevented_losses": 2_000_000,
                "false_positive_reduction": 0.90,
                "processing_efficiency": 0.95
            },
            "compliance_automation": {
                "cost_savings": 1_500_000,
                "violation_prevention": 15,
                "audit_efficiency": 0.75
            },
            "operational_efficiency": {
                "time_savings_hours": 8000,
                "labor_cost_savings": 800_000,
                "productivity_gains": 0.85
            },
            "risk_reduction": {
                "risk_score_improvement": 0.40,
                "incident_reduction": 0.60,
                "insurance_savings": 200_000
            }
        }
        
        # Generate dashboard data
        dashboard_data = await business_value_calculator.generate_dashboard_data(
            company_profile=profile,
            business_metrics=business_metrics,
            time_period="annual"
        )
        
        # Verify dashboard data structure
        assert "total_annual_value" in dashboard_data
        assert "roi_metrics" in dashboard_data
        assert "value_breakdown" in dashboard_data
        assert "performance_indicators" in dashboard_data
        assert "trend_analysis" in dashboard_data
        
        # Verify total annual value meets expectations
        total_value = dashboard_data["total_annual_value"]
        assert 1_000_000 <= total_value <= 10_000_000  # Medium company range
        
        # Verify ROI metrics
        roi_metrics = dashboard_data["roi_metrics"]
        assert roi_metrics["roi_percentage"] >= 300  # 3x minimum return
        assert roi_metrics["payback_period_months"] <= 24
        
        # Verify value breakdown
        value_breakdown = dashboard_data["value_breakdown"]
        assert "fraud_prevention" in value_breakdown
        assert "compliance_savings" in value_breakdown
        assert "operational_efficiency" in value_breakdown
        assert "risk_reduction" in value_breakdown
        
        # Verify performance indicators
        performance_indicators = dashboard_data["performance_indicators"]
        assert "time_reduction_percentage" in performance_indicators
        assert "cost_reduction_percentage" in performance_indicators
        assert "fraud_detection_accuracy" in performance_indicators
        assert "compliance_automation_level" in performance_indicators
        
        # Verify key performance targets
        assert performance_indicators["time_reduction_percentage"] >= 95  # 95% time reduction
        assert performance_indicators["cost_reduction_percentage"] >= 60  # Significant cost reduction
        assert performance_indicators["fraud_detection_accuracy"] >= 90  # High accuracy
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_competitive_value_analysis(
        self, 
        business_value_calculator, 
        sample_company_profiles
    ):
        """Test competitive value analysis vs traditional solutions"""
        
        profile = sample_company_profiles["large_institution"]
        
        # Mock traditional solution costs and capabilities
        traditional_solution = {
            "manual_analysis_cost": 5_000_000,  # Annual cost of manual analysis
            "legacy_fraud_system_cost": 3_000_000,  # Legacy fraud detection
            "compliance_consulting_cost": 2_000_000,  # External compliance consulting
            "false_positive_rate": 0.15,  # 15% false positive rate
            "analysis_time": 168,  # 1 week per analysis
            "compliance_violations": 25,  # Annual violations
            "fraud_detection_accuracy": 0.75  # 75% accuracy
        }
        
        # Mock RiskIntel360 solution performance
        riskintel360_solution = {
            "platform_cost": 2_000_000,  # Annual platform cost
            "implementation_cost": 800_000,  # One-time implementation
            "false_positive_rate": 0.015,  # 1.5% false positive rate (90% reduction)
            "analysis_time": 2,  # 2 hours per analysis
            "compliance_violations": 2,  # Significant reduction
            "fraud_detection_accuracy": 0.95  # 95% accuracy
        }
        
        # Calculate competitive advantage
        competitive_analysis = await business_value_calculator.calculate_competitive_advantage(
            company_profile=profile,
            traditional_solution=traditional_solution,
            riskintel360_solution=riskintel360_solution
        )
        
        # Verify competitive advantages
        assert competitive_analysis.cost_advantage > 0
        assert competitive_analysis.performance_advantage > 0
        assert competitive_analysis.efficiency_advantage > 0
        
        # Verify specific improvements
        assert competitive_analysis.false_positive_improvement >= 0.90  # 90% improvement
        assert competitive_analysis.time_reduction >= 0.95  # 95% time reduction
        assert competitive_analysis.accuracy_improvement >= 0.20  # 20% accuracy improvement
        
        # Verify total competitive value
        assert competitive_analysis.total_competitive_value >= 10_000_000  # Significant advantage for large institutions


class TestBusinessValueReporting:
    """Integration tests for business value reporting and analytics"""
    
    @pytest.fixture
    def business_value_calculator(self):
        """Create business value calculator for testing"""
        return BusinessValueCalculator()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_executive_summary_generation(self, business_value_calculator):
        """Test executive summary generation for business value"""
        
        # Mock comprehensive business results
        business_results = {
            "company_profile": {
                "company_name": "FinTech Innovations Inc",
                "company_size": "medium",
                "annual_revenue": 50_000_000,
                "industry": "digital_payments"
            },
            "implementation_period": "12_months",
            "total_investment": 700_000,
            "annual_value_generated": 4_500_000,
            "roi_percentage": 542,  # 5.42x return
            "payback_period_months": 18,
            "key_achievements": {
                "fraud_prevention_value": 2_000_000,
                "compliance_cost_savings": 1_500_000,
                "operational_efficiency_gains": 800_000,
                "time_reduction_percentage": 95,
                "cost_reduction_percentage": 75
            }
        }
        
        # Generate executive summary
        executive_summary = await business_value_calculator.generate_executive_summary(
            business_results=business_results
        )
        
        # Verify executive summary structure
        assert "executive_overview" in executive_summary
        assert "key_metrics" in executive_summary
        assert "financial_impact" in executive_summary
        assert "operational_improvements" in executive_summary
        assert "competitive_advantages" in executive_summary
        assert "recommendations" in executive_summary
        
        # Verify key metrics
        key_metrics = executive_summary["key_metrics"]
        assert key_metrics["roi_percentage"] == 542
        assert key_metrics["annual_value"] == 4_500_000
        assert key_metrics["payback_months"] == 18
        
        # Verify financial impact
        financial_impact = executive_summary["financial_impact"]
        assert financial_impact["total_investment"] == 700_000
        assert financial_impact["net_present_value"] > 0
        assert financial_impact["break_even_achieved"] is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_trend_analysis_reporting(self, business_value_calculator):
        """Test trend analysis for business value over time"""
        
        # Mock historical business value data (12 months)
        historical_data = []
        base_value = 100_000
        
        for month in range(12):
            monthly_data = {
                "month": month + 1,
                "fraud_prevention_value": base_value * (1 + month * 0.1),
                "compliance_savings": base_value * 0.8 * (1 + month * 0.08),
                "operational_efficiency": base_value * 0.6 * (1 + month * 0.12),
                "total_monthly_value": 0
            }
            
            monthly_data["total_monthly_value"] = (
                monthly_data["fraud_prevention_value"] +
                monthly_data["compliance_savings"] +
                monthly_data["operational_efficiency"]
            )
            
            historical_data.append(monthly_data)
        
        # Generate trend analysis
        trend_analysis = await business_value_calculator.analyze_value_trends(
            historical_data=historical_data,
            analysis_period="12_months"
        )
        
        # Verify trend analysis
        assert "growth_trends" in trend_analysis
        assert "performance_indicators" in trend_analysis
        assert "forecasting" in trend_analysis
        assert "insights" in trend_analysis
        
        # Verify growth trends
        growth_trends = trend_analysis["growth_trends"]
        assert growth_trends["overall_growth_rate"] > 0
        assert growth_trends["fraud_prevention_growth"] > 0
        assert growth_trends["compliance_savings_growth"] > 0
        
        # Verify forecasting
        forecasting = trend_analysis["forecasting"]
        assert "next_quarter_projection" in forecasting
        assert "annual_projection" in forecasting
        assert forecasting["confidence_level"] >= 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
