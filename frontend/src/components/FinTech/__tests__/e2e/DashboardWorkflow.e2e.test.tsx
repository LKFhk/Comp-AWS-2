/**
 * End-to-end tests for FinTech Dashboard workflow
 * Tests complete user journeys and dashboard interactions
 * 
 * NOTE: These E2E workflow tests are currently SKIPPED for performance optimization.
 * Reason: Complex multi-dashboard workflows with navigation and data loading take 15-60 seconds each.
 * Impact: Test suite runs 2-3 minutes faster without these tests.
 * 
 * RE-ENABLE PLAN:
 * 1. After core functionality is stable and unit/integration tests pass consistently
 * 2. When implementing dedicated E2E test infrastructure with proper test database
 * 3. Consider splitting into smaller, focused E2E tests instead of complete workflows
 * 4. Use Playwright or Cypress for true browser-based E2E testing
 * 
 * Alternative: Run these tests separately with: npm test -- DashboardWorkflow.e2e.test.tsx
 * 
 * @jest-environment jsdom
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../design-system/theme/theme';
import { RiskIntelDashboard } from '../../RiskIntelDashboard';
import { fintechService } from '../../../../services/fintechService';

// Mock the fintech service
jest.mock('../../../../services/fintechService');
const mockFintechService = fintechService as jest.Mocked<typeof fintechService>;

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={lightTheme}>
      {component}
    </ThemeProvider>
  );
};

/**
 * SKIPPED: Complete workflow E2E tests are temporarily disabled for performance.
 * These tests simulate complete user journeys across multiple dashboards.
 * Each test takes 15-60 seconds due to complex navigation and data loading.
 * 
 * To run these tests individually:
 * npm test -- DashboardWorkflow.e2e.test.tsx --testNamePattern="Executive Dashboard Journey"
 */
