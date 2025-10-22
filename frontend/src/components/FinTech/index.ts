/**
 * FinTech Dashboard Components Export
 * Centralized exports for all RiskIntel360 dashboard components
 */

export { default as RiskIntelDashboard } from './RiskIntelDashboard';
export { default as ComplianceMonitoringDashboard } from './ComplianceMonitoringDashboard';
export { default as FraudDetectionDashboard } from './FraudDetectionDashboard';
export { default as MarketIntelligenceDashboard } from './MarketIntelligenceDashboard';
export { default as KYCVerificationDashboard } from './KYCVerificationDashboard';
export { default as BusinessValueDashboard } from './BusinessValueDashboard';
export { default as PerformanceDashboard } from './PerformanceDashboard';
export { default as CompetitionDemoDashboard } from './CompetitionDemoDashboard';

// Re-export types for convenience
export type {
  ComplianceAssessment,
  FraudDetectionResult,
  MarketIntelligence,
  KYCVerificationResult,
  FinTechDashboardData,
  BusinessValueCalculation,
  FinancialAlert,
} from '../../types/fintech';