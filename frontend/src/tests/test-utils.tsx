import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AuthProvider } from '../contexts/AuthContext';
import { NotificationProvider } from '../contexts/NotificationContext';

// Re-export everything from React Testing Library
export * from '@testing-library/react';

const theme = createTheme();

// Mock user for testing
export const mockUser = {
  id: 'test-user',
  email: 'test@riskintel360.com',
  name: 'Test User',
  role: 'analyst',
  preferences: {
    theme: 'light',
    notifications: true,
    defaultAnalysisScope: ['market_risk', 'fraud_detection', 'credit_risk', 'compliance_monitoring', 'kyc_verification']
  }
};

// Mock API responses
export const mockValidationResponse = {
  id: 'test-validation-1',
  user_id: 'test-user',
  financial_institution_profile: 'FinTech startup processing $50M annual transactions with digital payment platform serving 100K active users across US markets',
  regulatory_jurisdiction: 'United States - SEC/FINRA regulated payment processor, state money transmitter licenses in 45 states',
  analysis_scope: ['market_risk', 'fraud_detection', 'credit_risk', 'compliance_monitoring', 'kyc_verification'],
  priority: 'medium',
  status: 'completed',
  created_at: '2024-10-20T12:00:00.000Z',
  updated_at: '2024-10-20T12:00:00.000Z',
  overall_score: 85.5,
  confidence_level: 0.92,
  progress_url: '/api/v1/validations/test-validation-1/progress'
};

export const mockValidationResult = {
  request_id: 'test-validation-1',
  overall_score: 78.5,
  confidence_level: 0.85,
  status: 'completed',
  market_risk_analysis: { volatility_score: 0.65, liquidity_risk: 'medium', market_exposure: 2500000000 },
  fraud_detection_analysis: { fraud_probability: 0.12, anomaly_count: 3, false_positive_rate: 0.08 },
  credit_risk_analysis: { default_probability: 0.05, credit_score: 720, risk_rating: 'A-' },
  compliance_monitoring: { compliance_score: 0.92, regulatory_gaps: 2, remediation_priority: 'medium' },
  kyc_verification_analysis: { verification_status: 'approved', risk_level: 'low', customer_segments: 3 },
  strategic_recommendations: [
    {
      title: 'Fraud Prevention Enhancement',
      description: 'Implement ML-based transaction monitoring for high-risk patterns',
      priority: 'High',
      timeline: '3-6 months'
    }
  ],
  generated_at: '2024-10-20T12:00:00.000Z',
  completion_time_seconds: 3600
};

// Mock API service
export const mockApiService = {
  getValidations: jest.fn().mockResolvedValue({
    validations: [mockValidationResponse],
    total: 1,
    page: 1,
    page_size: 20,
  }),
  createValidation: jest.fn().mockResolvedValue(mockValidationResponse),
  getValidation: jest.fn().mockResolvedValue(mockValidationResponse),
  getValidationResult: jest.fn().mockResolvedValue(mockValidationResult),
  getValidationProgress: jest.fn().mockResolvedValue({
    validation_id: 'test-validation-1',
    status: 'running',
    progress_percentage: 65,
    current_agent: 'risk_assessment',
    message: 'Analyzing financial projections...'
  }),
  healthCheck: jest.fn().mockResolvedValue({ 
    status: 'ok', 
    timestamp: '2024-10-20T12:00:00.000Z' 
  }),
  getVisualizationData: jest.fn().mockResolvedValue({
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
    data: [100, 150, 200, 250]
  }),
  generateReport: jest.fn().mockResolvedValue(new Blob(['mock pdf'], { type: 'application/pdf' })),
  updateUserPreferences: jest.fn().mockResolvedValue({}),
  getUserPreferences: jest.fn().mockResolvedValue({
    theme: 'light',
    notifications: { email: true, push: true },
    defaultAnalysisScope: ['market_risk', 'fraud_detection', 'credit_risk', 'compliance_monitoring']
  }),
  login: jest.fn().mockResolvedValue({ user: mockUser, token: 'mock-token' }),
  getCurrentUser: jest.fn().mockResolvedValue(mockUser),
  cancelValidation: jest.fn().mockResolvedValue(undefined),
};

// Mock WebSocket service
export const mockWebSocketService = {
  connectToValidationProgress: jest.fn(),
  connectToNotifications: jest.fn(),
  disconnect: jest.fn(),
};

// All providers wrapper
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AuthProvider>
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => {
  return render(ui, { wrapper: AllTheProviders, ...options });
};

// Helper function to render with providers
export const renderWithProviders = (ui: ReactElement) => {
  return customRender(ui);
};

// Export customRender as render for convenience
export { customRender as render };

// Setup mocks for all tests
export const setupMocks = () => {
  // Mock API service
  jest.mock('../services/api', () => ({
    apiService: mockApiService,
  }));

  // Mock WebSocket service
  jest.mock('../services/websocket', () => ({
    websocketService: mockWebSocketService,
  }));

  // Mock auth context with authenticated user
  jest.mock('../contexts/AuthContext', () => ({
    ...jest.requireActual('../contexts/AuthContext'),
    useAuth: () => ({
      user: mockUser,
      loading: false,
      login: jest.fn().mockResolvedValue(undefined),
      logout: jest.fn(),
      updateUser: jest.fn(),
    }),
  }));
};

// Clean up mocks
export const cleanupMocks = () => {
  jest.clearAllMocks();
};