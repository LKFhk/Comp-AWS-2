/**
 * RiskIntel360 Design System - Loading State Component
 * Consistent loading states for different UI contexts
 */

import React from 'react';
import {
  Box,
  CircularProgress,
  LinearProgress,
  Skeleton,
  Typography,
  Card,
  CardContent,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useTheme } from '../../theme/ThemeProvider';

// Loading state props
export interface LoadingStateProps {
  variant?: 'spinner' | 'linear' | 'skeleton' | 'card' | 'dashboard' | 'table' | 'chart';
  size?: 'small' | 'medium' | 'large';
  message?: string;
  fullHeight?: boolean;
  rows?: number;
  columns?: number;
  showProgress?: boolean;
  progress?: number;
}

// Styled loading container
const LoadingContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'fullHeight',
})<{ fullHeight?: boolean }>(
  ({ theme, fullHeight }) => ({
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing(3),
    minHeight: fullHeight ? '100vh' : '200px',
    gap: theme.spacing(2),
  })
);

// Spinner loading component
const SpinnerLoading: React.FC<LoadingStateProps> = ({
  size = 'medium',
  message,
  fullHeight,
  showProgress,
  progress,
}) => {
  const spinnerSize = {
    small: 24,
    medium: 40,
    large: 56,
  }[size];

  return (
    <LoadingContainer fullHeight={fullHeight}>
      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress size={spinnerSize} />
        {showProgress && progress !== undefined && (
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography
              variant="caption"
              component="div"
              color="textSecondary"
              sx={{ fontSize: size === 'small' ? '0.6rem' : '0.75rem' }}
            >
              {`${Math.round(progress)}%`}
            </Typography>
          </Box>
        )}
      </Box>
      {message && (
        <Typography
          variant={size === 'small' ? 'body2' : 'body1'}
          color="textSecondary"
          textAlign="center"
        >
          {message}
        </Typography>
      )}
    </LoadingContainer>
  );
};

// Linear loading component
const LinearLoading: React.FC<LoadingStateProps> = ({
  message,
  showProgress,
  progress,
}) => {
  return (
    <Box sx={{ width: '100%', p: 2 }}>
      {message && (
        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
          {message}
        </Typography>
      )}
      <LinearProgress
        variant={showProgress && progress !== undefined ? 'determinate' : 'indeterminate'}
        value={progress}
        sx={{ height: 6, borderRadius: 3 }}
      />
      {showProgress && progress !== undefined && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5 }}>
          {`${Math.round(progress)}% complete`}
        </Typography>
      )}
    </Box>
  );
};

// Skeleton loading component
const SkeletonLoading: React.FC<LoadingStateProps> = ({
  rows = 3,
  size = 'medium',
}) => {
  const skeletonHeight = {
    small: 16,
    medium: 20,
    large: 24,
  }[size];

  return (
    <Box sx={{ p: 2 }}>
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton
          key={index}
          variant="text"
          height={skeletonHeight}
          sx={{
            mb: 1,
            width: index === 0 ? '60%' : index === rows - 1 ? '40%' : '80%',
          }}
        />
      ))}
    </Box>
  );
};

// Card loading component
const CardLoading: React.FC<LoadingStateProps> = ({
  size = 'medium',
}) => {
  const cardHeight = {
    small: 120,
    medium: 160,
    large: 200,
  }[size];

  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="60%" height={24} />
        <Skeleton variant="text" width="40%" height={20} sx={{ mt: 1 }} />
        <Skeleton variant="rectangular" height={cardHeight - 80} sx={{ mt: 2 }} />
      </CardContent>
    </Card>
  );
};

// Dashboard loading component
const DashboardLoading: React.FC<LoadingStateProps> = () => {
  return (
    <Box sx={{ p: 3 }}>
      {/* Header skeleton */}
      <Box sx={{ mb: 3 }}>
        <Skeleton variant="text" width="30%" height={32} />
        <Skeleton variant="text" width="50%" height={20} sx={{ mt: 1 }} />
      </Box>

      {/* KPI cards skeleton */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2, mb: 3 }}>
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardContent>
              <Skeleton variant="text" width="40%" height={20} />
              <Skeleton variant="text" width="60%" height={40} sx={{ mt: 1 }} />
              <Skeleton variant="text" width="30%" height={16} sx={{ mt: 1 }} />
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Chart skeleton */}
      <Card>
        <CardContent>
          <Skeleton variant="text" width="25%" height={24} />
          <Skeleton variant="rectangular" height={300} sx={{ mt: 2 }} />
        </CardContent>
      </Card>
    </Box>
  );
};

// Table loading component
const TableLoading: React.FC<LoadingStateProps> = ({
  rows = 5,
  columns = 4,
}) => {
  return (
    <Box sx={{ p: 2 }}>
      {/* Table header */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} variant="text" width="100%" height={24} />
        ))}
      </Box>
      
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <Box key={rowIndex} sx={{ display: 'flex', gap: 2, mb: 1 }}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} variant="text" width="100%" height={20} />
          ))}
        </Box>
      ))}
    </Box>
  );
};

// Chart loading component
const ChartLoading: React.FC<LoadingStateProps> = ({
  size = 'medium',
  message,
}) => {
  const chartHeight = {
    small: 200,
    medium: 300,
    large: 400,
  }[size];

  return (
    <Box sx={{ p: 2 }}>
      <Skeleton variant="text" width="30%" height={24} sx={{ mb: 2 }} />
      <Skeleton variant="rectangular" height={chartHeight} />
      {message && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
          {message}
        </Typography>
      )}
    </Box>
  );
};

// Main loading state component
export const LoadingState = (props: LoadingStateProps) => {
  const { variant = 'spinner' } = props;

  switch (variant) {
    case 'linear':
      return <LinearLoading {...props} />;
    case 'skeleton':
      return <SkeletonLoading {...props} />;
    case 'card':
      return <CardLoading {...props} />;
    case 'dashboard':
      return <DashboardLoading {...props} />;
    case 'table':
      return <TableLoading {...props} />;
    case 'chart':
      return <ChartLoading {...props} />;
    case 'spinner':
    default:
      return <SpinnerLoading {...props} />;
  }
};

export default LoadingState;