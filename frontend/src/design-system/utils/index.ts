/**
 * RiskIntel360 Design System - Utilities Index
 * Central export for all design system utilities
 */

export { a11y, default as accessibility } from './accessibility';
export { animations, default as animationUtils } from './animations';
export * from './fintechIcons';
export * from './fintechVisualizations';

// Re-export commonly used utilities
export {
  // Accessibility
  getContrastRatio,
  meetsContrastRequirement,
  createFocusTrap,
  restoreFocus,
  generateId,
  announceToScreenReader,
  formatCurrencyForScreenReader,
  formatPercentageForScreenReader,
  formatRiskLevelForScreenReader,
  respectsReducedMotion,
  getAnimationDuration,
} from './accessibility';

export {
  // Animations
  durations,
  easing,
  createTransition,
  createAnimation,
  hoverLift,
  hoverScale,
  hoverGlow,
  pressEffect,
  numberCountUp,
  trendIndicator,
  chartAnimation,
  progressAnimation,
  staggerChildren,
  pageTransitions,
} from './animations';

// Fintech Icons
export {
  fintechIcons,
  getFraudIcon,
  getComplianceIcon,
  getRiskIcon,
  getMarketIcon,
  getKYCIcon,
  iconSizes,
  getIconSize,
} from './fintechIcons';

// Fintech Visualizations
export {
  riskMatrix,
  getRiskMatrixColor,
  getRiskMatrixLevel,
  getComplianceGaugeConfig,
  getCreditScoreGaugeConfig,
  getFraudHeatmapColor,
  getRiskLevelColor,
  getComplianceStatusColor,
  getMarketTrendColor,
  getFraudLevelColor,
  chartColorPalettes,
  getChartColorPalette,
  complianceGaugeConfig,
  creditScoreGaugeConfig,
  formatPercentage,
  formatCurrency,
  formatLargeNumber,
  getRiskScoreLabel,
  getComplianceScoreLabel,
} from './fintechVisualizations';