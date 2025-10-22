/**
 * TypeScript interfaces for RiskIntel360 Fintech data models
 * Provides type safety for all fintech API interactions
 */

// Enums
export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

export enum ComplianceStatus {
  COMPLIANT = 'compliant',
  NON_COMPLIANT = 'non_compliant',
  REQUIRES_REVIEW = 'requires_review',
  PENDING = 'pending'
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum FraudRiskLevel {
  MINIMAL = 'minimal',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum MarketTrend {
  BULLISH = 'bullish',
  BEARISH = 'bearish',
  NEUTRAL = 'neutral',
  VOLATILE = 'volatile'
}

// Request Models
export interface RiskAnalysisRequest {
  entity_id: string;
  entity_type: string;
  analysis_scope?: string[];
  priority?: Priority;
  custom_parameters?: Record<string, any>;
}

export interface ComplianceCheckRequest {
  business_type: string;
  jurisdiction?: string;
  regulations?: string[];
  priority?: Priority;
}

export interface FraudDetectionRequest {
  transaction_data: TransactionData[];
  customer_id?: string;
  detection_sensitivity?: number;
  real_time?: boolean;
}

export interface MarketIntelligenceRequest {
  market_segment: string;
  analysis_type?: string[];
  time_horizon?: string;
  data_sources?: string[];
}

export interface KYCVerificationRequest {
  customer_id: string;
  verification_level?: string;
  document_types?: string[];
  risk_tolerance?: string;
}

export interface BusinessValueCalculationRequest {
  company_size: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  industry: string;
  annual_revenue?: number;
  transaction_volume?: number;
  compliance_requirements?: string[];
  current_fraud_losses?: number;
  current_compliance_costs?: number;
  analysis_scope?: string[];
}

// Transaction Data Model
export interface TransactionData {
  transaction_id: string;
  amount: number;
  currency: string;
  merchant: string;
  timestamp: string;
  payment_method: string;
  location: string;
  merchant_category: string;
  customer_id?: string;
  additional_data?: Record<string, any>;
}

// Response Models
export interface AnalysisResponse {
  analysis_id: string;
  status: string;
  message: string;
  estimated_completion?: string;
  progress_url?: string;
}

export interface RiskAnalysisResponse extends AnalysisResponse {
  entity_id: string;
  entity_type: string;
  analysis_scope: string[];
}

export interface ComplianceCheckResponse extends AnalysisResponse {
  business_type: string;
  jurisdiction: string;
  regulations_checked: string[];
}

export interface FraudDetectionResponse extends AnalysisResponse {
  transactions_analyzed: number;
  anomalies_detected: number;
  risk_level: string;
}

export interface MarketIntelligenceResponse extends AnalysisResponse {
  market_segment: string;
  analysis_types: string[];
  time_horizon: string;
}

export interface KYCVerificationResponse extends AnalysisResponse {
  customer_id: string;
  verification_level: string;
  documents_required: string[];
}

export interface BusinessValueCalculationResponse extends AnalysisResponse {
  company_size: string;
  industry: string;
  estimated_annual_savings: number;
  estimated_fraud_prevention: number;
  estimated_compliance_savings: number;
  roi_percentage: number;
  payback_period_months: number;
}

// Result Models
export interface ComplianceAssessment {
  regulation_id: string;
  regulation_name: string;
  compliance_status: ComplianceStatus;
  risk_level: RiskLevel;
  requirements: string[];
  gaps: string[];
  remediation_plan: Record<string, any>;
  confidence_score: number;
  ai_reasoning: string;
}

export interface FraudDetectionResult {
  transaction_id: string;
  fraud_probability: number;
  anomaly_score: number;
  detection_methods: string[];
  risk_factors: string[];
  recommended_action: string;
  false_positive_likelihood: number;
  ml_explanation: string;
  llm_interpretation: string;
}

export interface MarketIntelligence {
  market_segment: string;
  trend_direction: MarketTrend;
  volatility_level: number;
  key_drivers: string[];
  risk_factors: string[];
  opportunities: string[];
  data_sources: string[];
  confidence_score: number;
  ai_insights: string;
}

export interface KYCVerificationResult {
  customer_id: string;
  verification_status: string;
  risk_score: number;
  verification_level: string;
  documents_verified: string[];
  sanctions_screening: Record<string, any>;
  pep_screening: Record<string, any>;
  adverse_media_screening: Record<string, any>;
  recommended_action: string;
  confidence_score: number;
}

export interface RiskAssessmentResult {
  entity_id: string;
  overall_risk_score: number;
  risk_level: RiskLevel;
  risk_categories: Record<string, any>;
  key_risk_factors: string[];
  mitigation_recommendations: string[];
  confidence_score: number;
  ai_reasoning: string;
}

export interface BusinessValueCalculation {
  calculation_id: string;
  company_size: string;
  industry: string;
  annual_revenue: number;
  
  // Fraud Prevention Value
  fraud_prevention_value: {
    current_annual_losses: number;
    prevented_losses: number;
    prevention_rate: number;
    annual_savings: number;
  };
  
  // Compliance Cost Savings
  compliance_savings: {
    current_annual_costs: number;
    automated_savings: number;
    automation_rate: number;
    annual_savings: number;
  };
  
  // Risk Reduction Value
  risk_reduction_value: {
    current_risk_exposure: number;
    reduced_exposure: number;
    reduction_percentage: number;
    annual_value: number;
  };
  
  // Total Business Impact
  total_impact: {
    total_annual_savings: number;
    implementation_cost: number;
    roi_percentage: number;
    payback_period_months: number;
    net_present_value: number;
  };
  
  // Confidence and Methodology
  confidence_score: number;
  calculation_methodology: string;
  assumptions: string[];
  risk_factors: string[];
}

// Progress and Status Models
export interface ProgressUpdate {
  analysis_id: string;
  status: string;
  progress_percentage: number;
  current_agent?: string;
  message?: string;
  agent_results?: Record<string, any>;
  estimated_completion?: string;
}

export interface FinancialAlert {
  alert_id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  entity_id?: string;
  created_at: string;
  resolved_at?: string;
  metadata?: Record<string, any>;
}

// Dashboard Models
export interface FinTechDashboardData {
  summary: {
    active_analyses: number;
    completed_today: number;
    fraud_alerts: number;
    compliance_issues: number;
  };
  
  recent_analyses: AnalysisResponse[];
  active_alerts: FinancialAlert[];
  
  performance_metrics: {
    average_response_time: number;
    success_rate: number;
    fraud_detection_accuracy: number;
    compliance_score: number;
  };
  
  business_value: {
    monthly_savings: number;
    fraud_prevented: number;
    compliance_cost_reduction: number;
    roi_percentage: number;
  };
}

// Error Models
export interface FinTechApiError {
  error_code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

// Cache Models
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

export interface ServiceConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  cacheTimeout: number;
}