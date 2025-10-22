/**
 * RiskIntel360 Design System - Card Component
 * Enhanced card component with fintech-specific variants
 */

import React, { forwardRef } from 'react';
import {
  Card as MuiCard,
  CardProps as MuiCardProps,
  CardContent,
  CardHeader,
  CardActions,
  Typography,
  Box,
  Chip,
  IconButton,
  Skeleton,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { MoreVert as MoreVertIcon } from '@mui/icons-material';
import { useTheme } from '../../theme/ThemeProvider';

// Extended card props
export interface CardProps extends Omit<MuiCardProps, 'variant'> {
  variant?: 'default' | 'outlined' | 'elevated' | 'financial' | 'kpi' | 'alert' | 'dashboard';
  loading?: boolean;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  showMenu?: boolean;
  onMenuClick?: () => void;
  status?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  trend?: 'up' | 'down' | 'neutral';
  value?: string | number;
  change?: string | number;
  changePercent?: string | number;
  footer?: React.ReactNode;
  compact?: boolean;
  interactive?: boolean;
}

// Styled card with financial variants
const StyledCard = styled(MuiCard, {
  shouldForwardProp: (prop) => 
    !['variant', 'status', 'riskLevel', 'trend', 'interactive'].includes(prop as string),
})<CardProps>(({ theme, variant, status, riskLevel, trend, interactive }) => {
  const financialTheme = (theme as any).financial;
  
  let borderColor = 'transparent';
  let backgroundColor = theme.palette.background.paper;
  
  // Status-based styling
  if (status) {
    const statusColors = {
      success: theme.palette.success.main,
      warning: theme.palette.warning.main,
      error: theme.palette.error.main,
      info: theme.palette.info.main,
      neutral: theme.palette.grey[400],
    };
    borderColor = statusColors[status];
  }

  // Risk level styling
  if (riskLevel) {
    const riskColors = {
      low: financialTheme.colors.risk.low,
      medium: financialTheme.colors.risk.medium,
      high: financialTheme.colors.risk.high,
      critical: financialTheme.colors.risk.critical,
    };
    borderColor = riskColors[riskLevel];
  }

  // Trend-based styling
  if (trend && trend !== 'neutral') {
    borderColor = trend === 'up' 
      ? financialTheme.colors.market.bullish 
      : financialTheme.colors.market.bearish;
  }

  // Variant-specific styling
  const variantStyles = {
    default: {
      boxShadow: theme.shadows[1],
    },
    outlined: {
      border: `1px solid ${theme.palette.divider}`,
      boxShadow: 'none',
    },
    elevated: {
      boxShadow: theme.shadows[4],
    },
    financial: {
      border: `2px solid ${borderColor}`,
      boxShadow: theme.shadows[2],
      '&:hover': interactive ? {
        boxShadow: theme.shadows[4],
        transform: 'translateY(-2px)',
        transition: 'all 0.2s ease-in-out',
      } : {},
    },
    kpi: {
      border: `1px solid ${theme.palette.divider}`,
      borderLeft: `4px solid ${borderColor}`,
      boxShadow: theme.shadows[1],
      '&:hover': interactive ? {
        boxShadow: theme.shadows[3],
      } : {},
    },
    alert: {
      border: `2px solid ${borderColor}`,
      backgroundColor: theme.palette.mode === 'light' 
        ? `${borderColor}08` 
        : `${borderColor}12`,
      boxShadow: theme.shadows[2],
    },
    dashboard: {
      boxShadow: theme.shadows[2],
      '&:hover': interactive ? {
        boxShadow: theme.shadows[6],
        transform: 'translateY(-1px)',
        transition: 'all 0.2s ease-in-out',
      } : {},
    },
  };

  return {
    borderRadius: 12,
    transition: 'all 0.2s ease-in-out',
    cursor: interactive ? 'pointer' : 'default',
    ...variantStyles[variant || 'default'],
  };
});

// KPI value component
const KPIValue = styled(Typography)(({ theme }) => ({
  fontFamily: theme.typography.fontFamily,
  fontWeight: 700,
  fontSize: '2rem',
  lineHeight: 1.2,
}));

// Change indicator component
const ChangeIndicator = styled(Box)<{ trend?: 'up' | 'down' | 'neutral' }>(
  ({ theme, trend }) => {
    const financialTheme = (theme as any).financial;
    
    let color = theme.palette.text.secondary;
    if (trend === 'up') color = financialTheme.colors.market.bullish;
    if (trend === 'down') color = financialTheme.colors.market.bearish;
    
    return {
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing(0.5),
      color,
      fontSize: '0.875rem',
      fontWeight: 500,
    };
  }
);

// Card component
export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      variant = 'default',
      loading = false,
      title,
      subtitle,
      action,
      showMenu = false,
      onMenuClick,
      status,
      riskLevel,
      trend,
      value,
      change,
      changePercent,
      footer,
      compact = false,
      interactive = false,
      sx,
      ...props
    },
    ref
  ) => {
    const { theme } = useTheme();

    // Loading skeleton
    if (loading) {
      return (
        <StyledCard ref={ref} sx={sx} {...props}>
          <CardContent sx={{ p: compact ? 2 : 3 }}>
            {title && <Skeleton variant="text" width="60%" height={24} />}
            {subtitle && <Skeleton variant="text" width="40%" height={20} sx={{ mt: 1 }} />}
            <Skeleton variant="rectangular" height={60} sx={{ mt: 2 }} />
            {(change || changePercent) && (
              <Skeleton variant="text" width="30%" height={20} sx={{ mt: 1 }} />
            )}
          </CardContent>
        </StyledCard>
      );
    }

    // Header content
    const headerContent = (title || subtitle || action || showMenu) && (
      <CardHeader
        title={title}
        subheader={subtitle}
        action={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {action}
            {showMenu && (
              <IconButton
                size="small"
                onClick={onMenuClick}
                aria-label="card menu"
              >
                <MoreVertIcon />
              </IconButton>
            )}
          </Box>
        }
        sx={{
          pb: compact ? 1 : 2,
          '& .MuiCardHeader-title': {
            fontSize: compact ? '1rem' : '1.25rem',
            fontWeight: 600,
          },
          '& .MuiCardHeader-subheader': {
            fontSize: '0.875rem',
          },
        }}
      />
    );

    // KPI content for financial cards
    const kpiContent = (variant === 'kpi' || variant === 'financial') && value && (
      <Box sx={{ mb: 2 }}>
        <KPIValue color="textPrimary">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </KPIValue>
        {(change || changePercent) && (
          <ChangeIndicator trend={trend}>
            {change && (
              <Typography variant="body2" component="span">
                {typeof change === 'number' && change > 0 ? '+' : ''}
                {typeof change === 'number' ? change.toLocaleString() : change}
              </Typography>
            )}
            {changePercent && (
              <Typography variant="body2" component="span">
                ({typeof changePercent === 'number' && changePercent > 0 ? '+' : ''}
                {typeof changePercent === 'number' 
                  ? `${changePercent.toFixed(2)}%` 
                  : changePercent})
              </Typography>
            )}
          </ChangeIndicator>
        )}
      </Box>
    );

    // Status chip
    const statusChip = status && (
      <Chip
        label={status.charAt(0).toUpperCase() + status.slice(1)}
        color={status === 'neutral' ? 'default' : status}
        size="small"
        sx={{ mb: 1 }}
      />
    );

    // Risk level chip
    const riskChip = riskLevel && (
      <Chip
        label={`${riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk`}
        color={riskLevel === 'low' ? 'success' : riskLevel === 'medium' ? 'warning' : 'error'}
        size="small"
        sx={{ mb: 1 }}
      />
    );

    return (
      <StyledCard
        ref={ref}
        // @ts-ignore - Custom props for styled component
        variant={variant}
        status={status}
        riskLevel={riskLevel}
        trend={trend}
        interactive={interactive}
        sx={sx}
        {...props}
      >
        {headerContent}
        <CardContent sx={{ pt: headerContent ? 0 : undefined, p: compact ? 2 : 3 }}>
          {statusChip}
          {riskChip}
          {kpiContent}
          {children}
        </CardContent>
        {footer && (
          <CardActions sx={{ px: compact ? 2 : 3, pb: compact ? 2 : 3 }}>
            {footer}
          </CardActions>
        )}
      </StyledCard>
    );
  }
);

Card.displayName = 'Card';

export default Card;