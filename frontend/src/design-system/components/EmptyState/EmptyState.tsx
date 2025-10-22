/**
 * RiskIntel360 Design System - Empty State Component
 * Consistent empty states for different UI contexts
 */

import React from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  SvgIcon,
} from '@mui/material';
import {
  Inbox as InboxIcon,
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Security as SecurityIcon,
  AccountBalance as AccountBalanceIcon,
  Warning as WarningIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Empty state props
export interface EmptyStateProps {
  variant?: 'default' | 'search' | 'data' | 'error' | 'financial' | 'dashboard' | 'table';
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'contained' | 'outlined' | 'text';
    startIcon?: React.ReactNode;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
    variant?: 'contained' | 'outlined' | 'text';
    startIcon?: React.ReactNode;
  };
  size?: 'small' | 'medium' | 'large';
  fullHeight?: boolean;
  showCard?: boolean;
  illustration?: React.ReactNode;
}

// Styled container
const EmptyStateContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'fullHeight' && prop !== 'size',
})<{ 
  fullHeight?: boolean; 
  size?: 'small' | 'medium' | 'large' 
}>(({ theme, fullHeight, size }) => {
  const padding = {
    small: theme.spacing(2),
    medium: theme.spacing(4),
    large: theme.spacing(6),
  }[size || 'medium'];

  return {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    padding,
    minHeight: fullHeight ? '100vh' : size === 'small' ? '200px' : size === 'large' ? '400px' : '300px',
    color: theme.palette.text.secondary,
  };
});

// Icon container
const IconContainer = styled(Box)<{ size?: 'small' | 'medium' | 'large' }>(
  ({ theme, size }) => {
    const iconSize = {
      small: 48,
      medium: 64,
      large: 80,
    }[size || 'medium'];

    return {
      marginBottom: theme.spacing(2),
      '& .MuiSvgIcon-root': {
        fontSize: iconSize,
        color: theme.palette.text.disabled,
      },
    };
  }
);

// Get default icon based on variant
const getDefaultIcon = (variant: string) => {
  switch (variant) {
    case 'search':
      return <SearchIcon />;
    case 'data':
      return <AssessmentIcon />;
    case 'error':
      return <WarningIcon />;
    case 'financial':
      return <TrendingUpIcon />;
    case 'dashboard':
      return <AccountBalanceIcon />;
    case 'table':
      return <InboxIcon />;
    default:
      return <InboxIcon />;
  }
};

// Financial illustration component
const FinancialIllustration: React.FC<{ size?: 'small' | 'medium' | 'large' }> = ({ size = 'medium' }) => {
  const dimensions = {
    small: 120,
    medium: 160,
    large: 200,
  }[size];

  return (
    <SvgIcon
      sx={{
        width: dimensions,
        height: dimensions,
        mb: 2,
        color: 'text.disabled',
      }}
      viewBox="0 0 200 200"
    >
      {/* Simple financial chart illustration */}
      <rect x="20" y="20" width="160" height="160" fill="none" stroke="currentColor" strokeWidth="2" rx="8" />
      <line x1="40" y1="160" x2="40" y2="40" stroke="currentColor" strokeWidth="2" />
      <line x1="40" y1="160" x2="160" y2="160" stroke="currentColor" strokeWidth="2" />
      <polyline
        points="40,140 60,120 80,100 100,80 120,90 140,70 160,60"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="60" cy="120" r="3" fill="currentColor" />
      <circle cx="80" cy="100" r="3" fill="currentColor" />
      <circle cx="100" cy="80" r="3" fill="currentColor" />
      <circle cx="120" cy="90" r="3" fill="currentColor" />
      <circle cx="140" cy="70" r="3" fill="currentColor" />
      <circle cx="160" cy="60" r="3" fill="currentColor" />
    </SvgIcon>
  );
};

