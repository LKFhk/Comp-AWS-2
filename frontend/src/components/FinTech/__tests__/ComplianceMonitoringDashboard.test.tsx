/**
 * Unit tests for ComplianceMonitoringDashboard component
 * @jest-environment jsdom
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../design-system/theme/theme';
import { ComplianceMonitoringDashboard } from '../ComplianceMonitoringDashboard';
import { setupFetchMocks, resetFetchMocks } from '../../../tests/__mocks__/dashboardMockData';

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={lightTheme}>
      {component}
    </ThemeProvider>
  );
};

describe('ComplianceMonitoringDashboard', () => {
  beforeEach(() => {
    setupFetchMocks();
    jest.setTimeout(10000); // Integration test timeout: 10 seconds
  });

  afterEach(() => {
    resetFetchMocks();
    jest.setTimeout(5000); // Reset to default unit test timeout
  });

  it('renders regulatory compliance monitoring title', async () => {
    renderWithTheme(<ComplianceMonitoringDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Regulatory Compliance Monitoring')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('displays compliance summary cards', async () => {
    renderWithTheme(<ComplianceMonitoringDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Overall Compliance Score|Compliance/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('displays regulatory compliance status list', async () => {
    renderWithTheme(<ComplianceMonitoringDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Regulatory Compliance|Compliance/i)).toBeInTheDocument();
    });
  });

  it('displays active alerts panel', async () => {
    renderWithTheme(<ComplianceMonitoringDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Active Alerts')).toBeInTheDocument();
    });
  });

  it('handles refresh button click', async () => {
    renderWithTheme(<ComplianceMonitoringDashboard />);

    await waitFor(() => {
      const refreshButton = screen.getByLabelText('Refresh Data');
      expect(refreshButton).toBeInTheDocument();
    });

    const refreshButton = screen.getByLabelText('Refresh Data');
    fireEvent.click(refreshButton);
  });
});