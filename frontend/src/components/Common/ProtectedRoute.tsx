/**
 * Protected Route Component with Role-Based Access Control
 * Ensures users have appropriate permissions to access specific dashboards
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { Box, Alert, Button, Typography } from '@mui/material';
import { Lock as LockIcon } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  fallbackPath?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  requiredPermissions = [],
  fallbackPath = '/dashboard',
}) => {
  const { user } = useAuth();

  // Check if user is authenticated
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Check role-based access
  const hasRequiredRole = requiredRoles.length === 0 || 
    requiredRoles.includes(user.role) ||
    user.role === 'admin'; // Admin has access to everything

  // Check permission-based access (if implemented)
  const hasRequiredPermissions = requiredPermissions.length === 0 || 
    requiredPermissions.every(permission => 
      user.permissions?.includes(permission)
    );

  // If user doesn't have required access, show access denied
  if (!hasRequiredRole || !hasRequiredPermissions) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          p: 3,
        }}
      >
        <LockIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
        <Typography variant="h4" gutterBottom>
          Access Denied
        </Typography>
        <Typography variant="body1" color="textSecondary" align="center" sx={{ mb: 3, maxWidth: 500 }}>
          You don't have permission to access this dashboard. 
          {requiredRoles.length > 0 && (
            <> Required roles: {requiredRoles.join(', ')}.</>
          )}
        </Typography>
        <Alert severity="warning" sx={{ mb: 3, maxWidth: 500 }}>
          Your current role: <strong>{user.role}</strong>
        </Alert>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            onClick={() => window.history.back()}
          >
            Go Back
          </Button>
          <Button
            variant="outlined"
            onClick={() => window.location.href = fallbackPath}
          >
            Go to Dashboard
          </Button>
        </Box>
      </Box>
    );
  }

  return <>{children}</>;
};

// Hook for checking permissions in components
export const usePermissions = () => {
  const { user } = useAuth();

  const hasRole = (role: string): boolean => {
    return user?.role === role || user?.role === 'admin';
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return roles.some(role => hasRole(role));
  };

  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) || user?.role === 'admin';
  };

  const hasAllPermissions = (permissions: string[]): boolean => {
    return permissions.every(permission => hasPermission(permission));
  };

  return {
    hasRole,
    hasAnyRole,
    hasPermission,
    hasAllPermissions,
    userRole: user?.role,
    userPermissions: user?.permissions || [],
  };
};
