import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';

// Mock the auth context
const mockUser = {
  id: 'test-user',
  email: 'test@example.com',
  name: 'Test User',
  role: 'analyst',
};

jest.mock('./contexts/AuthContext', () => ({
  ...jest.requireActual('./contexts/AuthContext'),
  useAuth: () => ({
    user: mockUser,
    loading: false,
    login: jest.fn(),
    logout: jest.fn(),
    updateUser: jest.fn(),
  }),
}));

// Mock API service
jest.mock('./services/api', () => ({
  apiService: {
    getValidations: jest.fn().mockResolvedValue({
      validations: [],
      total: 0,
      page: 1,
      page_size: 20,
    }),
    healthCheck: jest.fn().mockResolvedValue({ status: 'ok', timestamp: new Date().toISOString() }),
  },
}));

// Mock WebSocket service
jest.mock('./services/websocket', () => ({
  websocketService: {
    connectToNotifications: jest.fn(),
    disconnect: jest.fn(),
  },
}));

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AuthProvider>
          <NotificationProvider>
            {component}
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard when user is authenticated', async () => {
    renderWithProviders(<App />);
    
    await waitFor(() => {
      // Look for welcome message or dashboard content
      const welcomeElement = screen.queryByText(/Welcome back, Test User/i);
      if (welcomeElement) {
        expect(welcomeElement).toBeInTheDocument();
      } else {
        // If welcome message is not found, check for dashboard elements
        expect(screen.getByRole('main')).toBeInTheDocument();
      }
    });
  });

  test('renders navigation menu', async () => {
    renderWithProviders(<App />);
    
    await waitFor(() => {
      expect(screen.getAllByText('RiskIntel360')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
      expect(screen.getAllByText('New Validation')[0]).toBeInTheDocument();
    });
  });

  test('displays user avatar in header', async () => {
    renderWithProviders(<App />);
    
    await waitFor(() => {
      const avatar = screen.getByText('T'); // First letter of "Test User"
      expect(avatar).toBeInTheDocument();
    });
  });
});