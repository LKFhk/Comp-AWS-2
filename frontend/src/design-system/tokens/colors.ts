/**
 * RiskIntel360 Design System - Color Tokens
 * Fintech-focused color palette with accessibility compliance
 */

export const colors = {
  // Primary Colors - Financial Blue Palette
  primary: {
    50: '#e3f2fd',
    100: '#bbdefb',
    200: '#90caf9',
    300: '#64b5f6',
    400: '#42a5f5',
    500: '#2196f3', // Main primary
    600: '#1e88e5',
    700: '#1976d2',
    800: '#1565c0',
    900: '#0d47a1',
  },

  // Secondary Colors - Financial Green (Success/Growth)
  secondary: {
    50: '#e8f5e8',
    100: '#c8e6c9',
    200: '#a5d6a7',
    300: '#81c784',
    400: '#66bb6a',
    500: '#4caf50', // Main secondary
    600: '#43a047',
    700: '#388e3c',
    800: '#2e7d32',
    900: '#1b5e20',
  },

  // Error Colors - Financial Red (Risk/Loss)
  error: {
    50: '#ffebee',
    100: '#ffcdd2',
    200: '#ef9a9a',
    300: '#e57373',
    400: '#ef5350',
    500: '#f44336', // Main error
    600: '#e53935',
    700: '#d32f2f',
    800: '#c62828',
    900: '#b71c1c',
  },

  // Warning Colors - Financial Orange (Caution)
  warning: {
    50: '#fff3e0',
    100: '#ffe0b2',
    200: '#ffcc80',
    300: '#ffb74d',
    400: '#ffa726',
    500: '#ff9800', // Main warning
    600: '#fb8c00',
    700: '#f57c00',
    800: '#ef6c00',
    900: '#e65100',
  },

  // Info Colors - Financial Cyan (Information)
  info: {
    50: '#e0f2f1',
    100: '#b2dfdb',
    200: '#80cbc4',
    300: '#4db6ac',
    400: '#26a69a',
    500: '#009688', // Main info
    600: '#00897b',
    700: '#00796b',
    800: '#00695c',
    900: '#004d40',
  },

  // Success Colors - Enhanced Green
  success: {
    50: '#e8f5e8',
    100: '#c8e6c9',
    200: '#a5d6a7',
    300: '#81c784',
    400: '#66bb6a',
    500: '#4caf50',
    600: '#43a047',
    700: '#388e3c',
    800: '#2e7d32',
    900: '#1b5e20',
  },

  // Neutral Colors - Professional Grays
  neutral: {
    0: '#ffffff',
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
    1000: '#000000',
  },

  // Financial Specific Colors
  financial: {
    // Market Colors
    bullish: '#4caf50', // Green for positive trends
    bearish: '#f44336', // Red for negative trends
    neutral: '#9e9e9e', // Gray for neutral/stable

    // Risk Level Colors
    riskLow: '#4caf50',
    riskMedium: '#ff9800',
    riskHigh: '#f44336',
    riskCritical: '#d32f2f',

    // Compliance Colors
    compliant: '#4caf50',
    nonCompliant: '#f44336',
    pending: '#ff9800',
    underReview: '#2196f3',

    // Fraud Detection Colors
    fraudHigh: '#d32f2f',
    fraudMedium: '#f44336',
    fraudLow: '#ff9800',
    fraudNone: '#4caf50',
  },

  // Background Colors
  background: {
    default: '#fafafa',
    paper: '#ffffff',
    elevated: '#ffffff',
    overlay: 'rgba(0, 0, 0, 0.5)',
  },

  // Text Colors
  text: {
    primary: 'rgba(0, 0, 0, 0.87)',
    secondary: 'rgba(0, 0, 0, 0.6)',
    disabled: 'rgba(0, 0, 0, 0.38)',
    hint: 'rgba(0, 0, 0, 0.38)',
    inverse: '#ffffff',
  },

  // Border Colors
  border: {
    light: '#e0e0e0',
    medium: '#bdbdbd',
    dark: '#757575',
    focus: '#2196f3',
  },

  // Dark Theme Colors
  dark: {
    background: {
      default: '#121212',
      paper: '#1e1e1e',
      elevated: '#2d2d2d',
      overlay: 'rgba(0, 0, 0, 0.7)',
    },
    text: {
      primary: 'rgba(255, 255, 255, 0.87)',
      secondary: 'rgba(255, 255, 255, 0.6)',
      disabled: 'rgba(255, 255, 255, 0.38)',
      hint: 'rgba(255, 255, 255, 0.38)',
      inverse: '#000000',
    },
    border: {
      light: '#333333',
      medium: '#555555',
      dark: '#777777',
      focus: '#64b5f6',
    },
  },
} as const;

export type ColorToken = typeof colors;
export type ColorScale = keyof typeof colors.primary;