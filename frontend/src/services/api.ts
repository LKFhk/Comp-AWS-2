import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { logInfo, logError, logWarn, logDebug } from '../utils/logger';

// Create axios instance with base configuration
export const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    const status = error.response?.status;
    const url = error.config?.url;
    
    if (status === 401) {
      // Only redirect to login if we're not already on the login page
      // and if this isn't the login endpoint itself
      const isLoginEndpoint = url?.includes('/auth/login');
      const isOnLoginPage = window.location.pathname === '/login';
      
      if (!isLoginEndpoint && !isOnLoginPage) {
        // Unauthorized - clear token and redirect to login
        localStorage.removeItem('auth_token');
        delete apiClient.defaults.headers.common['Authorization'];
        
        // Use a small delay to prevent race conditions
        setTimeout(() => {
          window.location.href = '/login';
        }, 100);
      }
    }
    
    return Promise.reject(error);
  }
);

// API Types
export interface ValidationRequest {
  financial_institution_profile: string;
  regulatory_jurisdiction: string;
  analysis_scope: string[];
  priority: 'low' | 'medium' | 'high';
  custom_parameters?: Record<string, any>;
  // Backward compatibility aliases
  business_concept?: string;
  target_market?: string;
}

export interface ValidationResponse {
  id: string;
  user_id: string;
  financial_institution_profile: string;
  regulatory_jurisdiction: string;
  analysis_scope: string[];
  priority: string;
  status: string;
  created_at: string;
  estimated_completion?: string;
  progress_url?: string;
  // Backward compatibility aliases
  business_concept?: string;
  target_market?: string;
}

export interface ValidationResult {
  request_id: string;
  overall_score: number;
  confidence_level: number;
  status: string;
  market_analysis?: any;
  competitive_analysis?: any;
  financial_analysis?: any;
  risk_analysis?: any;
  customer_analysis?: any;
  strategic_recommendations: any[];
  generated_at?: string;
  completion_time_seconds?: number;
}

export interface ValidationListResponse {
  validations: ValidationResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProgressUpdate {
  validation_id: string;
  status: string;
  progress_percentage: number;
  current_agent?: string;
  message?: string;
  agent_results?: Record<string, any>;
}

// API Service Class
class ApiService {
  // Generic HTTP methods
  async get(url: string, config?: any): Promise<AxiosResponse> {
    return apiClient.get(url, config);
  }

  async post(url: string, data?: any, config?: any): Promise<AxiosResponse> {
    return apiClient.post(url, data, config);
  }

  async put(url: string, data?: any, config?: any): Promise<AxiosResponse> {
    return apiClient.put(url, data, config);
  }

  async delete(url: string, config?: any): Promise<AxiosResponse> {
    return apiClient.delete(url, config);
  }
  // Authentication
  async login(email: string, password: string): Promise<{ user: any; token: string }> {
    const response = await apiClient.post('/api/v1/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  async getCurrentUser(): Promise<any> {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  }

  // Validations
  async createValidation(request: ValidationRequest): Promise<ValidationResponse> {
    const response = await apiClient.post('/api/v1/validations/', request);
    return response.data;
  }

  async getValidations(
    page: number = 1,
    pageSize: number = 20,
    statusFilter?: string
  ): Promise<ValidationListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }

    const response = await apiClient.get(`/api/v1/validations/?${params}`);
    return response.data;
  }

  async getValidation(id: string): Promise<ValidationResponse> {
    const response = await apiClient.get(`/api/v1/validations/${id}`);
    return response.data;
  }

  async getValidationResult(id: string): Promise<ValidationResult> {
    const response = await apiClient.get(`/api/v1/validations/${id}/result`);
    return response.data;
  }

  async cancelValidation(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/validations/${id}`);
  }

  async getValidationProgress(id: string): Promise<ProgressUpdate> {
    const response = await apiClient.get(`/api/v1/validations/${id}/progress`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await apiClient.get('/health');
    return response.data;
  }

  // Visualization data endpoints
  async getVisualizationData(validationId: string, chartType: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/visualizations/${validationId}/${chartType}`);
    return response.data;
  }

  async generateReport(validationId: string, format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await apiClient.get(`/api/v1/reports/${validationId}`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  // User preferences
  async updateUserPreferences(preferences: Record<string, any>): Promise<void> {
    await apiClient.put('/api/v1/users/preferences', preferences);
  }

  async getUserPreferences(): Promise<Record<string, any>> {
    const response = await apiClient.get('/api/v1/users/preferences');
    return response.data;
  }

  // Demo execution
  async executeDemoScenario(scenarioId: string, forceMock: boolean = false): Promise<any> {
    const url = `/api/v1/demo/scenarios/${scenarioId}/execute${forceMock ? '?force_mock=true' : ''}`;
    // Use longer timeout for demo execution (2 minutes instead of 30 seconds)
    const response = await apiClient.post(url, {}, { timeout: 120000 });
    return response.data;
  }

  async getDemoExecutionStatus(executionId: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/demo/executions/${executionId}/status`);
    return response.data;
  }

  async getDemoExecutionResults(executionId: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/demo/executions/${executionId}/results`);
    return response.data;
  }

  async getDemoImpactDashboard(): Promise<any> {
    const response = await apiClient.get('/api/v1/demo/impact-dashboard');
    return response.data;
  }

  async getDemoScenarios(): Promise<any> {
    const response = await apiClient.get('/api/v1/demo/scenarios');
    return response.data;
  }

  async getDemoShowcase(): Promise<any> {
    const response = await apiClient.get('/api/v1/demo/competition-showcase');
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;