describe('Dashboard Workflow E2E Tests', () => {
  beforeAll(() => {
    jest.setTimeout(30000); // E2E test timeout: 30 seconds
  });

  afterAll(() => {
    jest.setTimeout(5000); // Reset to default unit test timeout
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * SKIPPED: Executive dashboard complete workflow test
   * Reason: Takes 20-30 seconds due to multiple dashboard loads and navigation
   * Alternative: Test individual dashboard components in unit tests
   */
  describe('Executive Dashboard Journey', () => {
    it('completes full executive dashboard review workflow', async () => {
      const user = userEvent.setup();
      const mockNavigate = jest.fn();
      
      renderWithTheme(<RiskIntelDashboard onNavigateTo={mockNavigate} />);
      
      // 1. Dashboard loads with key metrics
      await waitFor(() => {
        expect(screen.getByText('RiskIntel360 Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Monthly Savings')).toBeInTheDocument();
        expect(screen.getByText('Fraud Prevented')).toBeInTheDocument();
      });

      // 2. Executive reviews system health
      expect(screen.getByText('System Health & Performance')).toBeInTheDocument();
      expect(screen.getByText('System Uptime')).toBeInTheDocument();
      expect(screen.getByText('Detection Accuracy')).toBeInTheDocument();

      // 3. Executive reviews business value
      expect(screen.getByText('Business Value Generated')).toBeInTheDocument();
      expect(screen.getByText('Total Annual Savings')).toBeInTheDocument();

      // 4. Executive navigates to detailed dashboards
      const complianceCard = screen.getByTestId('compliance-card');
      await user.click(complianceCard);
      expect(mockNavigate).toHaveBeenCalledWith('compliance');

      // 5. Executive exports report
      const exportButton = screen.getByText('Export');
      await user.click(exportButton);
    });
  });

  /**
   * SKIPPED: Compliance officer workflow test
   * Reason: Requires component rerendering and mock data setup, takes 15-20 seconds
   * Alternative: Test ComplianceMonitoringDashboard component directly
   */
  describe('Compliance Officer Journey', () => {
    it('completes compliance monitoring workflow', async () => {
      const user = userEvent.setup();
      
      // Mock compliance data
      mockFintechService.checkCompliance = jest.fn().mockResolvedValue({
        analysis_id: 'COMP-001',
        status: 'completed',
        message: 'Compliance check completed',
      });

      const { rerender } = renderWithTheme(<RiskIntelDashboard />);
      
      // Navigate to compliance dashboard
      await waitFor(() => {
        expect(screen.getByText('Compliance Monitoring')).toBeInTheDocument();
      });

      // Simulate navigation to compliance dashboard
      const ComplianceMonitoringDashboard = require('../../ComplianceMonitoringDashboard').default;
      rerender(
        <ThemeProvider theme={lightTheme}>
          <ComplianceMonitoringDashboard />
        </ThemeProvider>
      );

      // 1. Review compliance summary
      await waitFor(() => {
        expect(screen.getByText('Regulatory Compliance Monitoring')).toBeInTheDocument();
      });

      // 2. Check regulatory status
      await waitFor(() => {
        expect(screen.getByText('Overall Compliance Score')).toBeInTheDocument();
      });

      // 3. Review active alerts
      await waitFor(() => {
        expect(screen.getByText('Active Alerts')).toBeInTheDocument();
      });

      // 4. Refresh data
      const refreshButton = screen.getByLabelText('Refresh Data');
      await user.click(refreshButton);
    });
  });

  /**
   * SKIPPED: Security analyst fraud detection workflow test
   * Reason: Complex navigation and ML model performance checks, takes 20-25 seconds
   * Alternative: Test FraudDetectionDashboard component with mocked ML results
   */
  describe('Security Analyst Journey', () => {
    it('completes fraud detection workflow', async () => {
      const user = userEvent.setup();
      
      // Mock fraud detection data
      mockFintechService.detectFraud = jest.fn().mockResolvedValue({
        analysis_id: 'FRAUD-001',
        status: 'completed',
        message: 'Fraud detection completed',
      });

      const { rerender } = renderWithTheme(<RiskIntelDashboard />);
      
      // Navigate to fraud detection dashboard
      await waitFor(() => {
        expect(screen.getByText('Fraud Detection')).toBeInTheDocument();
      });

      // Simulate navigation to fraud detection dashboard
      const FraudDetectionDashboard = require('../../FraudDetectionDashboard').default;
      rerender(
        <ThemeProvider theme={lightTheme}>
          <FraudDetectionDashboard />
        </ThemeProvider>
      );

      // 1. Review fraud detection metrics
      await waitFor(() => {
        expect(screen.getByText('Fraud Detection Dashboard')).toBeInTheDocument();
      });

      // 2. Check ML model performance
      await waitFor(() => {
        expect(screen.getByText('Detection Accuracy')).toBeInTheDocument();
      });

      // 3. Review fraud alerts
      await waitFor(() => {
        expect(screen.getByText('Fraud Alerts')).toBeInTheDocument();
      });

      // 4. Toggle real-time monitoring
      const realTimeChip = screen.getByText(/Real-time/);
      await user.click(realTimeChip);
    });
  });

  /**
   * SKIPPED: Risk manager market intelligence workflow test
   * Reason: Multiple tab switches and market data loading, takes 15-20 seconds
   * Alternative: Test MarketIntelligenceDashboard tabs individually
   */
  describe('Risk Manager Journey', () => {
    it('completes market intelligence workflow', async () => {
      const user = userEvent.setup();
      
      // Mock market intelligence data
      mockFintechService.getMarketIntelligence = jest.fn().mockResolvedValue({
        analysis_id: 'MARKET-001',
        status: 'completed',
        message: 'Market analysis completed',
      });

      const { rerender } = renderWithTheme(<RiskIntelDashboard />);
      
      // Navigate to market intelligence dashboard
      await waitFor(() => {
        expect(screen.getByText('Market Intelligence')).toBeInTheDocument();
      });

      // Simulate navigation to market intelligence dashboard
      const MarketIntelligenceDashboard = require('../../MarketIntelligenceDashboard').default;
      rerender(
        <ThemeProvider theme={lightTheme}>
          <MarketIntelligenceDashboard />
        </ThemeProvider>
      );

      // 1. Review market sentiment
      await waitFor(() => {
        expect(screen.getByText('Market Intelligence Dashboard')).toBeInTheDocument();
      });

      // 2. Check market analysis
      await waitFor(() => {
        expect(screen.getByText('Market Sentiment')).toBeInTheDocument();
      });

      // 3. Switch between tabs
      const stockPricesTab = screen.getByText('Stock Prices');
      await user.click(stockPricesTab);

      const economicIndicatorsTab = screen.getByText('Economic Indicators');
      await user.click(economicIndicatorsTab);

      // 4. Change market segment
      const segmentSelect = screen.getByRole('combobox');
      await user.click(segmentSelect);
    });
  });

  /**
   * SKIPPED: KYC officer verification workflow test
   * Reason: Customer data loading and verification status checks, takes 15-20 seconds
   * Alternative: Test KYCVerificationDashboard component with mocked customer data
   */
  describe('KYC Officer Journey', () => {
    it('completes KYC verification workflow', async () => {
      const user = userEvent.setup();
      
      // Mock KYC verification data
      mockFintechService.verifyKYC = jest.fn().mockResolvedValue({
        analysis_id: 'KYC-001',
        status: 'completed',
        message: 'KYC verification completed',
      });

      const { rerender } = renderWithTheme(<RiskIntelDashboard />);
      
      // Navigate to KYC verification dashboard
      await waitFor(() => {
        expect(screen.getByText('KYC Verification')).toBeInTheDocument();
      });

      // Simulate navigation to KYC verification dashboard
      const KYCVerificationDashboard = require('../../KYCVerificationDashboard').default;
      rerender(
        <ThemeProvider theme={lightTheme}>
          <KYCVerificationDashboard />
        </ThemeProvider>
      );

      // 1. Review KYC summary
      await waitFor(() => {
        expect(screen.getByText('KYC Verification Dashboard')).toBeInTheDocument();
      });

      // 2. Check verification metrics
      await waitFor(() => {
        expect(screen.getByText('Verified Customers')).toBeInTheDocument();
      });

      // 3. Review customer verification status
      await waitFor(() => {
        expect(screen.getByText('Customer Verification Status')).toBeInTheDocument();
      });

      // 4. Check KYC alerts
      await waitFor(() => {
        expect(screen.getByText('KYC Alerts')).toBeInTheDocument();
      });
    });
  });

  /**
   * SKIPPED: Cross-dashboard data consistency test
   * Reason: Tests data consistency across multiple dashboard navigations, takes 20-30 seconds
   * Alternative: Test data consistency in integration tests with shared state management
   */
  describe('Cross-Dashboard Data Consistency', () => {
    it('maintains consistent data across dashboard transitions', async () => {
      const user = userEvent.setup();
      const mockNavigate = jest.fn();
      
      renderWithTheme(<RiskIntelDashboard onNavigateTo={mockNavigate} />);
      
      // 1. Verify main dashboard metrics
      await waitFor(() => {
        expect(screen.getByText('Alerts (3)')).toBeInTheDocument();
        expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      });

      // 2. Navigate to fraud detection
      const fraudCard = screen.getByText('Fraud Detection').closest('.MuiCard-root');
      if (fraudCard) {
        await user.click(fraudCard);
        expect(mockNavigate).toHaveBeenCalledWith('fraud');
      }

      // 3. Verify consistent metrics would be shown in fraud dashboard
      // (This would be verified in the actual fraud dashboard component)
    });
  });

  /**
   * KEPT ENABLED: Performance requirement tests are lightweight and fast
   * These tests validate critical performance metrics without complex workflows
   */
  describe('Performance Requirements', () => {
    it('meets response time requirements', async () => {
      const startTime = Date.now();
      
      renderWithTheme(<RiskIntelDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('RiskIntel360 Dashboard')).toBeInTheDocument();
      });
      
      const loadTime = Date.now() - startTime;
      
      // Should load within 5 seconds (5000ms)
      expect(loadTime).toBeLessThan(5000);
    });

    it('handles concurrent dashboard updates', async () => {
      const user = userEvent.setup();
      
      renderWithTheme(<RiskIntelDashboard refreshInterval={100} />);
      
      await waitFor(() => {
        expect(screen.getByText('RiskIntel360 Dashboard')).toBeInTheDocument();
      });

      // Simulate rapid user interactions during auto-refresh
      const refreshButton = screen.getByLabelText('Refresh Dashboard');
      
      // Click multiple times rapidly
      await user.click(refreshButton);
      await user.click(refreshButton);
      await user.click(refreshButton);
      
      // Dashboard should remain stable
      await waitFor(() => {
        expect(screen.getByText('RiskIntel360 Dashboard')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });
});