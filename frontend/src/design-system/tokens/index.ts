/**
 * RiskIntel360 Design System - Token Index
 * Central export for all design tokens
 */

import { colors } from './colors';
import { typography } from './typography';
import { spacing } from './spacing';
import { breakpoints } from './breakpoints';
import { shadows } from './shadows';

export { colors, type ColorToken, type ColorScale } from './colors';
export { typography, type TypographyToken, type FontSize, type FontWeight, type LineHeight } from './typography';
export { spacing, type SpacingToken, type SpacingScale } from './spacing';
export { breakpoints, createMediaQuery, isBreakpointUp, isBreakpointDown, type BreakpointToken, type Breakpoint } from './breakpoints';
export { shadows, type ShadowToken, type ElevationLevel } from './shadows';

// Combined design tokens
export const designTokens = {
  colors,
  typography,
  spacing,
  breakpoints,
  shadows,
} as const;

export type DesignTokens = typeof designTokens;