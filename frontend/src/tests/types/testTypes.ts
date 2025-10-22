/**
 * TypeScript type definitions for test utilities
 * Provides type safety for all test data and mock functions
 */

import type {
  FinTechDashboardData,
  ComplianceAssessment,
  FraudDetectionResult,
  MarketIntelligence,
  BusinessValueCalculation,
  FinancialAlert,
  AnalysisResponse,
  ProgressUpdate
} from '../../types/fintech';

// Mock API Response Types
export interface MockApiResponse<T = any> {
  ok: boolean;
  status: number;
  statusText: string;
  json: () => Promise<T>;
  text?: () => Promise<string>;
  headers?: Headers;
}

// Mock Fetch Function Type
export type MockFetchFunction = (
  url: string | Request | URL,
  init?: RequestInit
) => Promise<MockApiResponse>;

// Test Data Types
export interface TestDashboardData extends FinTechDashboardData {
  // Additional test-specific fields if needed
}

export interface TestComplianceData {
  status: string;
  score: number;
  lastCheck: string;
  regulations: Array<{
    name: string;
    status: string;
    lastUpdate: string;
  }>;
}

export interface TestFraudData {
  detectedCases: number;
  preventedLosses: number;
  falsePositiveRate: number;
  accuracy: number;
  recentCases: Array<{
    id: string;
    amount: number;
    confidence: number;
    status: string;
    timestamp: string;
  }>;
}

export interface TestMarketData {
  trends: Array<{
    date: string;
    value: number;
  }>;
  indicators: {
    volatility: number;
    momentum: number;
    sentiment: number;
  };
}

export interface TestExecutionData {
  id: string;
  status: string;
  startTime: string;
  endTime: string;
  results: {
    regulatory_compliance: { status: string; confidence: number };
    fraud_detection: { status: string; confidence: number };
    risk_assessment: { status: string; confidence: number };
  };
  metrics: {
    totalValue: number;
    processingTime: number;
    agentsUsed: number;
  };
}

// Mock Fetch Responses Type
export interface MockFetchResponses {
  '/api/v1/dashboard/data': TestDashboardData;
  '/api/v1/compliance/status': TestComplianceData;
  '/api/v1/fraud/analytics': TestFraudData;
  '/api/v1/market/data': TestMarketData;
  '/api/v1/demo/executions': TestExecutionData[];
  '/api/v1/demo/executions/exec-123/results': TestExecutionData;
  '/api/v1/demo/impact-dashboard': {
    totalValue: number;
    metrics: TestDashboardData['performance_metrics'];
  };
}

// Test Utility Function Types
export type SetupFetchMocksFunction = () => void;
export type ResetFetchMocksFunction = () => void;

// Component Props Types for Testing
export interface TestComponentProps {
  onNavigateTo?: (dashboard: string) => void;
  refreshInterval?: number;
  enableAdvancedFeatures?: boolean;
}

// Mock Service Types
export interface MockFintechService {
  getDashboardData: jest.MockedFunction<() => Promise<FinTechDashboardData>>;
  getRiskAnalysisResult: jest.MockedFunction<(id: string) => Promise<any>>;
  getComplianceCheckResult: jest.MockedFunction<(id: string) => Promise<ComplianceAssessment[]>>;
  getFinancialAlerts: jest.MockedFunction<(limit?: number) => Promise<FinancialAlert[]>>;
  acknowledgeAlert: jest.MockedFunction<(alertId: string) => Promise<void>>;
  clearCache: jest.MockedFunction<() => void>;
  formatCurrency: jest.MockedFunction<(value: number) => string>;
  formatPercentage: jest.MockedFunction<(value: number) => string>;
  formatLargeNumber: jest.MockedFunction<(value: number) => string>;
  getRiskLevelColor: jest.MockedFunction<(level: string) => string>;
  getComplianceStatusColor: jest.MockedFunction<(status: string) => string>;
}

// Test Assertion Helpers
export interface TestAssertions {
  expectElementToBeInDocument: (text: string | RegExp) => void;
  expectElementNotToBeInDocument: (text: string | RegExp) => void;
  expectButtonToBeClickable: (label: string) => void;
  expectLoadingState: () => void;
  expectErrorState: (message?: string) => void;
}

// Test Timeout Configuration
export interface TestTimeoutConfig {
  default: number;
  extended: number;
  short: number;
}

export const TEST_TIMEOUTS: TestTimeoutConfig = {
  default: 5000,
  extended: 10000,
  short: 3000
};

// Test Data Factories
export type CreateMockDashboardData = (overrides?: Partial<TestDashboardData>) => TestDashboardData;
export type CreateMockAlert = (overrides?: Partial<FinancialAlert>) => FinancialAlert;
export type CreateMockAnalysis = (overrides?: Partial<AnalysisResponse>) => AnalysisResponse;

// Export all types
export type {
  FinTechDashboardData,
  ComplianceAssessment,
  FraudDetectionResult,
  MarketIntelligence,
  BusinessValueCalculation,
  FinancialAlert,
  AnalysisResponse,
  ProgressUpdate
};
