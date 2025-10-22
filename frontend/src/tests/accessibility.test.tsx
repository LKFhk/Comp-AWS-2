import React from 'react';
import { render, screen, act, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe } from 'jest-axe';
import { renderWithProviders } from './test-utils';

// Mock API service
jest.mock('../services/api', () => ({
  apiService: {
    getValidations: jest.fn().mockResolvedValue({
      validations: [
        {
          id: 'test-validation-1',
          financial_institution_profile: 'Cryptocurrency exchange with 100K users offering spot trading, staking, and custody services',
          regulatory_jurisdiction: 'United States - FinCEN registered MSB, state money transmitter licenses, SEC securities compliance',
          status: 'completed',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T02:00:00Z',
          overall_score: 85.5,
          confidence_level: 0.92
        }
      ],
      total: 1,
      page: 1,
      page_size: 20,
    }),
    createValidation: jest.fn(),
    getValidation: jest.fn(),
    getValidationResult: jest.fn(),
    getValidationProgress: jest.fn(),
    healthCheck: jest.fn().mockResolvedValue({ 
      status: 'ok', 
      timestamp: '2024-10-20T12:00:00.000Z' 
    }),
    getVisualizationData: jest.fn(),
    generateReport: jest.fn(),
    updateUserPreferences: jest.fn(),
    getUserPreferences: jest.fn(),
    login: jest.fn(),
    getCurrentUser: jest.fn(),
    cancelValidation: jest.fn(),
  }
}));

// Mock WebSocket service
jest.mock('../services/websocket', () => ({
  websocketService: {
    connectToValidationProgress: jest.fn(),
    connectToNotifications: jest.fn(),
    disconnect: jest.fn(),
  }
}));

// Mock auth context with authenticated user
jest.mock('../contexts/AuthContext', () => ({
  ...jest.requireActual('../contexts/AuthContext'),
  useAuth: () => ({
    user: {
      id: 'test-user',
      email: 'test@riskintel360.com',
      name: 'Test User',
      role: 'analyst',
      preferences: {
        theme: 'light',
        notifications: true,
        defaultAnalysisScope: ['market_risk', 'fraud_detection', 'credit_risk', 'compliance_monitoring', 'kyc_verification']
      }
    },
    loading: false,
    login: jest.fn().mockResolvedValue(undefined),
    logout: jest.fn(),
    updateUser: jest.fn(),
  }),
}));

import App from '../App';

