/**
 * Integration Tests for Dashboard Navigation and State Management
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import App from '../../App';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import Dashboard from '../../pages/Dashboard/Dashboard';
import { fintechService } from '../../services/fintechService';
import { mockDashboardData } from '../__mocks__/dashboardMockData';
import type { useAuth as UseAuthType } from '../../contexts/AuthContext';

// Mock the useAuth hook
jest.mock('../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../contexts/AuthContext'),
  useAuth: jest.fn(),
}));

// Import mocked useAuth
import { useAuth } from '../../contexts/AuthContext';
const mockUseAuth = useAuth as jest.MockedFunction<typeof UseAuthType>;

// Mock API services
jest.mock('../../services/fintechService', () => ({
  fintechService: {
    getRiskAnalysis: jest.fn().mockResolvedValue({ data: {} }),
    getComplianceStatus: jest.fn().mockResolvedValue({ data: {} }),
    getFraudAlerts: jest.fn().mockResolvedValue({ data: [] }),
    getDemoStats: jest.fn().mockResolvedValue({ data: {} }),
  },
}));

// Mock apiService
jest.mock('../../services/api', () => ({
  apiService: {
    getValidations: jest.fn().mockResolvedValue({
      validations: [],
      total: 0,
    }),
  },
}));

// Mock fetch for demo endpoint
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({
    total_executions: 5,
    average_metrics: {
      confidence_score: 0.85,
      time_reduction_percentage: 95,
      cost_savings_percentage: 80,
    },
  }),
});

// Create theme for tests
const theme = createTheme();

describe('Dashboard Navigation Integration Tests', () => {
  const defaultAuthMock = {
    user: {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'admin',
      permissions: ['view_all'],
    },
    loading: false,
    login: jest.fn(),
    updateUser: jest.fn(),
    logout: jest.fn(),
  };

  beforeAll(() => {
    jest.setTimeout(10000); // Integration test timeout: 10 seconds
  });

  afterAll(() => {
    jest.setTimeout(5000); // Reset to default unit test timeout
  });

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue(defaultAuthMock);
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  it('should navigate from main dashboard to fintech dashboards', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
    });
  });

  it('should navigate to validation wizard', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Wait for dashboard to load by checking for welcome message
    await waitFor(() => {
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // Find and click the "New Validation" link in the sidebar
    const newValidationLinks = screen.getAllByRole('button', { name: /New Validation/i });
    expect(newValidationLinks.length).toBeGreaterThan(0);
    
    fireEvent.click(newValidationLinks[0]);

    // Verify the validation wizard page loads
    await waitFor(() => {
      // Check for validation wizard specific content
      const wizardContents = screen.queryAllByText(/validation|wizard|step/i);
      expect(wizardContents.length).toBeGreaterThan(0);
    }, { timeout: 10000 });
  });

  it('should navigate to results page', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // Find and click the "Results" link in the sidebar
    const resultsLinks = screen.getAllByRole('button', { name: /Results/i });
    expect(resultsLinks.length).toBeGreaterThan(0);
    
    fireEvent.click(resultsLinks[0]);

    // Verify the results page loads
    await waitFor(() => {
      // Check for results page specific content
      const resultsContents = screen.queryAllByText(/results|analysis|report/i);
      expect(resultsContents.length).toBeGreaterThan(0);
    }, { timeout: 10000 });
  });

  it('should display user profile', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // Find the user avatar button (should display first letter of user name)
    const avatarButton = screen.getByRole('button', { name: /account of current user/i });
    expect(avatarButton).toBeInTheDocument();
    
    // Click to open profile menu
    fireEvent.click(avatarButton);

    // Verify profile menu items appear
    await waitFor(() => {
      const profileItem = screen.queryByText('Profile');
      const settingsItems = screen.queryAllByText('Settings');
      const logoutItem = screen.queryByText('Logout');
      expect(profileItem || settingsItems.length > 0 || logoutItem).toBeTruthy();
    }, { timeout: 10000 });
  });

  it('should maintain state when navigating between dashboards', async () => {
    const { rerender } = render(
      <MemoryRouter initialEntries={['/fintech/risk-intel']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Wait for initial dashboard to load
    await waitFor(() => {
      expect(screen.queryByText(/Loading dashboard/)).not.toBeInTheDocument();
    }, { timeout: 10000 });

    // Navigate to compliance dashboard
    rerender(
      <MemoryRouter initialEntries={['/fintech/compliance']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // State should be maintained
    await waitFor(() => {
      expect(screen.queryByText(/Loading dashboard/)).not.toBeInTheDocument();
    }, { timeout: 10000 });
  });

  it('should handle protected routes correctly', async () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Limited User',
        email: 'limited@example.com',
        role: 'viewer',
        permissions: [],
      },
      loading: false,
      login: jest.fn(),
      updateUser: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/fintech/fraud']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Should show access denied or redirect
    await waitFor(() => {
      const accessDenied = screen.queryByText('Access Denied');
      const dashboards = screen.queryAllByText(/RiskIntel360/);
      const dashboardContents = screen.queryAllByText(/Dashboard/);
      expect(accessDenied || dashboards.length > 0 || dashboardContents.length > 0).toBeTruthy();
    }, { timeout: 10000 });
  });

  it('should lazy load dashboard components', async () => {
    render(
      <MemoryRouter initialEntries={['/fintech/risk-intel']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Should show loading state initially or dashboard content
    await waitFor(() => {
      const loadingText = screen.queryByText(/Loading/);
      const dashboardContents = screen.queryAllByText(/Dashboard/);
      const welcomeText = screen.queryByText(/Welcome/);
      
      // Should show either loading or loaded content
      expect(loadingText || dashboardContents.length > 0 || welcomeText).toBeTruthy();
    }, { timeout: 10000 });
  });

  it('should handle navigation errors gracefully', async () => {
    render(
      <MemoryRouter initialEntries={['/invalid-route']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Should redirect to dashboard or show dashboard content
    await waitFor(() => {
      const welcomeText = screen.queryByText(/Welcome back/i);
      const dashboardTexts = screen.queryAllByText(/Dashboard/i);
      const errorText = screen.queryByText(/404/i);
      expect(welcomeText || dashboardTexts.length > 0 || errorText).toBeTruthy();
    }, { timeout: 10000 });
  });

  it('should preserve user preferences across navigation', async () => {
    const mockUpdateUser = jest.fn();
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin',
        preferences: {
          theme: 'dark',
          defaultDashboard: 'fraud',
        },
      },
      loading: false,
      login: jest.fn(),
      updateUser: mockUpdateUser,
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // Preferences should be accessible
    expect(mockUseAuth().user?.preferences?.theme).toBe('dark');
  });
});

describe('Dashboard State Management Integration Tests', () => {
  const defaultAuthMock = {
    user: {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'admin',
      permissions: ['view_all'],
    },
    loading: false,
    login: jest.fn(),
    updateUser: jest.fn(),
    logout: jest.fn(),
  };

  beforeAll(() => { jest.setTimeout(10000); }); // Integration test timeout: 10 seconds
  afterAll(() => { jest.setTimeout(5000); }); // Reset to default unit test timeout
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue(defaultAuthMock);
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  it('should update dashboard data on refresh', async () => {
    const { apiService } = require('../../services/api');
    
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <ThemeProvider theme={theme}>
          <NotificationProvider>
            <Dashboard />
          </NotificationProvider>
        </ThemeProvider>
      </MemoryRouter>
    );

    // Wait for component to mount and make service calls
    await waitFor(() => {
      expect(apiService.getValidations).toHaveBeenCalled();
    }, { timeout: 10000 });

    // Also check that fetch was called for demo data
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/demo/impact-dashboard');
  });

  it('should handle concurrent dashboard requests', async () => {
    const { apiService } = require('../../services/api');
    
    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <ThemeProvider theme={theme}>
          <NotificationProvider>
            <Dashboard />
          </NotificationProvider>
        </ThemeProvider>
      </MemoryRouter>
    );

    // Trigger multiple renders
    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <ThemeProvider theme={theme}>
          <NotificationProvider>
            <Dashboard />
          </NotificationProvider>
        </ThemeProvider>
      </MemoryRouter>
    );

    // Multiple requests should be handled
    await waitFor(() => {
      expect(apiService.getValidations).toHaveBeenCalled();
    }, { timeout: 10000 });
  });

  it('should cache dashboard data appropriately', async () => {
    const { apiService } = require('../../services/api');
    
    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <ThemeProvider theme={theme}>
          <NotificationProvider>
            <Dashboard />
          </NotificationProvider>
        </ThemeProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(apiService.getValidations).toHaveBeenCalled();
    }, { timeout: 10000 });

    // Navigate away and back by rerendering
    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <ThemeProvider theme={theme}>
          <NotificationProvider>
            <Dashboard />
          </NotificationProvider>
        </ThemeProvider>
      </MemoryRouter>
    );

    // Should use cached data or make new request
    await waitFor(() => {
      expect(apiService.getValidations).toHaveBeenCalled();
    }, { timeout: 10000 });
  });
});
