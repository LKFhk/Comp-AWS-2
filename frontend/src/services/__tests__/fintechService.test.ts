/**
 * Unit tests for FintechService
 * Tests all service methods, caching, error handling, and validation
 */

import type {
  RiskAnalysisRequest,
  ComplianceCheckRequest,
  FraudDetectionRequest,
  MarketIntelligenceRequest,
  KYCVerificationRequest,
  BusinessValueCalculationRequest,
  TransactionData
} from '../../types/fintech';
import { Priority } from '../../types/fintech';

// IMPORTANT: Unmock the fintechService to override the global mock in setupTests.ts
jest.unmock('../fintechService');

// Mock the api module with mock functions
jest.mock('../api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
    put: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    },
    defaults: {
      headers: {
        common: {}
      }
    }
  },
  apiService: {}
}));

// Import fintechService AFTER the mock is set up
import { fintechService } from '../fintechService';
import { apiClient } from '../api';

// Get references to the mock functions
const mockGet = apiClient.get as jest.MockedFunction<typeof apiClient.get>;
const mockPost = apiClient.post as jest.MockedFunction<typeof apiClient.post>;
const mockDelete = apiClient.delete as jest.MockedFunction<typeof apiClient.delete>;

describe('FintechService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGet.mockClear();
    mockPost.mockClear();
    mockDelete.mockClear();
    fintechService.clearCache();
  });

  // ==================== RISK ANALYSIS TESTS ====================

  describe('Risk Analysis', () => {
    const mockRiskRequest: RiskAnalysisRequest = {
      entity_id: 'test-entity-123',
      entity_type: 'fintech_startup',
      analysis_scope: ['credit', 'market', 'operational'],
      priority: Priority.HIGH
    };

    const mockRiskResponse = {
      analysis_id: 'risk-123',
      status: 'initiated',
      message: 'Risk analysis started',
      entity_id: 'test-entity-123',
      entity_type: 'fintech_startup',
      analysis_scope: ['credit', 'market', 'operational']
    };

    it('should create risk analysis successfully', async () => {
      mockPost.mockResolvedValue({ data: mockRiskResponse } as { data: typeof mockRiskResponse });

      const result = await fintechService.createRiskAnalysis(mockRiskRequest);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/fintech/risk-analysis',
        mockRiskRequest
      );
      expect(result).toEqual(mockRiskResponse);
    });

    it('should get risk analysis result with caching', async () => {
      const mockResult = {
        entity_id: 'test-entity-123',
        overall_risk_score: 0.75,
        risk_level: 'medium',
        confidence_score: 0.9
      };

      mockGet.mockResolvedValue({ data: mockResult });

      // First call should hit API
      const result1 = await fintechService.getRiskAnalysisResult('risk-123');
      expect(mockGet).toHaveBeenCalledTimes(1);
      expect(result1).toEqual(mockResult);

      // Second call should use cache
      const result2 = await fintechService.getRiskAnalysisResult('risk-123');
      expect(mockGet).toHaveBeenCalledTimes(1); // Still 1, not 2
      expect(result2).toEqual(mockResult);
    });

    it('should get risk analysis progress', async () => {
      const mockProgress = {
        analysis_id: 'risk-123',
        status: 'in_progress',
        progress_percentage: 45,
        current_agent: 'risk_assessment'
      };

      mockGet.mockResolvedValue({ data: mockProgress });

      const result = await fintechService.getRiskAnalysisProgress('risk-123');

      expect(mockGet).toHaveBeenCalledWith(
        '/api/v1/fintech/risk-analysis/risk-123/progress'
      );
      expect(result).toEqual(mockProgress);
    });

    it('should validate risk analysis request', () => {
      // Valid request
      const validRequest: RiskAnalysisRequest = {
        entity_id: 'test-entity',
        entity_type: 'startup'
      };
      expect(fintechService.validateRiskAnalysisRequest(validRequest)).toEqual([]);

      // Invalid request - missing entity_id
      const invalidRequest1: RiskAnalysisRequest = {
        entity_id: '',
        entity_type: 'startup'
      };
      const errors1 = fintechService.validateRiskAnalysisRequest(invalidRequest1);
      expect(errors1).toContain('Entity ID is required');

      // Invalid request - missing entity_type
      const invalidRequest2: RiskAnalysisRequest = {
        entity_id: 'test',
        entity_type: ''
      };
      const errors2 = fintechService.validateRiskAnalysisRequest(invalidRequest2);
      expect(errors2).toContain('Entity type is required');

      // Invalid request - empty analysis scope
      const invalidRequest3: RiskAnalysisRequest = {
        entity_id: 'test',
        entity_type: 'startup',
        analysis_scope: []
      };
      const errors3 = fintechService.validateRiskAnalysisRequest(invalidRequest3);
      expect(errors3).toContain('At least one analysis scope must be selected');
    });
  });

  // ==================== COMPLIANCE CHECKS TESTS ====================

  describe('Compliance Checks', () => {
    const mockComplianceRequest: ComplianceCheckRequest = {
      business_type: 'fintech_startup',
      jurisdiction: 'US',
      regulations: ['SEC', 'FINRA'],
      priority: Priority.HIGH
    };

    const mockComplianceResponse = {
      analysis_id: 'compliance-123',
      status: 'initiated',
      message: 'Compliance check started',
      business_type: 'fintech_startup',
      jurisdiction: 'US',
      regulations_checked: ['SEC', 'FINRA']
    };

    it('should create compliance check successfully', async () => {
      mockPost.mockResolvedValue({ data: mockComplianceResponse });

      const result = await fintechService.createComplianceCheck(mockComplianceRequest);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/fintech/compliance-check',
        mockComplianceRequest
      );
      expect(result).toEqual(mockComplianceResponse);
    });

    it('should get compliance check result', async () => {
      const mockResult = [{
        regulation_id: 'SEC-001',
        compliance_status: 'compliant',
        risk_level: 'low',
        confidence_score: 0.95
      }];

      mockGet.mockResolvedValue({ data: mockResult });

      const result = await fintechService.getComplianceCheckResult('compliance-123');

      expect(mockGet).toHaveBeenCalledWith(
        '/api/v1/fintech/compliance-check/compliance-123/result'
      );
      expect(result).toEqual(mockResult);
    });
  });

  // ==================== FRAUD DETECTION TESTS ====================

  describe('Fraud Detection', () => {
    const mockTransactionData: TransactionData[] = [
      {
        transaction_id: 'txn-001',
        amount: 150.75,
        currency: 'USD',
        merchant: 'Test Store',
        timestamp: '2024-01-15T14:30:00Z',
        payment_method: 'credit_card',
        location: 'New York, NY',
        merchant_category: 'retail'
      }
    ];

    const mockFraudRequest: FraudDetectionRequest = {
      transaction_data: mockTransactionData,
      customer_id: 'customer-123',
      detection_sensitivity: 0.8,
      real_time: true
    };

    const mockFraudResponse = {
      analysis_id: 'fraud-123',
      status: 'initiated',
      message: 'Fraud detection started',
      transactions_analyzed: 1,
      anomalies_detected: 0,
      risk_level: 'pending'
    };

    it('should create fraud detection successfully', async () => {
      mockPost.mockResolvedValue({ data: mockFraudResponse });

      const result = await fintechService.createFraudDetection(mockFraudRequest);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/fintech/fraud-detection',
        mockFraudRequest
      );
      expect(result).toEqual(mockFraudResponse);
    });

    it('should validate fraud detection request', () => {
      // Valid request
      const validRequest: FraudDetectionRequest = {
        transaction_data: mockTransactionData,
        detection_sensitivity: 0.8
      };
      expect(fintechService.validateFraudDetectionRequest(validRequest)).toEqual([]);

      // Invalid request - no transaction data
      const invalidRequest1: FraudDetectionRequest = {
        transaction_data: []
      };
      const errors1 = fintechService.validateFraudDetectionRequest(invalidRequest1);
      expect(errors1).toContain('Transaction data is required');

      // Invalid request - too many transactions
      const invalidRequest2: FraudDetectionRequest = {
        transaction_data: new Array(10001).fill(mockTransactionData[0])
      };
      const errors2 = fintechService.validateFraudDetectionRequest(invalidRequest2);
      expect(errors2).toContain('Maximum 10,000 transactions per request');

      // Invalid request - invalid sensitivity
      const invalidRequest3: FraudDetectionRequest = {
        transaction_data: mockTransactionData,
        detection_sensitivity: 1.5
      };
      const errors3 = fintechService.validateFraudDetectionRequest(invalidRequest3);
      expect(errors3).toContain('Detection sensitivity must be between 0 and 1');
    });
  });

  // ==================== MARKET INTELLIGENCE TESTS ====================

  describe('Market Intelligence', () => {
    const mockMarketRequest: MarketIntelligenceRequest = {
      market_segment: 'fintech_payments',
      analysis_type: ['trends', 'volatility'],
      time_horizon: '1Y'
    };

    const mockMarketResponse = {
      analysis_id: 'market-123',
      status: 'initiated',
      message: 'Market intelligence started',
      market_segment: 'fintech_payments',
      analysis_types: ['trends', 'volatility'],
      time_horizon: '1Y'
    };

    it('should create market intelligence successfully', async () => {
      mockPost.mockResolvedValue({ data: mockMarketResponse });

      const result = await fintechService.createMarketIntelligence(mockMarketRequest);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/fintech/market-intelligence',
        mockMarketRequest
      );
      expect(result).toEqual(mockMarketResponse);
    });
  });

  // ==================== KYC VERIFICATION TESTS ====================

  describe('KYC Verification', () => {
    const mockKYCRequest: KYCVerificationRequest = {
      customer_id: 'customer-123',
      verification_level: 'standard',
      document_types: ['identity', 'address']
    };

    const mockKYCResponse = {
      analysis_id: 'kyc-123',
      status: 'initiated',
      message: 'KYC verification started',
      customer_id: 'customer-123',
      verification_level: 'standard',
      documents_required: ['identity', 'address']
    };

    it('should create KYC verification successfully', async () => {
      mockPost.mockResolvedValue({ data: mockKYCResponse });

      const result = await fintechService.createKYCVerification(mockKYCRequest);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/fintech/kyc-verification',
        mockKYCRequest
      );
      expect(result).toEqual(mockKYCResponse);
    });
  });

  // ==================== BUSINESS VALUE CALCULATION TESTS ====================

  describe('Business Value Calculation', () => {
    const mockBusinessValueRequest: BusinessValueCalculationRequest = {
      company_size: 'startup',
      industry: 'fintech',
      annual_revenue: 1000000,
      transaction_volume: 50000
    };

    const mockBusinessValueResponse = {
      analysis_id: 'business-value-123',
      status: 'initiated',
      message: 'Business value calculation started',
      company_size: 'startup',
      industry: 'fintech',
      estimated_annual_savings: 250000,
      estimated_fraud_prevention: 100000,
      estimated_compliance_savings: 150000,
      roi_percentage: 300,
      payback_period_months: 4
    };

    it('should create business value calculation successfully', async () => {
      mockPost.mockResolvedValue({ data: mockBusinessValueResponse });

      const result = await fintechService.createBusinessValueCalculation(mockBusinessValueRequest);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/fintech/business-value',
        mockBusinessValueRequest
      );
      expect(result).toEqual(mockBusinessValueResponse);
    });

    it('should validate business value request', () => {
      // Valid request
      const validRequest: BusinessValueCalculationRequest = {
        company_size: 'startup',
        industry: 'fintech',
        annual_revenue: 1000000
      };
      expect(fintechService.validateBusinessValueRequest(validRequest)).toEqual([]);

      // Invalid request - missing company size
      const invalidRequest1 = {
        company_size: undefined as any,
        industry: 'fintech'
      } as unknown as BusinessValueCalculationRequest;
      const errors1 = fintechService.validateBusinessValueRequest(invalidRequest1);
      expect(errors1).toContain('Company size is required');

      // Invalid request - missing industry
      const invalidRequest2: BusinessValueCalculationRequest = {
        company_size: 'startup',
        industry: ''
      };
      const errors2 = fintechService.validateBusinessValueRequest(invalidRequest2);
      expect(errors2).toContain('Industry is required');

      // Invalid request - negative revenue
      const invalidRequest3: BusinessValueCalculationRequest = {
        company_size: 'startup',
        industry: 'fintech',
        annual_revenue: -1000
      };
      const errors3 = fintechService.validateBusinessValueRequest(invalidRequest3);
      expect(errors3).toContain('Annual revenue must be non-negative');
    });
  });

  // ==================== DASHBOARD AND MONITORING TESTS ====================

  describe('Dashboard and Monitoring', () => {
    it('should get dashboard data with caching', async () => {
      const mockDashboardData = {
        summary: {
          active_analyses: 5,
          completed_today: 12,
          fraud_alerts: 2,
          compliance_issues: 1
        },
        recent_analyses: [],
        active_alerts: [],
        performance_metrics: {
          average_response_time: 3.2,
          success_rate: 0.98,
          fraud_detection_accuracy: 0.92,
          compliance_score: 0.95
        },
        business_value: {
          monthly_savings: 50000,
          fraud_prevented: 25000,
          compliance_cost_reduction: 25000,
          roi_percentage: 250
        }
      };

      mockGet.mockResolvedValue({ data: mockDashboardData });

      const result = await fintechService.getDashboardData();

      expect(mockGet).toHaveBeenCalledWith('/api/v1/fintech/dashboard');
      expect(result).toEqual(mockDashboardData);
    });

    it('should get financial alerts', async () => {
      const mockAlerts = [
        {
          alert_id: 'alert-001',
          alert_type: 'fraud',
          severity: 'high',
          title: 'Suspicious Transaction Detected',
          description: 'High-risk transaction pattern identified',
          created_at: '2024-01-15T14:30:00Z'
        }
      ];

      mockGet.mockResolvedValue({ data: mockAlerts });

      const result = await fintechService.getFinancialAlerts(10);

      expect(mockGet).toHaveBeenCalledWith('/api/v1/fintech/alerts?limit=10');
      expect(result).toEqual(mockAlerts);
    });

    it('should acknowledge alert', async () => {
      mockPost.mockResolvedValue({ data: {} });

      await fintechService.acknowledgeAlert('alert-001');

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/fintech/alerts/alert-001/acknowledge'
      );
    });
  });

  // ==================== UTILITY TESTS ====================

  describe('Utility Methods', () => {
    it('should cancel analysis and clear cache', async () => {
      mockDelete.mockResolvedValue({ data: {} });

      await fintechService.cancelAnalysis('analysis-123');

      expect(mockDelete).toHaveBeenCalledWith(
        '/api/v1/fintech/analysis/analysis-123'
      );
    });

    it('should get analysis status', async () => {
      const mockStatus = { status: 'completed', progress: 100 };
      mockGet.mockResolvedValue({ data: mockStatus });

      const result = await fintechService.getAnalysisStatus('analysis-123');

      expect(mockGet).toHaveBeenCalledWith(
        '/api/v1/fintech/analysis/analysis-123/status'
      );
      expect(result).toEqual(mockStatus);
    });

    it('should get analysis history', async () => {
      const mockHistory = {
        analyses: [],
        total: 0,
        page: 1,
        pageSize: 20
      };
      mockGet.mockResolvedValue({ data: mockHistory });

      const result = await fintechService.getAnalysisHistory(1, 20, 'risk_analysis');

      expect(mockGet).toHaveBeenCalledWith(
        '/api/v1/fintech/history?page=1&page_size=20&analysis_type=risk_analysis'
      );
      expect(result).toEqual(mockHistory);
    });
  });

  // ==================== FORMATTING TESTS ====================

  describe('Formatting Utilities', () => {
    it('should format currency correctly', () => {
      expect(fintechService.formatCurrency(1234567)).toBe('$1,234,567');
      expect(fintechService.formatCurrency(1234.56)).toBe('$1,235');
    });

    it('should format percentage correctly', () => {
      expect(fintechService.formatPercentage(75)).toBe('75.0%');
      expect(fintechService.formatPercentage(12.34)).toBe('12.3%');
    });

    it('should format large numbers correctly', () => {
      expect(fintechService.formatLargeNumber(1234567890)).toBe('1.2B');
      expect(fintechService.formatLargeNumber(1234567)).toBe('1.2M');
      expect(fintechService.formatLargeNumber(1234)).toBe('1.2K');
      expect(fintechService.formatLargeNumber(123)).toBe('123');
    });

    it('should get risk level colors correctly', () => {
      expect(fintechService.getRiskLevelColor('low')).toBe('#10B981');
      expect(fintechService.getRiskLevelColor('medium')).toBe('#F59E0B');
      expect(fintechService.getRiskLevelColor('high')).toBe('#EF4444');
      expect(fintechService.getRiskLevelColor('critical')).toBe('#DC2626');
      expect(fintechService.getRiskLevelColor('unknown')).toBe('#6B7280');
    });

    it('should get compliance status colors correctly', () => {
      expect(fintechService.getComplianceStatusColor('compliant')).toBe('#10B981');
      expect(fintechService.getComplianceStatusColor('non_compliant')).toBe('#EF4444');
      expect(fintechService.getComplianceStatusColor('requires_review')).toBe('#F59E0B');
      expect(fintechService.getComplianceStatusColor('pending')).toBe('#6B7280');
    });
  });

  // ==================== ERROR HANDLING TESTS ====================

  describe('Error Handling', () => {
    it('should handle API errors properly', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            detail: 'Invalid request data'
          }
        }
      };

      mockPost.mockRejectedValue(mockError);

      await expect(fintechService.createRiskAnalysis({
        entity_id: 'test',
        entity_type: 'test'
      })).rejects.toMatchObject({
        error_code: '400',
        message: 'Invalid request data'
      });
    });

    it('should handle network errors', async () => {
      const mockError = new Error('Network error');
      mockGet.mockRejectedValue(mockError);

      await expect(fintechService.getDashboardData()).rejects.toMatchObject({
        error_code: 'UNKNOWN_ERROR',
        message: 'Network error'
      });
    });
  });

  // ==================== CACHE TESTS ====================

  describe('Cache Management', () => {
    it('should cache and retrieve data correctly', async () => {
      const mockData = { test: 'data' };
      mockGet.mockResolvedValue({ data: mockData });

      // First call should hit API
      await fintechService.getRiskAnalysisResult('test-123');
      expect(mockGet).toHaveBeenCalledTimes(1);

      // Second call should use cache
      await fintechService.getRiskAnalysisResult('test-123');
      expect(mockGet).toHaveBeenCalledTimes(1);
    });

    it('should clear cache correctly', async () => {
      const mockData = { test: 'data' };
      mockGet.mockResolvedValue({ data: mockData });

      // Cache some data
      await fintechService.getRiskAnalysisResult('test-123');
      
      // Clear cache
      fintechService.clearCache();
      
      // Next call should hit API again
      await fintechService.getRiskAnalysisResult('test-123');
      expect(mockGet).toHaveBeenCalledTimes(2);
    });
  });
});
