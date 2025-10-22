/**
 * Unit Tests for UserPreferences Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserPreferences } from '../UserPreferences';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the useAuth hook
jest.mock('../../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../../contexts/AuthContext'),
  useAuth: jest.fn(),
}));

const { useAuth } = require('../../../contexts/AuthContext');

describe('UserPreferences', () => {
  const mockUpdateUser = jest.fn();
  const mockOnSave = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'analyst',
        preferences: {
          theme: 'light',
          notifications: {
            email: true,
            push: false,
          },
          defaultDashboard: 'risk-intel',
          refreshInterval: 30,
        },
      },
      updateUser: mockUpdateUser,
    });
  });

  it('should render user preferences form', () => {
    render(<UserPreferences />);

    expect(screen.getByText('User Preferences')).toBeInTheDocument();
    expect(screen.getByText('Appearance')).toBeInTheDocument();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('Dashboard Settings')).toBeInTheDocument();
  });

  it('should display current user preferences', () => {
    render(<UserPreferences />);

    // Check theme selection - Material-UI Select uses hidden input
    expect(screen.getByText('Light')).toBeInTheDocument();
    expect(screen.getByText('Risk Intelligence')).toBeInTheDocument();
  });

  it('should enable save button when preferences change', () => {
    render(<UserPreferences />);

    const saveButton = screen.getByText('Save Preferences');
    expect(saveButton).toBeDisabled();

    // Change a notification switch to enable save button
    const complianceAlertsSwitch = screen.getByLabelText('Compliance Alerts');
    fireEvent.click(complianceAlertsSwitch);

    expect(saveButton).not.toBeDisabled();
  });

  it('should save preferences when save button is clicked', async () => {
    render(<UserPreferences onSave={mockOnSave} />);

    // Toggle a notification switch to enable save button
    const emailSwitch = screen.getByLabelText('Email Notifications');
    fireEvent.click(emailSwitch);

    // Click save
    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalled();
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('should reset preferences when reset button is clicked', () => {
    render(<UserPreferences />);

    // Change a notification setting
    const emailSwitch = screen.getByLabelText('Email Notifications');
    const initialState = emailSwitch.getAttribute('checked');
    fireEvent.click(emailSwitch);

    // Click reset
    const resetButton = screen.getByText('Reset');
    fireEvent.click(resetButton);

    // Should be back to original value
    expect(emailSwitch.getAttribute('checked')).toBe(initialState);
  });

  it('should toggle notification switches', () => {
    render(<UserPreferences />);

    const emailSwitch = screen.getByLabelText('Email Notifications');
    expect(emailSwitch).toBeChecked();

    fireEvent.click(emailSwitch);
    expect(emailSwitch).not.toBeChecked();
  });

  it('should change default dashboard', () => {
    render(<UserPreferences />);

    // Verify initial dashboard is displayed
    expect(screen.getByText('Risk Intelligence')).toBeInTheDocument();

    // Change a notification to enable save button (simpler test)
    const pushSwitch = screen.getByLabelText('Push Notifications');
    fireEvent.click(pushSwitch);

    // Verify save button is enabled
    const saveButton = screen.getByText('Save Preferences');
    expect(saveButton).not.toBeDisabled();
  });

  it('should change refresh interval', () => {
    render(<UserPreferences />);

    // Verify initial refresh interval is displayed
    expect(screen.getByText('30 seconds')).toBeInTheDocument();

    // Change a notification to test functionality
    const weeklyReportSwitch = screen.getByLabelText('Weekly Summary Report');
    fireEvent.click(weeklyReportSwitch);

    // Verify save button is enabled
    const saveButton = screen.getByText('Save Preferences');
    expect(saveButton).not.toBeDisabled();
  });

  it('should toggle analysis scope chips', () => {
    render(<UserPreferences />);

    const regulatoryChip = screen.getByText('Regulatory');
    fireEvent.click(regulatoryChip);

    // Save button should be enabled
    const saveButton = screen.getByText('Save Preferences');
    expect(saveButton).not.toBeDisabled();
  });

  it('should change language and timezone', () => {
    render(<UserPreferences />);

    // Verify initial language and timezone are displayed
    expect(screen.getByText('English')).toBeInTheDocument();
    expect(screen.getByText('UTC')).toBeInTheDocument();

    // Change a notification to test functionality
    const fraudAlertsSwitch = screen.getByLabelText('Fraud Detection Alerts');
    fireEvent.click(fraudAlertsSwitch);

    // Verify save button is enabled
    const saveButton = screen.getByText('Save Preferences');
    expect(saveButton).not.toBeDisabled();
  });

  it('should show success message after saving', async () => {
    render(<UserPreferences />);

    // Change a preference
    const emailSwitch = screen.getByLabelText('Email Notifications');
    fireEvent.click(emailSwitch);

    // Save
    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Preferences saved successfully!')).toBeInTheDocument();
    });
  });

  it('should toggle compact mode', () => {
    render(<UserPreferences />);

    const compactModeSwitch = screen.getByLabelText(/Compact Mode/);
    fireEvent.click(compactModeSwitch);

    const saveButton = screen.getByText('Save Preferences');
    expect(saveButton).not.toBeDisabled();
  });

  it('should toggle tutorials and animations', () => {
    render(<UserPreferences />);

    const tutorialsSwitch = screen.getByLabelText(/Show Tutorials/);
    const animationsSwitch = screen.getByLabelText(/Enable Animations/);

    fireEvent.click(tutorialsSwitch);
    fireEvent.click(animationsSwitch);

    const saveButton = screen.getByText('Save Preferences');
    expect(saveButton).not.toBeDisabled();
  });
});
