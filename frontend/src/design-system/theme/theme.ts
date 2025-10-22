/**
 * RiskIntel360 Design System - Theme System
 * Unified theme system with light/dark mode support
 */

import { createTheme, Theme, ThemeOptions } from '@mui/material/styles';
import { colors, typography, spacing, shadows, breakpoints } from '../tokens';

// Base theme configuration
const baseTheme: ThemeOptions = {
  breakpoints: {
    values: breakpoints.values,
  },
  spacing: (factor: number) => `${spacing.base * factor}px`,
  shape: {
    borderRadius: 8,
  },
  typography: {
    fontFamily: typography.fontFamily.primary,
    h1: {
      ...typography.scale.heading.h1,
      fontFamily: typography.fontFamily.primary,
    },
    h2: {
      ...typography.scale.heading.h2,
      fontFamily: typography.fontFamily.primary,
    },
    h3: {
      ...typography.scale.heading.h3,
      fontFamily: typography.fontFamily.primary,
    },
    h4: {
      ...typography.scale.heading.h4,
      fontFamily: typography.fontFamily.primary,
    },
    h5: {
      ...typography.scale.heading.h5,
      fontFamily: typography.fontFamily.primary,
    },
    h6: {
      ...typography.scale.heading.h6,
      fontFamily: typography.fontFamily.primary,
    },
    body1: {
      ...typography.scale.body.medium,
      fontFamily: typography.fontFamily.primary,
    },
    body2: {
      ...typography.scale.body.small,
      fontFamily: typography.fontFamily.primary,
    },
    caption: {
      ...typography.scale.caption.medium,
      fontFamily: typography.fontFamily.primary,
    },
    button: {
      ...typography.scale.button.medium,
      fontFamily: typography.fontFamily.primary,
    },
  },
  components: {
    // Button component overrides
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: typography.fontWeight.semibold,
          boxShadow: shadows.semantic.button.resting,
          '&:hover': {
            boxShadow: shadows.semantic.button.hover,
          },
          '&:active': {
            boxShadow: shadows.semantic.button.active,
          },
        },
        sizeSmall: {
          ...typography.scale.button.small,
          padding: `${spacing.component.button.paddingY.small} ${spacing.component.button.paddingX.small}`,
        },
        sizeMedium: {
          ...typography.scale.button.medium,
          padding: `${spacing.component.button.paddingY.medium} ${spacing.component.button.paddingX.medium}`,
        },
        sizeLarge: {
          ...typography.scale.button.large,
          padding: `${spacing.component.button.paddingY.large} ${spacing.component.button.paddingX.large}`,
        },
      },
    },

    // Card component overrides
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: shadows.semantic.card.resting,
          '&:hover': {
            boxShadow: shadows.semantic.card.hover,
          },
        },
      },
    },

    // Paper component overrides
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
        elevation1: {
          boxShadow: shadows.elevation[1],
        },
        elevation2: {
          boxShadow: shadows.elevation[2],
        },
        elevation3: {
          boxShadow: shadows.elevation[3],
        },
        elevation4: {
          boxShadow: shadows.elevation[4],
        },
        elevation6: {
          boxShadow: shadows.elevation[6],
        },
        elevation8: {
          boxShadow: shadows.elevation[8],
        },
        elevation12: {
          boxShadow: shadows.elevation[12],
        },
        elevation16: {
          boxShadow: shadows.elevation[16],
        },
        elevation24: {
          boxShadow: shadows.elevation[24],
        },
      },
    },

    // TextField component overrides
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderWidth: 2,
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderWidth: 2,
            },
          },
        },
      },
    },

    // Chip component overrides
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          fontWeight: typography.fontWeight.medium,
        },
      },
    },

    // AppBar component overrides
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: shadows.semantic.navigation.header,
        },
      },
    },

    // Drawer component overrides
    MuiDrawer: {
      styleOverrides: {
        paper: {
          boxShadow: shadows.semantic.navigation.sidebar,
        },
      },
    },

    // Menu component overrides
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: 8,
          boxShadow: shadows.semantic.dropdown.menu,
        },
      },
    },

    // Tooltip component overrides
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: 6,
          boxShadow: shadows.semantic.dropdown.tooltip,
          fontSize: typography.fontSize.sm,
        },
      },
    },

    // Dialog component overrides
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          boxShadow: shadows.semantic.modal.content,
        },
      },
    },

    // Table component overrides
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: spacing.component.table.cellPadding,
        },
        head: {
          padding: spacing.component.table.headerPadding,
          fontWeight: typography.fontWeight.semibold,
        },
      },
    },
  },
};

