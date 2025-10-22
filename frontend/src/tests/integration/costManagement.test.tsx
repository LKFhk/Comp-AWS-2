/**
 * Cost Management Integration Tests
 * Tests the complete cost management functionality from frontend to backend
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@mui/material/styles';

import CostEstimation from '../../pages/CredentialsManagement/components/CostEstimation';
import { NotificationProvider } from '../../contexts/NotificationContext';
import { credentialsService } from '../../services/credentialsService';

// Mock the credentials service
jest.mock('../../services/credentialsService', () => ({
  credentialsService: {
    estimateValidationCost: jest.fn(),
    formatCurrency: jest.fn((amount) => `$${amount.toFixed(2)}`),
  },
}));

const theme = createTheme();

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>
      <NotificationProvider>
        {children}
      </NotificationProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe('Cost Management Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('CostEstimation Component', () => {
    it('should render cost estimation form correctly', () => {
      render(
        <TestWrapper>
          <CostEstimation />
        </TestWrapper>
      );

      expect(screen.getByText('AWS Cost Estimation')).toBeInTheDocument();
      expect(screen.getByText('Validation Parameters')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument(); // Cost Profile dropdown
      expect(screen.getByText('Fill Sample Data')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /estimate cost/i })).toBeInTheDocument();
    });

    it('should fill sample data when button is clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <CostEstimation />
        </TestWrapper>
      );

      // Click fill sample data button
      const fillSampleButton = screen.getByText('Fill Sample Data');
      await user.click(fillSampleButton);

      // Check that form fields are populated
      await waitFor(() => {
        const businessConceptField = screen.getByDisplayValue(/FinTech startup - Payment processing platform/);
        expect(businessConceptField).toBeInTheDocument();
      });
    });

    it('should show validation error for empty required fields', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <CostEstimation />
        </TestWrapper>
      );

      // Try to estimate without filling required fields
      const estimateButton = screen.getByRole('button', { name: /estimate cost/i });
      await user.click(estimateButton);

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText('Please fill in all required fields')).toBeInTheDocument();
      });
    });

    it('should call API when form is properly filled', async () => {
      const user = userEvent.setup();
      const mockEstimationResult = {
        estimate: {
          total_cost_usd: 45.50,
          bedrock_cost: 35.00,
          infrastructure_cost: 10.50,
          estimated_duration_minutes: 120,
          confidence_level: 0.85,
          profile_used: 'development'
        }
      };

      (credentialsService.estimateValidationCost as jest.Mock).mockResolvedValue(mockEstimationResult);

      render(
        <TestWrapper>
          <CostEstimation />
        </TestWrapper>
      );

      // Fill sample data
      await user.click(screen.getByText('Fill Sample Data'));

      // Wait for form to be populated
      await waitFor(() => {
        expect(screen.getByDisplayValue(/FinTech startup/)).toBeInTheDocument();
      });

      // Click estimate cost
      const estimateButton = screen.getByRole('button', { name: /estimate cost/i });
      await user.click(estimateButton);

      // Verify API was called
      await waitFor(() => {
        expect(credentialsService.estimateValidationCost).toHaveBeenCalledWith(
          expect.objectContaining({
            profile: 'development',
            business_concept: 'FinTech startup - Payment processing platform',
            analysis_scope: ['regulatory', 'fraud', 'risk'],
            target_market: 'US - SEC/FINRA regulated',
          })
        );
      });
    });

    it('should handle API errors gracefully', async () => {
      const user = userEvent.setup();
      const mockError = new Error('Cost estimation service unavailable');

      (credentialsService.estimateValidationCost as jest.Mock).mockRejectedValue(mockError);

      render(
        <TestWrapper>
          <CostEstimation />
        </TestWrapper>
      );

      // Fill sample data and estimate
      await user.click(screen.getByText('Fill Sample Data'));
      await waitFor(() => {
        expect(screen.getByDisplayValue(/FinTech startup/)).toBeInTheDocument();
      });

      const estimateButton = screen.getByRole('button', { name: /estimate cost/i });
      await user.click(estimateButton);

      // Check that error is displayed
      await waitFor(() => {
        expect(screen.getByText('Cost estimation service unavailable')).toBeInTheDocument();
      });
    });
  });
});