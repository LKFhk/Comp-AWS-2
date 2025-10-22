import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CompetitionDemo from './CompetitionDemo';
import { 
  setupFetchMocks, 
  resetFetchMocks,
  mockDemoScenarios,
  mockShowcaseData,
  mockImpactDashboard,
  mockDemoStatus,
  mockExecutionResults
} from '../../tests/__mocks__/dashboardMockData';

// Setup fetch mocks
setupFetchMocks();

// Mock Chart.js - these will be rendered with data-testid attributes
jest.mock('react-chartjs-2', () => ({
  Line: (props: any) => <div data-testid="line-chart" {...props}>Line Chart</div>,
  Bar: (props: any) => <div data-testid="bar-chart" {...props}>Bar Chart</div>,
  Doughnut: (props: any) => <div data-testid="doughnut-chart" {...props}>Doughnut Chart</div>,
}));

describe('CompetitionDemo', () => {
  beforeAll(() => {
    jest.setTimeout(10000); // Integration test timeout: 10 seconds
  });

  afterAll(() => {
    jest.setTimeout(5000); // Reset to default unit test timeout
  });

  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
    // Setup default successful responses for all API calls
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoStatus
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoScenarios
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockShowcaseData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockImpactDashboard
      });
  });

  it('renders competition demo page', async () => {
    render(<CompetitionDemo />);

    expect(screen.getByText('AWS AI Agent Competition Demo')).toBeInTheDocument();
    expect(screen.getByText('RiskIntel360 - Autonomous Multi-Agent Financial Risk Validation Platform')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Competition Demo Scenarios')).toBeInTheDocument();
    });
  });

  it('loads and displays demo scenarios', async () => {
    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByText('SaaS Startup')).toBeInTheDocument();
    }, { timeout: 5000 });

    expect(screen.getByText('FinTech Expansion')).toBeInTheDocument();
    expect(screen.getByText('AI-powered customer service automation platform')).toBeInTheDocument();

    // Check complexity chips
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('displays AWS services and AgentCore primitives', async () => {
    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByText('AWS Services & Competition Requirements')).toBeInTheDocument();
    }, { timeout: 5000 });

    expect(screen.getByText('Amazon Bedrock Nova (Claude-3 family)')).toBeInTheDocument();
    expect(screen.getByText('Task Distribution')).toBeInTheDocument();
  });

  it('displays impact dashboard when executions exist', async () => {
    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByText('Measurable Impact Dashboard')).toBeInTheDocument();
    }, { timeout: 5000 });

    expect(screen.getByText('95.2%')).toBeInTheDocument(); // Time reduction
    expect(screen.getByText('82.1%')).toBeInTheDocument(); // Cost savings
  });

  it('executes demo scenario when button clicked', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoStatus
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoScenarios
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockShowcaseData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockImpactDashboard
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          execution_id: 'demo-saas-123',
          scenario: 'saas_startup',
          status: 'started'
        })
      });

    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByText('SaaS Startup')).toBeInTheDocument();
    }, { timeout: 5000 });

    const executeButtons = screen.getAllByText('Execute Demo');
    fireEvent.click(executeButtons[0]);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/demo/scenarios/saas_startup/execute', {
        method: 'POST'
      });
    }, { timeout: 5000 });
  });

  it('shows execution status when demo is running', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoStatus
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoScenarios
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockShowcaseData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockImpactDashboard
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          execution_id: 'demo-saas-123',
          scenario: 'saas_startup',
          status: 'started'
        })
      })
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          execution_id: 'demo-saas-123',
          status: 'running'
        })
      });

    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByText('SaaS Startup')).toBeInTheDocument();
    }, { timeout: 5000 });

    const executeButtons = screen.getAllByText('Execute Demo');
    fireEvent.click(executeButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Current Demo Execution')).toBeInTheDocument();
      expect(screen.getByText('Demo execution in progress. This typically takes 90-120 minutes to complete.')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('handles demo execution start', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoStatus
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoScenarios
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockShowcaseData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockImpactDashboard
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          execution_id: 'demo-saas-123',
          scenario: 'saas_startup',
          status: 'started'
        })
      });

    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByText('SaaS Startup')).toBeInTheDocument();
    }, { timeout: 5000 });

    const executeButtons = screen.getAllByText('Execute Demo');
    fireEvent.click(executeButtons[0]);

    // Wait for the execution to start
    await waitFor(() => {
      expect(screen.getByText('Current Demo Execution')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Verify the execution status is shown
    expect(screen.getByText('Demo execution in progress. This typically takes 90-120 minutes to complete.')).toBeInTheDocument();
  });

  it('renders charts when data is available', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoStatus
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoScenarios
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockShowcaseData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockImpactDashboard
      });

    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('handles API errors gracefully', async () => {
    (fetch as jest.Mock)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemoScenarios
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockShowcaseData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockImpactDashboard
      });

    // Should not crash when API calls fail
    render(<CompetitionDemo />);

    await waitFor(() => {
      expect(screen.getByText('AWS AI Agent Competition Demo')).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});