// Light theme configuration
const lightThemeOptions: ThemeOptions = {
  ...baseTheme,
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary[500],
      light: colors.primary[300],
      dark: colors.primary[700],
      contrastText: colors.text.inverse,
    },
    secondary: {
      main: colors.secondary[500],
      light: colors.secondary[300],
      dark: colors.secondary[700],
      contrastText: colors.text.inverse,
    },
    error: {
      main: colors.error[500],
      light: colors.error[300],
      dark: colors.error[700],
      contrastText: colors.text.inverse,
    },
    warning: {
      main: colors.warning[500],
      light: colors.warning[300],
      dark: colors.warning[700],
      contrastText: colors.text.primary,
    },
    info: {
      main: colors.info[500],
      light: colors.info[300],
      dark: colors.info[700],
      contrastText: colors.text.inverse,
    },
    success: {
      main: colors.success[500],
      light: colors.success[300],
      dark: colors.success[700],
      contrastText: colors.text.inverse,
    },
    grey: colors.neutral,
    background: {
      default: colors.background.default,
      paper: colors.background.paper,
    },
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
      disabled: colors.text.disabled,
    },
    divider: colors.border.light,
  },
};

// Dark theme configuration
const darkThemeOptions: ThemeOptions = {
  ...baseTheme,
  palette: {
    mode: 'dark',
    primary: {
      main: colors.primary[400],
      light: colors.primary[200],
      dark: colors.primary[600],
      contrastText: colors.dark.text.primary,
    },
    secondary: {
      main: colors.secondary[400],
      light: colors.secondary[200],
      dark: colors.secondary[600],
      contrastText: colors.dark.text.primary,
    },
    error: {
      main: colors.error[400],
      light: colors.error[200],
      dark: colors.error[600],
      contrastText: colors.dark.text.primary,
    },
    warning: {
      main: colors.warning[400],
      light: colors.warning[200],
      dark: colors.warning[600],
      contrastText: colors.dark.text.primary,
    },
    info: {
      main: colors.info[400],
      light: colors.info[200],
      dark: colors.info[600],
      contrastText: colors.dark.text.primary,
    },
    success: {
      main: colors.success[400],
      light: colors.success[200],
      dark: colors.success[600],
      contrastText: colors.dark.text.primary,
    },
    grey: colors.neutral,
    background: {
      default: colors.dark.background.default,
      paper: colors.dark.background.paper,
    },
    text: {
      primary: colors.dark.text.primary,
      secondary: colors.dark.text.secondary,
      disabled: colors.dark.text.disabled,
    },
    divider: colors.dark.border.light,
  },
  components: {
    ...baseTheme.components,
    // Dark theme specific component overrides
    MuiPaper: {
      styleOverrides: {
        ...baseTheme.components?.MuiPaper?.styleOverrides,
        elevation1: {
          boxShadow: shadows.dark.elevation[1],
        },
        elevation2: {
          boxShadow: shadows.dark.elevation[2],
        },
        elevation3: {
          boxShadow: shadows.dark.elevation[3],
        },
        elevation4: {
          boxShadow: shadows.dark.elevation[4],
        },
        elevation6: {
          boxShadow: shadows.dark.elevation[6],
        },
        elevation8: {
          boxShadow: shadows.dark.elevation[8],
        },
        elevation12: {
          boxShadow: shadows.dark.elevation[12],
        },
        elevation16: {
          boxShadow: shadows.dark.elevation[16],
        },
        elevation24: {
          boxShadow: shadows.dark.elevation[24],
        },
      },
    },
  },
};

// Create theme instances
export const lightTheme = createTheme(lightThemeOptions);
export const darkTheme = createTheme(darkThemeOptions);

// Financial-specific theme extensions
export const financialTheme = {
  colors: {
    risk: {
      low: colors.financial.riskLow,
      medium: colors.financial.riskMedium,
      high: colors.financial.riskHigh,
      critical: colors.financial.riskCritical,
    },
    market: {
      bullish: colors.financial.bullish,
      bearish: colors.financial.bearish,
      neutral: colors.financial.neutral,
    },
    compliance: {
      compliant: colors.financial.compliant,
      nonCompliant: colors.financial.nonCompliant,
      pending: colors.financial.pending,
      underReview: colors.financial.underReview,
    },
    fraud: {
      none: colors.financial.fraudNone,
      low: colors.financial.fraudLow,
      medium: colors.financial.fraudMedium,
      high: colors.financial.fraudHigh,
    },
  },
  typography: {
    financial: typography.scale.financial,
  },
  spacing: {
    financial: spacing.component.financial,
    dashboard: spacing.component.dashboard,
  },
  shadows: {
    financial: shadows.semantic.financial,
  },
};

// Theme type augmentation
declare module '@mui/material/styles' {
  interface Theme {
    financial: typeof financialTheme;
  }

  interface ThemeOptions {
    financial?: typeof financialTheme;
  }
}

// Add financial theme to both light and dark themes
lightTheme.financial = financialTheme;
darkTheme.financial = financialTheme;

export type RiskIntelTheme = Theme & {
  financial: typeof financialTheme;
};

export { baseTheme, lightThemeOptions, darkThemeOptions };