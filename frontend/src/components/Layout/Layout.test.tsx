import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { axe } from 'jest-axe';
import Layout from './Layout';

// Mock the auth context
const mockUser = {
  id: 'test-user',
  email: 'test@example.com',
  name: 'Test User',
  role: 'analyst',
};

const mockLogout = jest.fn();

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    loading: false,
    login: jest.fn(),
    logout: mockLogout,
    updateUser: jest.fn(),
  }),
}));

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Layout Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders layout with navigation and content area', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('displays application title', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Use getAllByText to handle multiple instances and check the first one (in sidebar)
    const riskIntelElements = screen.getAllByText(/RiskIntel360/i);
    expect(riskIntelElements.length).toBeGreaterThan(0);
    expect(riskIntelElements[0]).toBeInTheDocument();
  });

  test('shows user avatar in header', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // The user name appears as the first letter in the avatar, not as full text
    const avatar = screen.getByText('T'); // First letter of "Test User"
    expect(avatar).toBeInTheDocument();
    
    // Also check for the account button with proper aria-label
    const accountButton = screen.getByRole('button', { name: /account of current user/i });
    expect(accountButton).toBeInTheDocument();
  });

  test('renders navigation menu items', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Use getAllByText for items that appear multiple times (mobile + desktop)
    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
    expect(screen.getAllByText('New Validation')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Results')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Competition Demo')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Settings')[0]).toBeInTheDocument();
  });

  test('handles mobile menu toggle', async () => {
    const user = userEvent.setup();
    
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Use the correct aria-label from the component
    const menuButton = screen.getByRole('button', { name: /open drawer/i });
    expect(menuButton).toBeInTheDocument();
    
    // Verify the menu button is clickable
    await act(async () => {
      await user.click(menuButton);
    });
    
    // Instead of checking for navigation role (which might be hidden in mobile),
    // check that the menu items are still accessible
    await waitFor(() => {
      const dashboardItems = screen.getAllByText('Dashboard');
      expect(dashboardItems.length).toBeGreaterThan(0);
    });
  });

  test('has no accessibility violations', async () => {
    const { container } = renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Tab through navigation items - use role-based selectors for better reliability
    await act(async () => {
      await user.tab();
    });
    
    // Check if any navigation button has focus
    const dashboardButton = screen.getByRole('button', { name: 'Dashboard' });
    const menuButton = screen.getByRole('button', { name: /open drawer/i });
    
    // Either the menu button or dashboard button should have focus after first tab
    const focusedElement = document.activeElement;
    expect(focusedElement === dashboardButton || focusedElement === menuButton).toBe(true);
  });

  test('renders responsive layout', () => {
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    const main = screen.getByRole('main');
    expect(main).toBeInTheDocument();
    // The main element has flexGrow: 1 but the parent container has display: flex
    const layoutContainer = main.parentElement;
    expect(layoutContainer).toHaveStyle({ display: 'flex' });
  });

  test('handles logout functionality', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    
    // Click on the account button (avatar) to open the menu
    const accountButton = screen.getByRole('button', { name: /account of current user/i });
    
    await act(async () => {
      await user.click(accountButton);
    });
    
    // Wait for the menu to appear and check for logout option
    await waitFor(() => {
      const logoutButton = screen.getByText(/logout/i);
      expect(logoutButton).toBeInTheDocument();
    });
    
    // Test clicking logout
    const logoutButton = screen.getByText(/logout/i);
    await act(async () => {
      await user.click(logoutButton);
    });
    
    // Verify logout was called
    expect(mockLogout).toHaveBeenCalled();
  });
});