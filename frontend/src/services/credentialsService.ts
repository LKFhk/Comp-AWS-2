import { apiService } from './api';

export interface AWSCredentials {
  access_key_id: string;
  secret_access_key: string;
  region: string;
}

export interface ExternalAPIKey {
  service_name: string;
  api_key: string;
  endpoint_url?: string;
  additional_config?: Record<string, any>;
}

export interface CredentialValidationResponse {
  valid: boolean;
  service_name: string;
  region?: string;
  error_message?: string;
  permissions?: string[];
  cost_estimate?: any;
}

export interface CostEstimationRequest {
  profile: string;
  business_concept: string;
  analysis_scope: string[];
  target_market: string;
}

export interface BudgetLimits {
  max_daily_spend: number;
  max_monthly_spend: number;
  max_per_validation: number;
  alert_threshold_percent: number;
  auto_throttle_enabled: boolean;
}

export interface BudgetUsage {
  limits: BudgetLimits | null;
  usage: {
    daily: number;
    monthly: number;
    validations_today: number;
    validations_this_month: number;
  };
  usage_percentages: {
    daily: number;
    monthly: number;
  };
  alerts: Array<{
    type: string;
    message: string;
    severity: string;
  }>;
}

export interface ConfiguredServices {
  aws_services: string[];
  external_services: string[];
  total_count: number;
}

class CredentialsService {
  private baseUrl = '/api/v1/credentials';

  async setupAWSCredentials(credentials: AWSCredentials): Promise<CredentialValidationResponse> {
    try {
      const response = await apiService.post(`${this.baseUrl}/aws/setup`, credentials);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to setup AWS credentials');
    }
  }

  async setupExternalAPIKey(apiKey: ExternalAPIKey): Promise<CredentialValidationResponse> {
    try {
      const response = await apiService.post(`${this.baseUrl}/external/setup`, apiKey);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to setup external API key');
    }
  }

  async listConfiguredServices(): Promise<ConfiguredServices> {
    try {
      const response = await apiService.get(`${this.baseUrl}/list`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to list configured services');
    }
  }

  async validateServiceCredentials(serviceName: string): Promise<CredentialValidationResponse> {
    try {
      const response = await apiService.post(`${this.baseUrl}/validate/${serviceName}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to validate credentials');
    }
  }

  async deleteServiceCredentials(serviceName: string): Promise<{ message: string }> {
    try {
      const response = await apiService.delete(`${this.baseUrl}/${serviceName}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to delete credentials');
    }
  }

  async estimateValidationCost(request: CostEstimationRequest): Promise<any> {
    try {
      const response = await apiService.post(`${this.baseUrl}/cost/estimate`, request);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to estimate cost');
    }
  }

  async setBudgetLimits(limits: BudgetLimits): Promise<{ message: string; limits: BudgetLimits }> {
    try {
      const response = await apiService.post(`${this.baseUrl}/budget/set`, limits);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to set budget limits');
    }
  }

  async getCurrentBudgetUsage(): Promise<BudgetUsage> {
    try {
      const response = await apiService.get(`${this.baseUrl}/budget/current`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get budget usage');
    }
  }

  // Helper methods for validation
  validateAWSCredentials(credentials: AWSCredentials): string[] {
    const errors: string[] = [];

    if (!credentials.access_key_id) {
      errors.push('Access Key ID is required');
    } else if (!credentials.access_key_id.startsWith('AKIA') && !credentials.access_key_id.startsWith('ASIA')) {
      errors.push('Invalid Access Key ID format');
    }

    if (!credentials.secret_access_key) {
      errors.push('Secret Access Key is required');
    } else if (credentials.secret_access_key.length < 16) {
      errors.push('Secret Access Key is too short');
    }

    if (!credentials.region) {
      errors.push('Region is required');
    }

    return errors;
  }

  validateExternalAPIKey(apiKey: ExternalAPIKey): string[] {
    const errors: string[] = [];

    if (!apiKey.service_name) {
      errors.push('Service name is required');
    }

    if (!apiKey.api_key) {
      errors.push('API key is required');
    } else if (apiKey.api_key.length < 8) {
      errors.push('API key is too short');
    }

    return errors;
  }

  validateBudgetLimits(limits: BudgetLimits): string[] {
    const errors: string[] = [];

    if (limits.max_daily_spend <= 0) {
      errors.push('Daily spend limit must be greater than 0');
    }

    if (limits.max_monthly_spend <= 0) {
      errors.push('Monthly spend limit must be greater than 0');
    }

    if (limits.max_per_validation <= 0) {
      errors.push('Per-validation limit must be greater than 0');
    }

    if (limits.alert_threshold_percent < 0 || limits.alert_threshold_percent > 100) {
      errors.push('Alert threshold must be between 0 and 100');
    }

    if (limits.max_daily_spend > limits.max_monthly_spend) {
      errors.push('Daily limit cannot exceed monthly limit');
    }

    return errors;
  }

  // Utility methods
  maskAPIKey(apiKey: string): string {
    if (apiKey.length <= 8) {
      return '*'.repeat(apiKey.length);
    }
    return apiKey.substring(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.substring(apiKey.length - 4);
  }

  getServiceDisplayName(serviceName: string): string {
    const displayNames: Record<string, string> = {
      'aws': 'Amazon Web Services',
      'bedrock': 'Amazon Bedrock',
      'alpha_vantage': 'Alpha Vantage',
      'news_api': 'News API',
      'twitter_api': 'Twitter API',
      'reddit_api': 'Reddit API',
      'crunchbase': 'Crunchbase',
      'pitchbook': 'PitchBook',
    };

    return displayNames[serviceName] || serviceName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  getServiceIcon(serviceName: string): string {
    const icons: Record<string, string> = {
      'aws': '☁️',
      'bedrock': '🤖',
      'alpha_vantage': '📈',
      'news_api': '📰',
      'twitter_api': '🐦',
      'reddit_api': '🔴',
      'crunchbase': '🏢',
      'pitchbook': '💼',
    };

    return icons[serviceName] || '🔑';
  }

  getCostProfileDescription(profile: string): string {
    const descriptions: Record<string, string> = {
      'demo': 'Optimized for demos and testing with minimal costs (~60% savings)',
      'development': 'Balanced performance and cost for development (~20% savings)',
      'production': 'Maximum performance for production workloads (full cost)',
    };

    return descriptions[profile] || 'Unknown profile';
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(amount);
  }

  formatPercentage(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value / 100);
  }
}

export const credentialsService = new CredentialsService();