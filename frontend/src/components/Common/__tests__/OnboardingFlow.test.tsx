/**
 * Unit Tests for OnboardingFlow Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { OnboardingFlow } from '../OnboardingFlow';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the useAuth hook
jest.mock('../../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../../contexts/AuthContext'),
  useAuth: jest.fn(),
}));

const { useAuth } = require('../../../contexts/AuthContext');

describe('OnboardingFlow', () => {
  const mockNavigate = jest.fn();
  const mockUpdateUser = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'analyst',
        preferences: {},
      },
      updateUser: mockUpdateUser,
    });

    // Mock useNavigate
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));
  });

  it('should render welcome dialog on mount', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    expect(screen.getByText('Welcome to RiskIntel360!')).toBeInTheDocument();
    expect(screen.getByText(/Would you like a quick tour/)).toBeInTheDocument();
  });

  it('should start tour when Start Tour button is clicked', async () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    const startButton = screen.getByText('Start Tour');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.queryByText('Welcome to RiskIntel360!')).not.toBeInTheDocument();
    });
  });

  it('should navigate through onboarding steps', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    // Close dialog first
    const startButton = screen.getByText('Start Tour');
    fireEvent.click(startButton);

    // Check first step
    expect(screen.getByText('AI-Powered Financial Risk Intelligence')).toBeInTheDocument();

    // Click next
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    // Should show second step
    expect(screen.getByText('Automated Regulatory Compliance')).toBeInTheDocument();
  });

  it('should allow going back to previous step', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    // Close dialog
    fireEvent.click(screen.getByText('Start Tour'));

    // Go to second step
    fireEvent.click(screen.getByText('Next'));

    // Verify we're on second step
    expect(screen.getByText('Automated Regulatory Compliance')).toBeInTheDocument();

    // Go back - use getAllByText and click the enabled one
    const backButtons = screen.getAllByText('Back');
    const enabledBackButton = backButtons.find(btn => !btn.hasAttribute('disabled'));
    if (enabledBackButton) {
      fireEvent.click(enabledBackButton);
    }

    // Should be back at first step
    expect(screen.getByText('AI-Powered Financial Risk Intelligence')).toBeInTheDocument();
  });

  it('should skip tour and navigate to dashboard', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    // Get all skip buttons and click the first one (from dialog)
    const skipButtons = screen.getAllByText('Skip Tour');
    fireEvent.click(skipButtons[0]);

    expect(mockUpdateUser).toHaveBeenCalledWith(
      expect.objectContaining({
        preferences: expect.objectContaining({
          onboardingCompleted: true,
        }),
      })
    );
  });

  it('should complete onboarding and navigate to risk intel dashboard', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    // Close dialog
    fireEvent.click(screen.getByText('Start Tour'));

    // Navigate to last step
    for (let i = 0; i < 5; i++) {
      fireEvent.click(screen.getByText('Next'));
    }

    // Complete onboarding
    const getStartedButton = screen.getByText('Get Started');
    fireEvent.click(getStartedButton);

    expect(mockUpdateUser).toHaveBeenCalledWith(
      expect.objectContaining({
        preferences: expect.objectContaining({
          onboardingCompleted: true,
        }),
      })
    );
  });

  it('should display correct features for each step', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    // Close dialog
    fireEvent.click(screen.getByText('Start Tour'));

    // Check first step features
    expect(screen.getByText(/Multi-agent AI architecture/)).toBeInTheDocument();
    expect(screen.getByText(/Real-time financial risk monitoring/)).toBeInTheDocument();

    // Go to fraud detection step
    fireEvent.click(screen.getByText('Next'));
    fireEvent.click(screen.getByText('Next'));

    // Check fraud detection features
    expect(screen.getByText(/Real-time transaction analysis/)).toBeInTheDocument();
    expect(screen.getByText(/90% false positive reduction/)).toBeInTheDocument();
  });

  it('should show step counter', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    // Close dialog
    fireEvent.click(screen.getByText('Start Tour'));

    expect(screen.getByText('1 of 6')).toBeInTheDocument();

    // Go to next step
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('2 of 6')).toBeInTheDocument();
  });

  it('should render action buttons for dashboards', () => {
    render(
      <BrowserRouter>
        <OnboardingFlow />
      </BrowserRouter>
    );

    // Close dialog
    fireEvent.click(screen.getByText('Start Tour'));

    // Go to compliance step (has action button)
    fireEvent.click(screen.getByText('Next'));

    expect(screen.getByText('View Compliance Dashboard')).toBeInTheDocument();
  });
});
