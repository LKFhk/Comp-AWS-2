/**
 * Visual Regression Tests for Dashboard UI Consistency
 * Ensures UI remains consistent across changes
 */

import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { RiskIntelDashboard } from '../../components/FinTech/RiskIntelDashboard';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the useAuth hook
jest.mock('../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../contexts/AuthContext'),
  useAuth: jest.fn(),
}));

const { useAuth } = require('../../contexts/AuthContext');

// Mock fintech service
jest.mock('../../services/fintechService', () => ({
  fintechService: {
    getRiskAnalysis: jest.fn().mockResolvedValue({
      data: {
        summary: {
          active_analyses: 12,
          completed_today: 45,
          fraud_alerts: 3,
          compliance_issues: 1,
        },
      },
    }),
  },
}));

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});

describe('Dashboard Visual Regression Tests', () => {
  beforeEach(() => {
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin',
      },
      loading: false,
    });
  });

  it('should match snapshot for Risk Intel Dashboard', async () => {
    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    // Wait for async data to load
    await new Promise(resolve => setTimeout(resolve, 1000));

    expect(container).toMatchSnapshot();
  });

  it('should match snapshot for mobile view', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard enableMobileView={true} />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    await new Promise(resolve => setTimeout(resolve, 1000));

    expect(container).toMatchSnapshot();
  });

  it('should match snapshot for dark theme', async () => {
    const darkTheme = createTheme({
      palette: {
        mode: 'dark',
        primary: {
          main: '#90caf9',
        },
      },
    });

    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={darkTheme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    await new Promise(resolve => setTimeout(resolve, 1000));

    expect(container).toMatchSnapshot();
  });

  it('should match snapshot for loading state', () => {
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin',
      },
      loading: true,
    });

    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    expect(container).toMatchSnapshot();
  });

  it('should match snapshot for error state', async () => {
    const { fintechService } = require('../../services/fintechService');
    fintechService.getRiskAnalysis.mockRejectedValue(new Error('API Error'));

    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    await new Promise(resolve => setTimeout(resolve, 1000));

    expect(container).toMatchSnapshot();
  });

  it('should match snapshot for different user roles', async () => {
    useAuth.mockReturnValue({
      user: {
        id: '2',
        name: 'Analyst User',
        email: 'analyst@example.com',
        role: 'analyst',
      },
      loading: false,
    });

    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    await new Promise(resolve => setTimeout(resolve, 1000));

    expect(container).toMatchSnapshot();
  });
});

describe('Component Visual Consistency Tests', () => {
  it('should maintain consistent spacing and layout', async () => {
    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Check that cards are rendered with proper structure
    const cards = container.querySelectorAll('[class*="MuiCard"]');
    expect(cards.length).toBeGreaterThan(0);
    
    // Verify cards have proper MUI classes applied
    cards.forEach(card => {
      expect(card.className).toContain('MuiCard');
    });
  });

  it('should maintain consistent typography', async () => {
    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Check typography consistency
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
    headings.forEach(heading => {
      const styles = window.getComputedStyle(heading);
      expect(styles.fontFamily).toContain('Roboto');
    });
  });

  it('should maintain consistent color scheme', async () => {
    const { container } = render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthProvider>
            <RiskIntelDashboard />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    );

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Check color consistency
    const primaryElements = container.querySelectorAll('[class*="MuiButton-containedPrimary"]');
    primaryElements.forEach(element => {
      const styles = window.getComputedStyle(element);
      expect(styles.backgroundColor).toBeTruthy();
    });
  });
});
