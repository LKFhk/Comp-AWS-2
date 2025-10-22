/**
 * RiskIntel360 Design System - Button Component
 * Enhanced button component with fintech-specific variants
 */

import React, { forwardRef } from 'react';
import {
  Button as MuiButton,
  ButtonProps as MuiButtonProps,
  CircularProgress,
  Box,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useTheme } from '../../theme/ThemeProvider';

// Extended button props
export interface ButtonProps extends Omit<MuiButtonProps, 'variant'> {
  variant?: 'contained' | 'outlined' | 'text' | 'financial' | 'risk' | 'success' | 'warning' | 'error';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  loadingText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'start' | 'end';
  fullWidth?: boolean;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  financialAction?: 'buy' | 'sell' | 'hold' | 'alert';
}

// Styled button with financial variants
const StyledButton = styled(MuiButton, {
  shouldForwardProp: (prop) => 
    !['riskLevel', 'financialAction', 'loading', 'customVariant'].includes(prop as string),
})<ButtonProps & { customVariant?: string }>(({ theme, customVariant, riskLevel, financialAction }) => {
  const financialTheme = (theme as any).financial;
  
  // Financial variant styles
  if (customVariant === 'financial' && financialAction) {
    const actionColors = {
      buy: financialTheme.colors.market.bullish,
      sell: financialTheme.colors.market.bearish,
      hold: financialTheme.colors.market.neutral,
      alert: theme.palette.warning.main,
    };

    return {
      backgroundColor: actionColors[financialAction],
      color: theme.palette.getContrastText(actionColors[financialAction]),
      '&:hover': {
        backgroundColor: theme.palette.mode === 'light' 
          ? theme.palette.action.hover 
          : theme.palette.action.selected,
        filter: 'brightness(0.9)',
      },
      '&:active': {
        filter: 'brightness(0.8)',
      },
    };
  }

  // Risk variant styles
  if (customVariant === 'risk' && riskLevel) {
    const riskColors = {
      low: financialTheme.colors.risk.low,
      medium: financialTheme.colors.risk.medium,
      high: financialTheme.colors.risk.high,
      critical: financialTheme.colors.risk.critical,
    };

    return {
      backgroundColor: riskColors[riskLevel],
      color: theme.palette.getContrastText(riskColors[riskLevel]),
      '&:hover': {
        filter: 'brightness(0.9)',
      },
      '&:active': {
        filter: 'brightness(0.8)',
      },
    };
  }

  // Success variant
  if (customVariant === 'success') {
    return {
      backgroundColor: theme.palette.success.main,
      color: theme.palette.success.contrastText,
      '&:hover': {
        backgroundColor: theme.palette.success.dark,
      },
    };
  }

  // Warning variant
  if (customVariant === 'warning') {
    return {
      backgroundColor: theme.palette.warning.main,
      color: theme.palette.warning.contrastText,
      '&:hover': {
        backgroundColor: theme.palette.warning.dark,
      },
    };
  }

  // Error variant
  if (customVariant === 'error') {
    return {
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText,
      '&:hover': {
        backgroundColor: theme.palette.error.dark,
      },
    };
  }

  return {};
});

// Loading overlay component
const LoadingOverlay = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: 'rgba(255, 255, 255, 0.8)',
  borderRadius: 'inherit',
}));

// Button component
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'contained',
      size = 'medium',
      loading = false,
      loadingText,
      icon,
      iconPosition = 'start',
      disabled,
      riskLevel,
      financialAction,
      sx,
      ...props
    },
    ref
  ) => {
    const { theme } = useTheme();
    
    // Determine MUI variant for custom variants
    const muiVariant = ['financial', 'risk', 'success', 'warning', 'error'].includes(variant || '')
      ? 'contained'
      : (variant as 'contained' | 'outlined' | 'text');

    // Button content with icon
    const buttonContent = (
      <>
        {icon && iconPosition === 'start' && (
          <Box component="span" sx={{ mr: 1, display: 'flex', alignItems: 'center' }}>
            {icon}
          </Box>
        )}
        {loading && loadingText ? loadingText : children}
        {icon && iconPosition === 'end' && (
          <Box component="span" sx={{ ml: 1, display: 'flex', alignItems: 'center' }}>
            {icon}
          </Box>
        )}
      </>
    );

    return (
      <StyledButton
        ref={ref}
        variant={muiVariant}
        size={size}
        disabled={disabled || loading}
        // @ts-ignore - Custom props for styled component
        customVariant={variant}
        riskLevel={riskLevel}
        financialAction={financialAction}
        sx={{
          position: 'relative',
          ...sx,
        }}
        {...props}
      >
        {buttonContent}
        {loading && (
          <LoadingOverlay>
            <CircularProgress
              size={size === 'small' ? 16 : size === 'large' ? 24 : 20}
              color="inherit"
            />
          </LoadingOverlay>
        )}
      </StyledButton>
    );
  }
);

Button.displayName = 'Button';

export default Button;