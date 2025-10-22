/**
 * End-to-End Tests for Complete User Workflows
 * Tests the entire user journey through the application
 */

describe('Complete User Workflow - Risk Analysis', () => {
  beforeEach(() => {
    // Mock authentication
    cy.intercept('POST', '/api/v1/auth/login', {
      statusCode: 200,
      body: {
        user: {
          id: '1',
          name: 'Test User',
          email: 'test@example.com',
          role: 'admin',
        },
        token: 'mock-token',
      },
    }).as('login');

    // Mock dashboard data
    cy.intercept('GET', '/api/v1/fintech/risk-analysis', {
      statusCode: 200,
      body: {
        summary: {
          active_analyses: 12,
          completed_today: 45,
          fraud_alerts: 3,
          compliance_issues: 1,
        },
      },
    }).as('getRiskAnalysis');

    cy.visit('/');
  });

  it('should complete full risk analysis workflow', () => {
    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    cy.wait('@login');

    // Navigate to Risk Intel Dashboard
    cy.contains('Risk Intelligence').click();
    cy.wait('@getRiskAnalysis');

    // Verify dashboard loaded
    cy.contains('RiskIntel360 Dashboard').should('be.visible');
    cy.contains('Monthly Savings').should('be.visible');

    // Navigate to Compliance Dashboard
    cy.contains('Compliance Monitoring').click();
    cy.contains('Compliance Monitoring Dashboard').should('be.visible');

    // Navigate to Fraud Detection Dashboard
    cy.contains('Fraud Detection').click();
    cy.contains('Fraud Detection Dashboard').should('be.visible');

    // Verify alerts are displayed
    cy.get('[data-testid="fraud-alerts"]').should('exist');
  });

  it('should handle onboarding flow for new users', () => {
    // Mock new user
    cy.intercept('POST', '/api/v1/auth/login', {
      statusCode: 200,
      body: {
        user: {
          id: '2',
          name: 'New User',
          email: 'new@example.com',
          role: 'analyst',
          preferences: {
            onboardingCompleted: false,
          },
        },
        token: 'mock-token',
      },
    });

    cy.get('input[name="email"]').type('new@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Should show onboarding dialog
    cy.contains('Welcome to RiskIntel360!').should('be.visible');
    cy.contains('Start Tour').click();

    // Navigate through onboarding
    cy.contains('AI-Powered Financial Risk Intelligence').should('be.visible');
    cy.contains('Next').click();

    cy.contains('Automated Regulatory Compliance').should('be.visible');
    cy.contains('Next').click();

    // Skip to end
    cy.contains('Skip Tour').click();

    // Should be on dashboard
    cy.url().should('include', '/dashboard');
  });

  it('should update user preferences', () => {
    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Navigate to settings
    cy.get('[aria-label="account of current user"]').click();
    cy.contains('Settings').click();

    // Change theme
    cy.get('[aria-label="Theme"]').click();
    cy.contains('Dark').click();

    // Change default dashboard
    cy.get('[aria-label="Default Dashboard"]').click();
    cy.contains('Fraud Detection').click();

    // Save preferences
    cy.contains('Save Preferences').click();

    // Verify success message
    cy.contains('Preferences saved successfully!').should('be.visible');
  });

  it('should handle role-based access control', () => {
    // Mock limited user
    cy.intercept('POST', '/api/v1/auth/login', {
      statusCode: 200,
      body: {
        user: {
          id: '3',
          name: 'Limited User',
          email: 'limited@example.com',
          role: 'viewer',
        },
        token: 'mock-token',
      },
    });

    cy.get('input[name="email"]').type('limited@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Try to access fraud dashboard
    cy.visit('/fintech/fraud');

    // Should show access denied
    cy.contains('Access Denied').should('be.visible');
    cy.contains('viewer').should('be.visible');
  });

  it('should handle real-time updates', () => {
    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Navigate to fraud dashboard
    cy.contains('Fraud Detection').click();

    // Mock WebSocket connection
    cy.window().then((win) => {
      // Simulate real-time alert
      win.postMessage({
        type: 'fraud_alert',
        data: {
          alert_id: 'ALERT-NEW',
          severity: 'high',
          title: 'New Fraud Alert',
        },
      }, '*');
    });

    // Verify alert appears
    cy.contains('New Fraud Alert', { timeout: 5000 }).should('be.visible');
  });

  it('should export dashboard data', () => {
    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Navigate to business value dashboard
    cy.visit('/fintech/business-value');

    // Click export button
    cy.contains('Export').click();
    cy.contains('Export as PDF').click();

    // Verify download initiated
    cy.get('[data-testid="export-progress"]').should('be.visible');
  });

  it('should handle mobile responsive layout', () => {
    // Set mobile viewport
    cy.viewport('iphone-x');

    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Navigate to risk intel dashboard
    cy.visit('/fintech/risk-intel');

    // Should show mobile optimized view
    cy.get('[data-testid="mobile-dashboard"]').should('be.visible');

    // Test bottom navigation
    cy.get('[data-testid="bottom-navigation"]').should('be.visible');
    cy.get('[data-testid="bottom-nav-alerts"]').click();

    // Verify navigation worked
    cy.contains('Alerts').should('be.visible');
  });

  it('should handle error states gracefully', () => {
    // Mock API error
    cy.intercept('GET', '/api/v1/fintech/risk-analysis', {
      statusCode: 500,
      body: { error: 'Internal Server Error' },
    }).as('getRiskAnalysisError');

    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Navigate to risk intel dashboard
    cy.visit('/fintech/risk-intel');
    cy.wait('@getRiskAnalysisError');

    // Should show error message
    cy.contains('Failed to fetch dashboard data').should('be.visible');

    // Should have retry button
    cy.contains('Retry').click();
  });

  it('should persist user session across page reloads', () => {
    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Navigate to a dashboard
    cy.visit('/fintech/compliance');

    // Reload page
    cy.reload();

    // Should still be logged in
    cy.contains('Compliance Monitoring Dashboard').should('be.visible');
  });

  it('should handle concurrent dashboard operations', () => {
    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Open multiple dashboards in quick succession
    cy.visit('/fintech/risk-intel');
    cy.visit('/fintech/compliance');
    cy.visit('/fintech/fraud');

    // Should handle all requests
    cy.contains('Fraud Detection Dashboard').should('be.visible');
  });
});

describe('Dashboard Performance Tests', () => {
  beforeEach(() => {
    cy.intercept('POST', '/api/v1/auth/login', {
      statusCode: 200,
      body: {
        user: {
          id: '1',
          name: 'Test User',
          email: 'test@example.com',
          role: 'admin',
        },
        token: 'mock-token',
      },
    });

    cy.visit('/');
  });

  it('should load dashboard within performance budget', () => {
    // Login
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    // Measure dashboard load time
    const startTime = Date.now();

    cy.visit('/fintech/risk-intel');
    cy.contains('RiskIntel360 Dashboard').should('be.visible');

    cy.then(() => {
      const loadTime = Date.now() - startTime;
      expect(loadTime).to.be.lessThan(3000); // Should load within 3 seconds
    });
  });

  it('should handle large datasets efficiently', () => {
    // Mock large dataset
    cy.intercept('GET', '/api/v1/fintech/fraud-alerts', {
      statusCode: 200,
      body: {
        alerts: Array.from({ length: 1000 }, (_, i) => ({
          id: `alert-${i}`,
          severity: 'high',
          title: `Alert ${i}`,
        })),
      },
    });

    // Login and navigate
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    cy.visit('/fintech/fraud');

    // Should render without freezing
    cy.get('[data-testid="fraud-alerts"]', { timeout: 5000 }).should('be.visible');
  });
});
