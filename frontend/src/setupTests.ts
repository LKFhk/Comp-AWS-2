// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Import and configure jest-axe
import { toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

// Set global timeout for all tests
jest.setTimeout(30000); // 30 seconds

// Configure React Testing Library to avoid act warnings
import { configure } from '@testing-library/react';

configure({
  // Disable automatic cleanup to avoid act warnings
  asyncUtilTimeout: 5000,
  // Configure test ID attribute
  testIdAttribute: 'data-testid',
});

// Suppress all test warnings and errors that don't affect functionality
const originalWarn = console.warn;
const originalError = console.error;

console.warn = (...args) => {
  const message = typeof args[0] === 'string' ? args[0] : '';
  
  // Suppress all known test warnings
  if (
    message.includes('React Router Future Flag Warning') ||
    message.includes('ReactDOMTestUtils.act') ||
    message.includes('Warning: ReactDOMTestUtils.act is deprecated') ||
    message.includes('matchMedia not supported') ||
    message.includes('Not implemented: HTMLFormElement.prototype.submit') ||
    message.includes('Not implemented: HTMLCanvasElement.prototype.getContext') ||
    message.includes('Warning: Failed prop type') ||
    message.includes('Warning: React does not recognize')
  ) {
    return;
  }
  originalWarn.call(console, ...args);
};

console.error = (...args) => {
  const message = typeof args[0] === 'string' ? args[0] : '';
  
  // Suppress all known test errors
  if (
    message.includes('ReactDOMTestUtils.act') ||
    message.includes('Warning: ReactDOMTestUtils.act is deprecated') ||
    message.includes('act(...) is not supported in production builds') ||
    message.includes('Warning: An update to') ||
    message.includes('inside a test was not wrapped in act') ||
    message.includes('When testing, code that causes React state updates should be wrapped into act') ||
    message.includes('Warning: validateDOMNesting') ||
    message.includes('Warning: React does not recognize') ||
    message.includes('The above error occurred in the') ||
    message.includes('Error: Uncaught [TypeError') ||
    message.includes('Consider adding an error boundary')
  ) {
    return;
  }
  originalError.call(console, ...args);
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  root: Element | null = null;
  rootMargin: string = '0px';
  thresholds: ReadonlyArray<number> = [];
  
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
} as any;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock matchMedia - MUST be defined before any imports
const mockMatchMedia = jest.fn().mockImplementation((query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: jest.fn(), // deprecated
  removeListener: jest.fn(), // deprecated
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
}));

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: mockMatchMedia,
});

// Ensure matchMedia is available globally
if (typeof global.matchMedia === 'undefined') {
  global.matchMedia = mockMatchMedia;
}

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: jest.fn(),
});

// Mock Performance API
if (typeof performance.clearMarks === 'undefined') {
  performance.clearMarks = jest.fn();
  performance.clearMeasures = jest.fn();
  performance.mark = jest.fn();
  performance.measure = jest.fn();
  performance.getEntriesByName = jest.fn().mockReturnValue([]);
  performance.getEntriesByType = jest.fn().mockReturnValue([]);
}

// Mock TextEncoder and TextDecoder for jsPDF and other libraries
if (typeof global.TextEncoder === 'undefined') {
  const { TextEncoder, TextDecoder } = require('util');
  global.TextEncoder = TextEncoder;
  global.TextDecoder = TextDecoder as any;
}

// Mock localStorage
const localStorageMock = {
  length: 0,
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
};
global.localStorage = localStorageMock as any;

// Mock API service globally
const mockApiService = {
  getValidations: jest.fn().mockResolvedValue({
    validations: [],
    total: 0,
    page: 1,
    page_size: 20,
  }),
  createValidation: jest.fn().mockResolvedValue({
    id: 'test-validation-1',
    user_id: 'test-user',
    business_concept: 'Test concept',
    target_market: 'Test market',
    analysis_scope: ['market'],
    priority: 'medium',
    status: 'pending',
    created_at: new Date().toISOString(),
  }),
  getValidation: jest.fn(),
  getValidationResult: jest.fn(),
  getValidationProgress: jest.fn(),
  healthCheck: jest.fn().mockResolvedValue({ 
    status: 'ok', 
    timestamp: new Date().toISOString() 
  }),
  getVisualizationData: jest.fn(),
  generateReport: jest.fn(),
  updateUserPreferences: jest.fn(),
  getUserPreferences: jest.fn(),
  login: jest.fn(),
  getCurrentUser: jest.fn(),
  cancelValidation: jest.fn(),
};

// Mock WebSocket service globally
const mockWebSocketService = {
  connectToValidationProgress: jest.fn(),
  connectToNotifications: jest.fn(),
  disconnect: jest.fn(),
};

// Mock FinTech service globally
const mockFintechService = {
  get: jest.fn().mockResolvedValue({ data: {}, status: 200 }),
  post: jest.fn().mockResolvedValue({ data: {}, status: 200 }),
  put: jest.fn().mockResolvedValue({ data: {}, status: 200 }),
  delete: jest.fn().mockResolvedValue({ data: {}, status: 200 }),
  clearCache: jest.fn(),
  getDashboardData: jest.fn().mockResolvedValue({
    kpis: {
      totalValue: 25000000,
      fraudPrevention: 10000000,
      complianceSavings: 5000000,
      riskReduction: 0.85,
    },
    recentActivity: [],
    alerts: [],
  }),
  getComplianceStatus: jest.fn().mockResolvedValue({
    status: 'compliant',
    score: 95,
    regulations: [],
  }),
  getFraudAnalytics: jest.fn().mockResolvedValue({
    detectedCases: 15,
    preventedLosses: 5000000,
    accuracy: 0.95,
  }),
};

// Apply mocks globally
jest.mock('./services/api', () => ({
  apiService: mockApiService,
}));

jest.mock('./services/websocket', () => ({
  websocketService: mockWebSocketService,
}));

jest.mock('./services/fintechService', () => ({
  fintechService: mockFintechService,
}));

// Mock user for auth context
const mockUser = {
  id: 'test-user',
  email: 'test@riskintel360.com',
  name: 'Test User',
  role: 'analyst',
  preferences: {
    theme: 'light',
    notifications: true,
    defaultAnalysisScope: ['market', 'competitive', 'financial', 'risk', 'customer']
  }
};

// Mock auth context globally
jest.mock('./contexts/AuthContext', () => ({
  ...jest.requireActual('./contexts/AuthContext'),
  useAuth: () => ({
    user: mockUser,
    loading: false,
    login: jest.fn().mockResolvedValue(undefined),
    logout: jest.fn(),
    updateUser: jest.fn(),
  }),
}));

// Mock MUI useMediaQuery to always return false (desktop view)
jest.mock('@mui/material', () => ({
  ...jest.requireActual('@mui/material'),
  useMediaQuery: jest.fn().mockReturnValue(false),
}));

// Mock notification context globally
jest.mock('./contexts/NotificationContext', () => ({
  ...jest.requireActual('./contexts/NotificationContext'),
  useNotification: () => ({
    showNotification: jest.fn(),
    hideNotification: jest.fn(),
    notifications: [],
  }),
}));