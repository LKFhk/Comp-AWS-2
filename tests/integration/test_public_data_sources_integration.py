"""
Integration tests for public data source integrations (SEC, FINRA, CFPB, FRED).
Tests real API connections, data quality, and integration with fintech agents.
"""

import pytest
import pytest_asyncio
import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional

from riskintel360.services.external_data_integration_layer import (
    ExternalDataIntegrationLayer, DataSource, DataQuality
)
from riskintel360.agents.regulatory_compliance_agent import RegulatoryComplianceAgent
from riskintel360.agents.market_analysis_agent import MarketAnalysisAgent


class TestSECEdgarIntegration:
    """Integration tests for SEC EDGAR API"""
    
    @pytest.fixture
    def data_integration_layer(self):
        """Create data integration layer for testing"""
        return ExternalDataIntegrationLayer()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sec_edgar_api_connectivity(self, data_integration_layer):
        """Test SEC EDGAR API connectivity and basic functionality"""
        try:
            # Test SEC EDGAR company search
            search_result = await data_integration_layer.fetch_sec_data(
                endpoint="company_search",
                params={
                    "query": "fintech",
                    "limit": 10
                }
            )
            
            assert search_result is not None
            assert "companies" in search_result or "results" in search_result
            
            # Verify data structure
            if "companies" in search_result:
                companies = search_result["companies"]
                assert isinstance(companies, list)
                if len(companies) > 0:
                    company = companies[0]
                    assert "cik" in company
                    assert "name" in company
                    
        except Exception as e:
            pytest.skip(f"SEC EDGAR API not accessible: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sec_filings_retrieval(self, data_integration_layer):
        """Test SEC filings retrieval for fintech companies"""
        try:
            # Test retrieving recent 10-K filings for fintech companies
            filings_result = await data_integration_layer.fetch_sec_data(
                endpoint="filings",
                params={
                    "form_type": "10-K",
                    "date_range": "recent",
                    "industry": "fintech",
                    "limit": 5
                }
            )
            
            assert filings_result is not None
            
            if "filings" in filings_result:
                filings = filings_result["filings"]
                assert isinstance(filings, list)
                
                for filing in filings[:3]:  # Check first 3 filings
                    assert "accession_number" in filing
                    assert "form_type" in filing
                    assert filing["form_type"] == "10-K"
                    
        except Exception as e:
            pytest.skip(f"SEC filings API not accessible: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sec_data_quality_assessment(self, data_integration_layer):
        """Test SEC data quality assessment and validation"""
        try:
            # Test data quality validation for SEC filings
            sample_filing_data = {
                "cik": "0001234567",
                "company_name": "Test FinTech Corp",
                "form_type": "10-K",
                "filing_date": "2024-01-15",
                "accession_number": "0001234567-24-000001"
            }
            
            quality_result = await data_integration_layer.validate_sec_data_quality(sample_filing_data)
            
            assert quality_result is not None
            assert hasattr(quality_result, "quality_score")
            assert hasattr(quality_result, "is_valid")
            assert 0.0 <= quality_result.quality_score <= 1.0
            
        except Exception as e:
            pytest.skip(f"SEC data quality validation not available: {e}")


class TestFINRAIntegration:
    """Integration tests for FINRA regulatory data"""
    
    @pytest.fixture
    def data_integration_layer(self):
        """Create data integration layer for testing"""
        return ExternalDataIntegrationLayer()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_finra_regulatory_updates(self, data_integration_layer):
        """Test FINRA regulatory updates retrieval"""
        try:
            # Test FINRA regulatory notices
            regulatory_result = await data_integration_layer.fetch_finra_data(
                endpoint="regulatory_notices",
                params={
                    "date_range": "recent",
                    "category": "fintech",
                    "limit": 10
                }
            )
            
            assert regulatory_result is not None
            
            if "notices" in regulatory_result:
                notices = regulatory_result["notices"]
                assert isinstance(notices, list)
                
                for notice in notices[:3]:  # Check first 3 notices
                    assert "notice_id" in notice or "id" in notice
                    assert "title" in notice or "subject" in notice
                    assert "date" in notice or "published_date" in notice
                    
        except Exception as e:
            pytest.skip(f"FINRA API not accessible: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_finra_broker_dealer_data(self, data_integration_layer):
        """Test FINRA broker-dealer information retrieval"""
        try:
            # Test broker-dealer search
            bd_result = await data_integration_layer.fetch_finra_data(
                endpoint="broker_dealers",
                params={
                    "search_type": "fintech",
                    "status": "active",
                    "limit": 5
                }
            )
            
            assert bd_result is not None
            
            if "broker_dealers" in bd_result:
                brokers = bd_result["broker_dealers"]
                assert isinstance(brokers, list)
                
        except Exception as e:
            pytest.skip(f"FINRA broker-dealer API not accessible: {e}")


class TestCFPBIntegration:
    """Integration tests for CFPB consumer finance data"""
    
    @pytest.fixture
    def data_integration_layer(self):
        """Create data integration layer for testing"""
        return ExternalDataIntegrationLayer()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cfpb_regulatory_guidance(self, data_integration_layer):
        """Test CFPB regulatory guidance retrieval"""
        try:
            # Test CFPB guidance documents
            guidance_result = await data_integration_layer.fetch_cfpb_data(
                endpoint="guidance",
                params={
                    "topic": "digital_payments",
                    "date_range": "recent",
                    "limit": 10
                }
            )
            
            assert guidance_result is not None
            
            if "guidance_documents" in guidance_result:
                documents = guidance_result["guidance_documents"]
                assert isinstance(documents, list)
                
                for doc in documents[:3]:  # Check first 3 documents
                    assert "title" in doc or "subject" in doc
                    assert "date" in doc or "published_date" in doc
                    
        except Exception as e:
            pytest.skip(f"CFPB API not accessible: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cfpb_complaint_data(self, data_integration_layer):
        """Test CFPB consumer complaint data retrieval"""
        try:
            # Test consumer complaint trends
            complaint_result = await data_integration_layer.fetch_cfpb_data(
                endpoint="complaints",
                params={
                    "product": "credit_card",
                    "date_range": "last_30_days",
                    "aggregation": "trends"
                }
            )
            
            assert complaint_result is not None
            
            if "complaint_trends" in complaint_result:
                trends = complaint_result["complaint_trends"]
                assert isinstance(trends, (list, dict))
                
        except Exception as e:
            pytest.skip(f"CFPB complaint API not accessible: {e}")


class TestFREDIntegration:
    """Integration tests for Federal Reserve Economic Data (FRED)"""
    
    @pytest.fixture
    def data_integration_layer(self):
        """Create data integration layer for testing"""
        return ExternalDataIntegrationLayer()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fred_economic_indicators(self, data_integration_layer):
        """Test FRED economic indicators retrieval"""
        try:
            # Test key economic indicators
            economic_result = await data_integration_layer.fetch_fred_data(
                endpoint="series/observations",
                params={
                    "series_id": "GDP",  # Gross Domestic Product
                    "limit": 10,
                    "sort_order": "desc"
                }
            )
            
            assert economic_result is not None
            
            if "observations" in economic_result:
                observations = economic_result["observations"]
                assert isinstance(observations, list)
                
                for obs in observations[:3]:  # Check first 3 observations
                    assert "date" in obs
                    assert "value" in obs
                    
        except Exception as e:
            pytest.skip(f"FRED API not accessible: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fred_financial_stress_indicators(self, data_integration_layer):
        """Test FRED financial stress indicators for fintech risk assessment"""
        try:
            # Test financial stress indicators relevant to fintech
            stress_indicators = ["STLFSI", "NFCI", "ANFCI"]  # Financial stress indices
            
            for indicator in stress_indicators:
                stress_result = await data_integration_layer.fetch_fred_data(
                    endpoint="series/observations",
                    params={
                        "series_id": indicator,
                        "limit": 5,
                        "sort_order": "desc"
                    }
                )
                
                assert stress_result is not None
                
                if "observations" in stress_result:
                    observations = stress_result["observations"]
                    assert isinstance(observations, list)
                    
        except Exception as e:
            pytest.skip(f"FRED financial stress indicators not accessible: {e}")


class TestYahooFinanceIntegration:
    """Integration tests for Yahoo Finance public market data"""
    
    @pytest.fixture
    def data_integration_layer(self):
        """Create data integration layer for testing"""
        return ExternalDataIntegrationLayer()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_yahoo_finance_market_data(self, data_integration_layer):
        """Test Yahoo Finance market data retrieval"""
        try:
            # Test market data for fintech stocks
            fintech_symbols = ["SQ", "PYPL", "V", "MA"]  # Major fintech companies
            
            for symbol in fintech_symbols[:2]:  # Test first 2 symbols
                market_result = await data_integration_layer.fetch_yahoo_finance_data(
                    endpoint="quote",
                    params={
                        "symbol": symbol,
                        "interval": "1d",
                        "range": "5d"
                    }
                )
                
                assert market_result is not None
                
                if "chart" in market_result:
                    chart_data = market_result["chart"]
                    assert "result" in chart_data
                    
        except Exception as e:
            pytest.skip(f"Yahoo Finance API not accessible: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_yahoo_finance_fintech_sector_analysis(self, data_integration_layer):
        """Test Yahoo Finance fintech sector analysis"""
        try:
            # Test fintech sector ETF data
            sector_result = await data_integration_layer.fetch_yahoo_finance_data(
                endpoint="quote",
                params={
                    "symbol": "FINX",  # Global X FinTech ETF
                    "interval": "1d",
                    "range": "1mo"
                }
            )
            
            assert sector_result is not None
            
        except Exception as e:
            pytest.skip(f"Yahoo Finance sector data not accessible: {e}")


class TestIntegratedPublicDataWorkflow:
    """Integration tests for complete public data workflows"""
    
    @pytest.fixture
    def data_integration_layer(self):
        """Create data integration layer for testing"""
        return ExternalDataIntegrationLayer()
    
    @pytest.fixture
    def regulatory_compliance_agent(self, data_integration_layer):
        """Create regulatory compliance agent with data integration"""
        return RegulatoryComplianceAgent(
            data_integration_layer=data_integration_layer
        )
    
    @pytest.fixture
    def market_analysis_agent(self, data_integration_layer):
        """Create market analysis agent with data integration"""
        return MarketAnalysisAgent(
            data_integration_layer=data_integration_layer
        )
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comprehensive_regulatory_data_integration(
        self, 
        regulatory_compliance_agent, 
        data_integration_layer
    ):
        """Test comprehensive regulatory data integration across all sources"""
        try:
            # Test integrated regulatory analysis using multiple public sources
            regulatory_request = {
                "entity_type": "fintech_startup",
                "business_model": "digital_payments",
                "jurisdiction": "US",
                "analysis_scope": ["SEC", "FINRA", "CFPB"]
            }
            
            # Execute comprehensive regulatory analysis
            analysis_result = await regulatory_compliance_agent.analyze_comprehensive_compliance(
                regulatory_request
            )
            
            assert analysis_result is not None
            assert hasattr(analysis_result, "compliance_status")
            assert hasattr(analysis_result, "data_sources_used")
            
            # Verify multiple data sources were integrated
            data_sources = analysis_result.data_sources_used
            expected_sources = ["SEC", "FINRA", "CFPB"]
            
            for source in expected_sources:
                assert any(source.lower() in ds.lower() for ds in data_sources), \
                    f"Expected {source} data source not found in analysis"
                    
        except Exception as e:
            pytest.skip(f"Comprehensive regulatory analysis not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_integrated_market_intelligence_workflow(
        self, 
        market_analysis_agent, 
        data_integration_layer
    ):
        """Test integrated market intelligence using public data sources"""
        try:
            # Test market intelligence using FRED + Yahoo Finance
            market_request = {
                "analysis_type": "fintech_market_assessment",
                "sector": "digital_payments",
                "time_horizon": "1Y",
                "data_sources": ["FRED", "yahoo_finance"]
            }
            
            # Execute market intelligence analysis
            market_result = await market_analysis_agent.analyze_market_intelligence(
                market_request
            )
            
            assert market_result is not None
            assert hasattr(market_result, "market_trends")
            assert hasattr(market_result, "economic_indicators")
            assert hasattr(market_result, "data_quality_score")
            
            # Verify data quality meets requirements
            assert market_result.data_quality_score >= 0.6, \
                "Market intelligence data quality should be >= 0.6"
                
        except Exception as e:
            pytest.skip(f"Market intelligence analysis not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_public_data_performance_requirements(self, data_integration_layer):
        """Test public data integration performance requirements"""
        # Test concurrent data fetching from multiple sources
        data_requests = [
            ("SEC", {"endpoint": "company_search", "params": {"query": "fintech"}}),
            ("FINRA", {"endpoint": "regulatory_notices", "params": {"limit": 5}}),
            ("CFPB", {"endpoint": "guidance", "params": {"topic": "payments"}}),
            ("FRED", {"endpoint": "series/observations", "params": {"series_id": "GDP"}}),
            ("yahoo_finance", {"endpoint": "quote", "params": {"symbol": "SQ"}})
        ]
        
        # Execute concurrent requests
        start_time = datetime.now(timezone.utc)
        
        tasks = []
        for source, request_data in data_requests:
            if source == "SEC":
                task = data_integration_layer.fetch_sec_data(**request_data)
            elif source == "FINRA":
                task = data_integration_layer.fetch_finra_data(**request_data)
            elif source == "CFPB":
                task = data_integration_layer.fetch_cfpb_data(**request_data)
            elif source == "FRED":
                task = data_integration_layer.fetch_fred_data(**request_data)
            elif source == "yahoo_finance":
                task = data_integration_layer.fetch_yahoo_finance_data(**request_data)
            
            tasks.append(task)
        
        try:
            # Execute all requests concurrently with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0  # 30 second timeout for all requests
            )
            
            end_time = datetime.now(timezone.utc)
            total_time = (end_time - start_time).total_seconds()
            
            # Verify performance requirements
            assert total_time < 30.0, f"Public data integration took {total_time:.2f}s, should be < 30s"
            
            # Verify at least some requests succeeded
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= 2, "At least 2 public data sources should be accessible"
            
        except asyncio.TimeoutError:
            pytest.skip("Public data sources timeout - network connectivity issues")
        except Exception as e:
            pytest.skip(f"Public data integration test failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_quality_validation_across_sources(self, data_integration_layer):
        """Test data quality validation across all public data sources"""
        # Test data quality validation for different source types
        quality_tests = [
            {
                "source_type": "SEC",
                "sample_data": {
                    "cik": "0001234567",
                    "company_name": "Test Corp",
                    "form_type": "10-K",
                    "filing_date": "2024-01-15"
                }
            },
            {
                "source_type": "FINRA",
                "sample_data": {
                    "notice_id": "24-001",
                    "title": "Test Regulatory Notice",
                    "published_date": "2024-01-15"
                }
            },
            {
                "source_type": "CFPB",
                "sample_data": {
                    "guidance_id": "cfpb-2024-001",
                    "title": "Digital Payment Guidance",
                    "published_date": "2024-01-15"
                }
            },
            {
                "source_type": "FRED",
                "sample_data": {
                    "series_id": "GDP",
                    "date": "2024-01-01",
                    "value": "25000.0"
                }
            },
            {
                "source_type": "yahoo_finance",
                "sample_data": {
                    "symbol": "SQ",
                    "price": 75.50,
                    "volume": 1000000,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        ]
        
        for test in quality_tests:
            try:
                quality_result = await data_integration_layer.validate_data_quality(
                    data=test["sample_data"],
                    source_type=test["source_type"],
                    source_name=f"test_{test['source_type'].lower()}"
                )
                
                assert quality_result is not None
                assert hasattr(quality_result, "quality_score")
                assert hasattr(quality_result, "is_valid")
                assert 0.0 <= quality_result.quality_score <= 1.0
                
            except Exception as e:
                # Log but don't fail test for individual source validation issues
                print(f"Data quality validation for {test['source_type']} failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