// Dashboard illustration component
const DashboardIllustration: React.FC<{ size?: 'small' | 'medium' | 'large' }> = ({ size = 'medium' }) => {
  const dimensions = {
    small: 120,
    medium: 160,
    large: 200,
  }[size];

  return (
    <SvgIcon
      sx={{
        width: dimensions,
        height: dimensions,
        mb: 2,
        color: 'text.disabled',
      }}
      viewBox="0 0 200 200"
    >
      {/* Dashboard grid illustration */}
      <rect x="20" y="20" width="160" height="160" fill="none" stroke="currentColor" strokeWidth="2" rx="8" />
      <rect x="30" y="30" width="70" height="50" fill="none" stroke="currentColor" strokeWidth="1" rx="4" />
      <rect x="110" y="30" width="60" height="50" fill="none" stroke="currentColor" strokeWidth="1" rx="4" />
      <rect x="30" y="90" width="60" height="80" fill="none" stroke="currentColor" strokeWidth="1" rx="4" />
      <rect x="100" y="90" width="70" height="80" fill="none" stroke="currentColor" strokeWidth="1" rx="4" />
      
      {/* Mini charts */}
      <line x1="35" y1="70" x2="95" y2="40" stroke="currentColor" strokeWidth="2" />
      <rect x="115" y="45" width="40" height="20" fill="currentColor" opacity="0.3" />
      <circle cx="60" cy="130" r="15" fill="none" stroke="currentColor" strokeWidth="2" />
      <rect x="110" y="110" width="50" height="40" fill="currentColor" opacity="0.2" />
    </SvgIcon>
  );
};

// Main empty state component
export const EmptyState: React.FC<EmptyStateProps> = ({
  variant = 'default',
  title,
  description,
  icon,
  action,
  secondaryAction,
  size = 'medium',
  fullHeight = false,
  showCard = false,
  illustration,
}) => {
  // Get appropriate illustration
  const getIllustration = () => {
    if (illustration) return illustration;
    
    switch (variant) {
      case 'financial':
        return <FinancialIllustration size={size} />;
      case 'dashboard':
        return <DashboardIllustration size={size} />;
      default:
        return null;
    }
  };

  // Content component
  const Content = (
    <EmptyStateContainer fullHeight={fullHeight} size={size}>
      {/* Illustration or Icon */}
      {getIllustration() || (
        <IconContainer size={size}>
          {icon || getDefaultIcon(variant)}
        </IconContainer>
      )}

      {/* Title */}
      <Typography
        variant={size === 'small' ? 'h6' : size === 'large' ? 'h4' : 'h5'}
        component="h2"
        gutterBottom
        sx={{
          fontWeight: 600,
          color: 'text.primary',
          mb: description ? 1 : 3,
        }}
      >
        {title}
      </Typography>

      {/* Description */}
      {description && (
        <Typography
          variant={size === 'small' ? 'body2' : 'body1'}
          color="textSecondary"
          sx={{
            mb: 3,
            maxWidth: size === 'small' ? 300 : size === 'large' ? 600 : 400,
            lineHeight: 1.6,
          }}
        >
          {description}
        </Typography>
      )}

      {/* Actions */}
      {(action || secondaryAction) && (
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            flexDirection: size === 'small' ? 'column' : 'row',
            alignItems: 'center',
          }}
        >
          {action && (
            <Button
              variant={action.variant || 'contained'}
              onClick={action.onClick}
              startIcon={action.startIcon}
              size={size === 'small' ? 'small' : 'medium'}
            >
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              variant={secondaryAction.variant || 'outlined'}
              onClick={secondaryAction.onClick}
              startIcon={secondaryAction.startIcon}
              size={size === 'small' ? 'small' : 'medium'}
            >
              {secondaryAction.label}
            </Button>
          )}
        </Box>
      )}
    </EmptyStateContainer>
  );

  // Wrap in card if requested
  if (showCard) {
    return (
      <Card>
        <CardContent sx={{ p: 0 }}>
          {Content}
        </CardContent>
      </Card>
    );
  }

  return Content;
};

// Preset empty states for common scenarios
export const NoDataEmptyState: React.FC<Omit<EmptyStateProps, 'variant' | 'title'>> = (props) => (
  <EmptyState
    variant="data"
    title="No financial data available"
    description="There's no financial risk data to display at the moment. Try adjusting your filters or initiate a new risk analysis."
    {...props}
  />
);

export const SearchEmptyState: React.FC<Omit<EmptyStateProps, 'variant' | 'title'>> = (props) => (
  <EmptyState
    variant="search"
    title="No financial risk analyses found"
    description="We couldn't find any risk analyses matching your search criteria. Try adjusting your search terms or filters."
    {...props}
  />
);

export const FinancialEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState
    variant="financial"
    {...props}
  />
);

export const DashboardEmptyState: React.FC<Omit<EmptyStateProps, 'variant'>> = (props) => (
  <EmptyState
    variant="dashboard"
    {...props}
  />
);

export default EmptyState;