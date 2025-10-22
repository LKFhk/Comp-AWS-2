import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '../services/api';

interface UserPreferences {
  theme?: 'light' | 'dark' | 'auto';
  notifications?: {
    email?: boolean;
    push?: boolean;
    validationComplete?: boolean;
    weeklyReport?: boolean;
    fraudAlerts?: boolean;
    complianceAlerts?: boolean;
  };
  defaultAnalysisScope?: string[];
  defaultPriority?: 'low' | 'medium' | 'high';
  language?: string;
  timezone?: string;
  onboardingCompleted?: boolean;
  defaultDashboard?: string;
  refreshInterval?: number;
  compactMode?: boolean;
  showTutorials?: boolean;
  enableAnimations?: boolean;
}

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions?: string[];
  preferences?: UserPreferences;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing authentication on app load
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        
        if (token) {
          // Set the token in API client
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // Verify token and get user info
          const response = await apiClient.get('/api/v1/auth/me');
          setUser(response.data);
        }
      } catch (error: any) {
        console.error('Auth initialization failed:', error);
        // Clear invalid token
        localStorage.removeItem('auth_token');
        delete apiClient.defaults.headers.common['Authorization'];
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      
      // Call the actual login API
      const response = await apiClient.post('/api/v1/auth/login', {
        email,
        password,
      });
      
      const { user: userData, token } = response.data;
      
      // Store token and set in API client
      localStorage.setItem('auth_token', token);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setUser(userData);
    } catch (error: any) {
      console.error('Login failed:', error);
      // Clear any existing token
      localStorage.removeItem('auth_token');
      delete apiClient.defaults.headers.common['Authorization'];
      throw new Error(error.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('auth_token');
    delete apiClient.defaults.headers.common['Authorization'];
  };

  const updateUser = (updates: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...updates });
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};