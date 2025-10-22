/**
 * RiskIntel360 Design System - Main Index
 * Central export for the entire design system
 */

// Design tokens
export * from './tokens';

// Theme system
export * from './theme/theme';
export { ThemeProvider, useTheme, useThemeMode, useThemeColors, useFinancialTheme } from './theme/ThemeProvider';

// Components
export * from './components';

// Utilities
export * from './utils';

// Version
export const DESIGN_SYSTEM_VERSION = '1.0.0';

// Design system configuration
export const designSystemConfig = {
  name: 'RiskIntel360 Design System',
  version: DESIGN_SYSTEM_VERSION,
  description: 'Modern design system for fintech applications with WCAG 2.1 AA compliance',
  features: [
    'Comprehensive design tokens',
    'Light/dark theme support',
    'Responsive grid system',
    'Accessibility utilities',
    'Financial-specific components',
    'Animation system',
    'TypeScript support',
  ],
} as const;