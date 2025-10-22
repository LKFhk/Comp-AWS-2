/**
 * RiskIntel360 Fintech Service
 * Provides comprehensive API integration for all fintech endpoints including
 * risk analysis, compliance checks, fraud detection, market intelligence, KYC verification,
 * and business value calculations.
 */

import { apiClient } from './api';
import type {
  // Request Types
  RiskAnalysisRequest,
  ComplianceCheckRequest,
  FraudDetectionRequest,
  MarketIntelligenceRequest,
  KYCVerificationRequest,
  BusinessValueCalculationRequest,
  
  // Response Types
  RiskAnalysisResponse,
  ComplianceCheckResponse,
  FraudDetectionResponse,
  MarketIntelligenceResponse,
  KYCVerificationResponse,
  BusinessValueCalculationResponse,
  
  // Result Types
  ComplianceAssessment,
  FraudDetectionResult,
  MarketIntelligence,
  KYCVerificationResult,
  RiskAssessmentResult,
  BusinessValueCalculation,
  
  // Utility Types
  ProgressUpdate,
  FinancialAlert,
  FinTechDashboardData,
  FinTechApiError,
  CacheEntry,
  ServiceConfig
} from '../types/fintech';

/**
 * Fintech Service Class
 * Handles all fintech-related API calls with caching, error handling, and retry logic
 */
class FintechService {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private config: ServiceConfig;

  constructor(config?: Partial<ServiceConfig>) {
    this.config = {
      baseURL: '/api/v1/fintech',
      timeout: 30000,
      retryAttempts: 3,
      cacheTimeout: 5 * 60 * 1000, // 5 minutes default cache
      ...config
    };
  }

  // ==================== RISK ANALYSIS ====================

  /**
   * Create comprehensive financial risk assessment
   * Analyzes credit, market, operational, regulatory, and fraud risks
   */
  async createRiskAnalysis(request: RiskAnalysisRequest): Promise<RiskAnalysisResponse> {
    try {
      const response = await apiClient.post(`${this.config.baseURL}/risk-analysis`, request);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to create risk analysis');
    }
  }

