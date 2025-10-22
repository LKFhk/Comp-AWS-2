/**
 * Unit Tests for ProtectedRoute Component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ProtectedRoute, usePermissions } from '../ProtectedRoute';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the useAuth hook
jest.mock('../../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../../contexts/AuthContext'),
  useAuth: jest.fn(),
}));

const { useAuth } = require('../../../contexts/AuthContext');

describe('ProtectedRoute', () => {
  const mockNavigate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock useNavigate
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));
  });

  it('should render children when user has required role', () => {
    useAuth.mockReturnValue({
      user: { id: '1', name: 'Test User', email: 'test@example.com', role: 'admin' },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRoles={['admin']}>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should show access denied when user lacks required role', () => {
    useAuth.mockReturnValue({
      user: { id: '1', name: 'Test User', email: 'test@example.com', role: 'viewer' },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRoles={['admin']}>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should allow admin access to all routes', () => {
    useAuth.mockReturnValue({
      user: { id: '1', name: 'Admin User', email: 'admin@example.com', role: 'admin' },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRoles={['analyst', 'compliance_officer']}>
          <div>Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should render children when no roles are required', () => {
    useAuth.mockReturnValue({
      user: { id: '1', name: 'Test User', email: 'test@example.com', role: 'viewer' },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <div>Public Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Public Protected Content')).toBeInTheDocument();
  });

  it('should check permissions when provided', () => {
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'analyst',
        permissions: ['view_fraud', 'view_compliance'],
      },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredPermissions={['view_fraud']}>
          <div>Fraud Dashboard</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Fraud Dashboard')).toBeInTheDocument();
  });

  it('should deny access when user lacks required permissions', () => {
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'analyst',
        permissions: ['view_compliance'],
      },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredPermissions={['view_fraud', 'edit_fraud']}>
          <div>Fraud Dashboard</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
  });
});

describe('usePermissions hook', () => {
  it('should return correct permission checks', () => {
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'analyst',
        permissions: ['view_fraud', 'view_compliance'],
      },
    });

    const TestComponent = () => {
      const { hasRole, hasPermission, hasAnyRole } = usePermissions();
      return (
        <div>
          <div>{hasRole('analyst') ? 'Has Analyst Role' : 'No Analyst Role'}</div>
          <div>{hasPermission('view_fraud') ? 'Has Fraud Permission' : 'No Fraud Permission'}</div>
          <div>{hasAnyRole(['admin', 'analyst']) ? 'Has Any Role' : 'No Roles'}</div>
        </div>
      );
    };

    render(
      <BrowserRouter>
        <TestComponent />
      </BrowserRouter>
    );

    expect(screen.getByText('Has Analyst Role')).toBeInTheDocument();
    expect(screen.getByText('Has Fraud Permission')).toBeInTheDocument();
    expect(screen.getByText('Has Any Role')).toBeInTheDocument();
  });

  it('should grant all permissions to admin', () => {
    useAuth.mockReturnValue({
      user: {
        id: '1',
        name: 'Admin User',
        email: 'admin@example.com',
        role: 'admin',
        permissions: [],
      },
    });

    const TestComponent = () => {
      const { hasPermission, hasAllPermissions } = usePermissions();
      return (
        <div>
          <div>{hasPermission('any_permission') ? 'Has Permission' : 'No Permission'}</div>
          <div>{hasAllPermissions(['perm1', 'perm2']) ? 'Has All' : 'Missing Some'}</div>
        </div>
      );
    };

    render(
      <BrowserRouter>
        <TestComponent />
      </BrowserRouter>
    );

    expect(screen.getByText('Has Permission')).toBeInTheDocument();
    expect(screen.getByText('Has All')).toBeInTheDocument();
  });
});
