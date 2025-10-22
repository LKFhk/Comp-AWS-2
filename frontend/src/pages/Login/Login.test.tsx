import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Login from './Login';

const theme = createTheme();

// Mock the auth context
const mockLogin = jest.fn();
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
  }),
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    mockLogin.mockClear();
  });

  test('renders login form', () => {
    renderWithTheme(<Login />);
    
    expect(screen.getByText('RiskIntel360')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /email address/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue('demo123')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('displays demo credentials', () => {
    renderWithTheme(<Login />);
    
    expect(screen.getByText(/Demo Credentials/i)).toBeInTheDocument();
    expect(screen.getByText(/demo@riskintel360\.com/)).toBeInTheDocument();
    expect(screen.getByText(/demo123/)).toBeInTheDocument();
  });

  test('pre-fills demo credentials', () => {
    renderWithTheme(<Login />);
    
    const emailInput = screen.getByRole('textbox', { name: /email address/i }) as HTMLInputElement;
    const passwordInput = screen.getByDisplayValue('demo123') as HTMLInputElement;
    
    expect(emailInput.value).toBe('demo@riskintel360.com');
    expect(passwordInput.value).toBe('demo123');
  });

  test('calls login function when form is submitted', async () => {
    const user = userEvent.setup();
    renderWithTheme(<Login />);
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('demo@riskintel360.com', 'demo123');
    });
  });

  test('toggles password visibility', async () => {
    const user = userEvent.setup();
    renderWithTheme(<Login />);
    
    const passwordInput = screen.getByDisplayValue('demo123') as HTMLInputElement;
    const toggleButton = screen.getByLabelText(/toggle password visibility/i);
    
    expect(passwordInput.type).toBe('password');
    
    await user.click(toggleButton);
    expect(passwordInput.type).toBe('text');
    
    await user.click(toggleButton);
    expect(passwordInput.type).toBe('password');
  });

  test('disables submit button when fields are empty', async () => {
    const user = userEvent.setup();
    renderWithTheme(<Login />);
    
    const emailInput = screen.getByRole('textbox', { name: /email address/i });
    const passwordInput = screen.getByDisplayValue('demo123');
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    // Clear the pre-filled values
    await user.clear(emailInput);
    await user.clear(passwordInput);
    
    expect(submitButton).toBeDisabled();
  });

  test('displays error message on login failure', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));
    
    renderWithTheme(<Login />);
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});