  /**
   * Get risk analysis result
   */
  async getRiskAnalysisResult(analysisId: string): Promise<RiskAssessmentResult> {
    const cacheKey = `risk-result-${analysisId}`;
    const cached = this.getFromCache<RiskAssessmentResult>(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.config.baseURL}/risk-analysis/${analysisId}/result`);
      const result = response.data;
      this.setCache(cacheKey, result, this.config.cacheTimeout);
      return result;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get risk analysis result');
    }
  }

  /**
   * Get risk analysis progress
   */
  async getRiskAnalysisProgress(analysisId: string): Promise<ProgressUpdate> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/risk-analysis/${analysisId}/progress`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get risk analysis progress');
    }
  }

  // ==================== COMPLIANCE CHECKS ====================

  /**
   * Create regulatory compliance analysis
   * Monitors SEC, FINRA, CFPB, and other regulatory requirements
   */
  async createComplianceCheck(request: ComplianceCheckRequest): Promise<ComplianceCheckResponse> {
    try {
      const response = await apiClient.post(`${this.config.baseURL}/compliance-check`, request);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to create compliance check');
    }
  }

  /**
   * Convenience method: Check compliance (alias for createComplianceCheck)
   */
  async checkCompliance(request: ComplianceCheckRequest): Promise<ComplianceCheckResponse> {
    return this.createComplianceCheck(request);
  }

  /**
   * Get compliance check result
   */
  async getComplianceCheckResult(analysisId: string): Promise<ComplianceAssessment[]> {
    const cacheKey = `compliance-result-${analysisId}`;
    const cached = this.getFromCache<ComplianceAssessment[]>(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.config.baseURL}/compliance-check/${analysisId}/result`);
      const result = response.data;
      this.setCache(cacheKey, result, this.config.cacheTimeout);
      return result;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get compliance check result');
    }
  }

  /**
   * Get compliance check progress
   */
  async getComplianceCheckProgress(analysisId: string): Promise<ProgressUpdate> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/compliance-check/${analysisId}/progress`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get compliance check progress');
    }
  }

  // ==================== FRAUD DETECTION ====================

  /**
   * Create advanced fraud detection analysis
   * Uses unsupervised ML and AI reasoning for real-time fraud pattern recognition
   */
  async createFraudDetection(request: FraudDetectionRequest): Promise<FraudDetectionResponse> {
    try {
      const response = await apiClient.post(`${this.config.baseURL}/fraud-detection`, request);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to create fraud detection analysis');
    }
  }

  /**
   * Convenience method: Detect fraud (alias for createFraudDetection)
   */
  async detectFraud(request: FraudDetectionRequest): Promise<FraudDetectionResponse> {
    return this.createFraudDetection(request);
  }

  /**
   * Get fraud detection result
   */
  async getFraudDetectionResult(analysisId: string): Promise<FraudDetectionResult[]> {
    const cacheKey = `fraud-result-${analysisId}`;
    const cached = this.getFromCache<FraudDetectionResult[]>(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.config.baseURL}/fraud-detection/${analysisId}/result`);
      const result = response.data;
      this.setCache(cacheKey, result, this.config.cacheTimeout);
      return result;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get fraud detection result');
    }
  }

  /**
   * Get fraud detection progress
   */
  async getFraudDetectionProgress(analysisId: string): Promise<ProgressUpdate> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/fraud-detection/${analysisId}/progress`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get fraud detection progress');
    }
  }

  // ==================== MARKET INTELLIGENCE ====================

  /**
   * Create financial market intelligence analysis
   * Analyzes market trends, volatility, opportunities, and risks using public data
   */
  async createMarketIntelligence(request: MarketIntelligenceRequest): Promise<MarketIntelligenceResponse> {
    try {
      const response = await apiClient.post(`${this.config.baseURL}/market-intelligence`, request);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to create market intelligence analysis');
    }
  }

  /**
   * Convenience method: Get market intelligence (alias for createMarketIntelligence)
   */
  async getMarketIntelligence(request: MarketIntelligenceRequest): Promise<MarketIntelligenceResponse> {
    return this.createMarketIntelligence(request);
  }

  /**
   * Get market intelligence result
   */
  async getMarketIntelligenceResult(analysisId: string): Promise<MarketIntelligence> {
    const cacheKey = `market-result-${analysisId}`;
    const cached = this.getFromCache<MarketIntelligence>(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.config.baseURL}/market-intelligence/${analysisId}/result`);
      const result = response.data;
      this.setCache(cacheKey, result, this.config.cacheTimeout);
      return result;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get market intelligence result');
    }
  }

  /**
   * Get market intelligence progress
   */
  async getMarketIntelligenceProgress(analysisId: string): Promise<ProgressUpdate> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/market-intelligence/${analysisId}/progress`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get market intelligence progress');
    }
  }

  // ==================== KYC VERIFICATION ====================

  /**
   * Create KYC verification workflow
   * Automated customer verification with AI-powered risk assessment
   */
  async createKYCVerification(request: KYCVerificationRequest): Promise<KYCVerificationResponse> {
    try {
      const response = await apiClient.post(`${this.config.baseURL}/kyc-verification`, request);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to create KYC verification');
    }
  }

  /**
   * Convenience method: Verify KYC (alias for createKYCVerification)
   */
  async verifyKYC(request: KYCVerificationRequest): Promise<KYCVerificationResponse> {
    return this.createKYCVerification(request);
  }

  /**
   * Get KYC verification result
   */
  async getKYCVerificationResult(analysisId: string): Promise<KYCVerificationResult> {
    const cacheKey = `kyc-result-${analysisId}`;
    const cached = this.getFromCache<KYCVerificationResult>(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.config.baseURL}/kyc-verification/${analysisId}/result`);
      const result = response.data;
      this.setCache(cacheKey, result, this.config.cacheTimeout);
      return result;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get KYC verification result');
    }
  }

  /**
   * Get KYC verification progress
   */
  async getKYCVerificationProgress(analysisId: string): Promise<ProgressUpdate> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/kyc-verification/${analysisId}/progress`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get KYC verification progress');
    }
  }

  // ==================== BUSINESS VALUE CALCULATION ====================

  /**
   * Create business value calculation
   * Calculates fraud prevention value, compliance savings, and ROI
   */
  async createBusinessValueCalculation(request: BusinessValueCalculationRequest): Promise<BusinessValueCalculationResponse> {
    try {
      const response = await apiClient.post(`${this.config.baseURL}/business-value`, request);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to create business value calculation');
    }
  }

  /**
   * Get business value calculation result
   */
  async getBusinessValueCalculationResult(analysisId: string): Promise<BusinessValueCalculation> {
    const cacheKey = `business-value-result-${analysisId}`;
    const cached = this.getFromCache<BusinessValueCalculation>(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.config.baseURL}/business-value/${analysisId}/result`);
      const result = response.data;
      this.setCache(cacheKey, result, this.config.cacheTimeout);
      return result;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get business value calculation result');
    }
  }

  /**
   * Get business value calculation progress
   */
  async getBusinessValueCalculationProgress(analysisId: string): Promise<ProgressUpdate> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/business-value/${analysisId}/progress`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get business value calculation progress');
    }
  }

  // ==================== DASHBOARD AND MONITORING ====================

  /**
   * Get fintech dashboard data
   * Comprehensive overview of all fintech activities and metrics
   */
  async getDashboardData(): Promise<FinTechDashboardData> {
    const cacheKey = 'dashboard-data';
    const cached = this.getFromCache<FinTechDashboardData>(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.config.baseURL}/dashboard`);
      const result = response.data;
      this.setCache(cacheKey, result, 60000); // Cache for 1 minute
      return result;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get dashboard data');
    }
  }

  /**
   * Get financial alerts
   */
  async getFinancialAlerts(limit: number = 50): Promise<FinancialAlert[]> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/alerts?limit=${limit}`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get financial alerts');
    }
  }

  /**
   * Acknowledge financial alert
   */
  async acknowledgeAlert(alertId: string): Promise<void> {
    try {
      await apiClient.post(`${this.config.baseURL}/alerts/${alertId}/acknowledge`);
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to acknowledge alert');
    }
  }

  // ==================== UTILITY METHODS ====================

  /**
   * Cancel any ongoing analysis
   */
  async cancelAnalysis(analysisId: string): Promise<void> {
    try {
      await apiClient.delete(`${this.config.baseURL}/analysis/${analysisId}`);
      // Clear related cache entries
      this.clearCacheByPattern(analysisId);
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to cancel analysis');
    }
  }

  /**
   * Get analysis status (works for any analysis type)
   */
  async getAnalysisStatus(analysisId: string): Promise<{ status: string; progress: number }> {
    try {
      const response = await apiClient.get(`${this.config.baseURL}/analysis/${analysisId}/status`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get analysis status');
    }
  }

  /**
   * Get user's analysis history
   */
  async getAnalysisHistory(
    page: number = 1, 
    pageSize: number = 20, 
    analysisType?: string
  ): Promise<{
    analyses: any[];
    total: number;
    page: number;
    pageSize: number;
  }> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      
      if (analysisType) {
        params.append('analysis_type', analysisType);
      }

      const response = await apiClient.get(`${this.config.baseURL}/history?${params}`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Failed to get analysis history');
    }
  }

  // ==================== CACHE MANAGEMENT ====================

  /**
   * Get data from cache if available and not expired
   */
  private getFromCache<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /**
   * Set data in cache with expiry
   */
  private setCache<T>(key: string, data: T, ttl: number): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + ttl
    };
    this.cache.set(key, entry);
  }

  /**
   * Clear cache entries matching pattern
   */
  private clearCacheByPattern(pattern: string): void {
    const keys = Array.from(this.cache.keys());
    for (const key of keys) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Clear all cache
   */
  public clearCache(): void {
    this.cache.clear();
  }

  // ==================== ERROR HANDLING ====================

  /**
   * Handle API errors with proper error formatting
   */
  private handleApiError(error: any, defaultMessage: string): FinTechApiError {
    const apiError: FinTechApiError = {
      error_code: error.response?.status?.toString() || 'UNKNOWN_ERROR',
      message: error.response?.data?.detail || error.message || defaultMessage,
      details: error.response?.data || {},
      timestamp: new Date().toISOString()
    };

    console.error('Fintech API Error:', apiError);
    return apiError;
  }

  // ==================== VALIDATION HELPERS ====================

  /**
   * Validate risk analysis request
   */
  public validateRiskAnalysisRequest(request: RiskAnalysisRequest): string[] {
    const errors: string[] = [];

    if (!request.entity_id?.trim()) {
      errors.push('Entity ID is required');
    }

    if (!request.entity_type?.trim()) {
      errors.push('Entity type is required');
    }

    if (request.analysis_scope && request.analysis_scope.length === 0) {
      errors.push('At least one analysis scope must be selected');
    }

    return errors;
  }

  /**
   * Validate fraud detection request
   */
  public validateFraudDetectionRequest(request: FraudDetectionRequest): string[] {
    const errors: string[] = [];

    if (!request.transaction_data || request.transaction_data.length === 0) {
      errors.push('Transaction data is required');
    }

    if (request.transaction_data && request.transaction_data.length > 10000) {
      errors.push('Maximum 10,000 transactions per request');
    }

    if (request.detection_sensitivity !== undefined && 
        (request.detection_sensitivity < 0 || request.detection_sensitivity > 1)) {
      errors.push('Detection sensitivity must be between 0 and 1');
    }

    return errors;
  }

  /**
   * Validate business value calculation request
   */
  public validateBusinessValueRequest(request: BusinessValueCalculationRequest): string[] {
    const errors: string[] = [];

    if (!request.company_size) {
      errors.push('Company size is required');
    }

    if (!request.industry?.trim()) {
      errors.push('Industry is required');
    }

    if (request.annual_revenue !== undefined && request.annual_revenue < 0) {
      errors.push('Annual revenue must be non-negative');
    }

    if (request.transaction_volume !== undefined && request.transaction_volume < 0) {
      errors.push('Transaction volume must be non-negative');
    }

    return errors;
  }

  // ==================== UTILITY FORMATTERS ====================

  /**
   * Format currency values
   */
  public formatCurrency(amount: number, currency: string = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }

  /**
   * Format percentage values
   */
  public formatPercentage(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value / 100);
  }

  /**
   * Format large numbers with appropriate suffixes
   */
  public formatLargeNumber(num: number): string {
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toString();
  }

  /**
   * Get risk level color for UI
   */
  public getRiskLevelColor(riskLevel: string): string {
    const colors: Record<string, string> = {
      'low': '#10B981',      // Green
      'medium': '#F59E0B',   // Yellow
      'high': '#EF4444',     // Red
      'critical': '#DC2626'  // Dark Red
    };
    return colors[riskLevel.toLowerCase()] || '#6B7280'; // Gray default
  }

  /**
   * Get compliance status color for UI
   */
  public getComplianceStatusColor(status: string): string {
    const colors: Record<string, string> = {
      'compliant': '#10B981',        // Green
      'non_compliant': '#EF4444',    // Red
      'requires_review': '#F59E0B',  // Yellow
      'pending': '#6B7280'           // Gray
    };
    return colors[status.toLowerCase()] || '#6B7280';
  }
}

// Create singleton instance
const fintechServiceInstance = new FintechService();

// Export as named export
export { fintechServiceInstance as fintechService };