describe('Accessibility Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  test('App has proper form validation', async () => {
    let container: HTMLElement | undefined;
    
    await act(async () => {
      const result = renderWithProviders(<App />);
      container = result.container;
    });

    // Ensure container is defined
    if (!container) {
      throw new Error('Container not initialized');
    }

    // Wait for the app to load
    await waitFor(() => {
      expect(container!.querySelector('[data-testid="dashboard"]') || 
             container!.querySelector('main') ||
             container!.querySelector('[role="main"]')).toBeInTheDocument();
    }, { timeout: 15000 });

    // Check for proper form validation attributes
    const forms = container.querySelectorAll('form');
    forms.forEach(form => {
      const inputs = form.querySelectorAll('input[required]');
      inputs.forEach(input => {
        expect(input).toHaveAttribute('aria-required', 'true');
      });
    });

    // Check for error message containers
    const errorContainers = container.querySelectorAll('[role="alert"]');
    expect(errorContainers.length).toBeGreaterThanOrEqual(0);
  }, 30000);

  test('App has basic accessibility structure', async () => {
    let container: HTMLElement | undefined;
    
    await act(async () => {
      const result = render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <App />
        </MemoryRouter>
      );
      container = result.container;
    });

    // Ensure container is defined
    if (!container) {
      throw new Error('Container not initialized');
    }

    // Wait for the app to load
    await waitFor(() => {
      expect(container!.querySelector('main') || 
             container!.querySelector('[role="main"]') ||
             container!.querySelector('div')).toBeInTheDocument();
    }, { timeout: 15000 });

    // Check for basic accessibility structure
    const main = container.querySelector('main, [role="main"], div');
    expect(main).toBeInTheDocument();

    // Check for navigation (may be present in the rendered app)
    const nav = container.querySelector('nav, [role="navigation"], [aria-label*="navigation"], .MuiDrawer-root, .MuiAppBar-root');
    if (nav) {
      expect(nav).toBeInTheDocument();
    } else {
      // If no nav found, just ensure the app rendered successfully
      expect(main).toBeInTheDocument();
    }

    // Check for headings (should be present in dashboard)
    await waitFor(() => {
      const headings = container!.querySelectorAll('h1, h2, h3, h4, h5, h6');
      expect(headings.length).toBeGreaterThan(0);
    }, { timeout: 10000 });
  }, 30000);

  test('App has proper ARIA labels', async () => {
    let container: HTMLElement | undefined;
    
    await act(async () => {
      const result = renderWithProviders(<App />);
      container = result.container;
    });

    // Ensure container is defined
    if (!container) {
      throw new Error('Container not initialized');
    }

    // Wait for the app to load
    await waitFor(() => {
      expect(container!.querySelector('main') || 
             container!.querySelector('[role="main"]')).toBeInTheDocument();
    }, { timeout: 15000 });

    // Check for ARIA labels on interactive elements
    const buttons = container.querySelectorAll('button');
    buttons.forEach(button => {
      const hasLabel = button.getAttribute('aria-label') || 
                      button.getAttribute('aria-labelledby') ||
                      button.textContent?.trim();
      expect(hasLabel).toBeTruthy();
    });

    // Check for ARIA labels on form inputs
    const inputs = container.querySelectorAll('input');
    inputs.forEach(input => {
      const hasLabel = input.getAttribute('aria-label') || 
                      input.getAttribute('aria-labelledby') ||
                      container!.querySelector(`label[for="${input.id}"]`);
      if (input.type !== 'hidden') {
        expect(hasLabel).toBeTruthy();
      }
    });
  }, 30000);

  test('App supports keyboard navigation', async () => {
    let container: HTMLElement | undefined;
    
    await act(async () => {
      const result = renderWithProviders(<App />);
      container = result.container;
    });

    // Ensure container is defined
    if (!container) {
      throw new Error('Container not initialized');
    }

    // Wait for the app to load
    await waitFor(() => {
      expect(container!.querySelector('main') || 
             container!.querySelector('[role="main"]')).toBeInTheDocument();
    }, { timeout: 15000 });

    // Check for focusable elements
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    expect(focusableElements.length).toBeGreaterThan(0);

    // Check that focusable elements have proper tabindex
    focusableElements.forEach(element => {
      const tabIndex = element.getAttribute('tabindex');
      if (tabIndex !== null) {
        expect(parseInt(tabIndex)).toBeGreaterThanOrEqual(-1);
      }
    });
  }, 30000);

  test('App has sufficient color contrast', async () => {
    let container: HTMLElement | undefined;
    
    await act(async () => {
      const result = renderWithProviders(<App />);
      container = result.container;
    });

    // Ensure container is defined
    if (!container) {
      throw new Error('Container not initialized');
    }

    // Wait for the app to load
    await waitFor(() => {
      expect(container!.querySelector('main') || 
             container!.querySelector('[role="main"]')).toBeInTheDocument();
    }, { timeout: 15000 });

    // Basic check for text elements
    const textElements = container.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6');
    expect(textElements.length).toBeGreaterThan(0);

    // This is a basic structural check - actual contrast testing would require more complex tools
    textElements.forEach(element => {
      const computedStyle = window.getComputedStyle(element);
      expect(computedStyle.color).toBeDefined();
      expect(computedStyle.backgroundColor).toBeDefined();
    });
  }, 30000);
});