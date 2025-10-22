/**
 * RiskIntel360 Design System - Fintech Visualization Utilities
 * Standardized visualization helpers for financial industry use cases
 */

import { colors } from '../tokens/colors';

/**
 * Risk Matrix Configuration (3x3 grid)
 * Standard financial industry risk assessment matrix
 */
export interface RiskMatrixCell {
  likelihood: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  color: string;
  label: string;
}

export const riskMatrix: RiskMatrixCell[][] = [
  // High Impact Row
  [
    { likelihood: 'low', impact: 'high', riskLevel: 'medium', color: colors.financial.riskMedium, label: 'Medium' },
    { likelihood: 'medium', impact: 'high', riskLevel: 'high', color: colors.financial.riskHigh, label: 'High' },
    { likelihood: 'high', impact: 'high', riskLevel: 'critical', color: colors.financial.riskCritical, label: 'Critical' },
  ],
  // Medium Impact Row
  [
    { likelihood: 'low', impact: 'medium', riskLevel: 'low', color: colors.financial.riskLow, label: 'Low' },
    { likelihood: 'medium', impact: 'medium', riskLevel: 'medium', color: colors.financial.riskMedium, label: 'Medium' },
    { likelihood: 'high', impact: 'medium', riskLevel: 'high', color: colors.financial.riskHigh, label: 'High' },
  ],
  // Low Impact Row
  [
    { likelihood: 'low', impact: 'low', riskLevel: 'low', color: colors.financial.riskLow, label: 'Low' },
    { likelihood: 'medium', impact: 'low', riskLevel: 'low', color: colors.financial.riskLow, label: 'Low' },
    { likelihood: 'high', impact: 'low', riskLevel: 'medium', color: colors.financial.riskMedium, label: 'Medium' },
  ],
];

/**
 * Get risk level color based on likelihood and impact
 */
export const getRiskMatrixColor = (likelihood: 'low' | 'medium' | 'high', impact: 'low' | 'medium' | 'high'): string => {
  const impactIndex = impact === 'high' ? 0 : impact === 'medium' ? 1 : 2;
  const likelihoodIndex = likelihood === 'low' ? 0 : likelihood === 'medium' ? 1 : 2;
  return riskMatrix[impactIndex][likelihoodIndex].color;
};

/**
 * Get risk level label based on likelihood and impact
 */
export const getRiskMatrixLevel = (likelihood: 'low' | 'medium' | 'high', impact: 'low' | 'medium' | 'high'): string => {
  const impactIndex = impact === 'high' ? 0 : impact === 'medium' ? 1 : 2;
  const likelihoodIndex = likelihood === 'low' ? 0 : likelihood === 'medium' ? 1 : 2;
  return riskMatrix[impactIndex][likelihoodIndex].riskLevel;
};

/**
 * Compliance Gauge Configuration
 * Standard compliance score visualization (0-100 scale)
 */
export interface ComplianceGaugeConfig {
  score: number;
  color: string;
  label: string;
  status: 'critical' | 'warning' | 'good' | 'excellent';
}

export const getComplianceGaugeConfig = (score: number): ComplianceGaugeConfig => {
  if (score < 50) {
    return {
      score,
      color: colors.financial.riskCritical,
      label: 'Critical',
      status: 'critical',
    };
  } else if (score < 70) {
    return {
      score,
      color: colors.financial.riskMedium,
      label: 'Needs Improvement',
      status: 'warning',
    };
  } else if (score < 90) {
    return {
      score,
      color: colors.financial.riskLow,
      label: 'Good',
      status: 'good',
    };
  } else {
    return {
      score,
      color: colors.financial.compliant,
      label: 'Excellent',
      status: 'excellent',
    };
  }
};

/**
 * Credit Score Gauge Configuration
 * Standard credit score visualization (300-850 scale)
 */
export interface CreditScoreGaugeConfig {
  score: number;
  color: string;
  label: string;
  category: 'poor' | 'fair' | 'good' | 'very-good' | 'excellent';
}

export const getCreditScoreGaugeConfig = (score: number): CreditScoreGaugeConfig => {
  if (score < 580) {
    return {
      score,
      color: colors.financial.riskCritical,
      label: 'Poor',
      category: 'poor',
    };
  } else if (score < 670) {
    return {
      score,
      color: colors.financial.riskMedium,
      label: 'Fair',
      category: 'fair',
    };
  } else if (score < 740) {
    return {
      score,
      color: colors.financial.riskLow,
      label: 'Good',
      category: 'good',
    };
  } else if (score < 800) {
    return {
      score,
      color: colors.financial.compliant,
      label: 'Very Good',
      category: 'very-good',
    };
  } else {
    return {
      score,
      color: colors.financial.compliant,
      label: 'Excellent',
      category: 'excellent',
    };
  }
};

/**
 * Fraud Heatmap Configuration
 * Color-coded transaction pattern visualization
 */
export interface FraudHeatmapCell {
  value: number; // 0-1 fraud probability
  color: string;
  label: string;
  level: 'none' | 'low' | 'medium' | 'high';
}

export const getFraudHeatmapColor = (fraudProbability: number): FraudHeatmapCell => {
  if (fraudProbability < 0.2) {
    return {
      value: fraudProbability,
      color: colors.financial.fraudNone,
      label: 'Safe',
      level: 'none',
    };
  } else if (fraudProbability < 0.5) {
    return {
      value: fraudProbability,
      color: colors.financial.fraudLow,
      label: 'Low Risk',
      level: 'low',
    };
  } else if (fraudProbability < 0.8) {
    return {
      value: fraudProbability,
      color: colors.financial.fraudMedium,
      label: 'Suspicious',
      level: 'medium',
    };
  } else {
    return {
      value: fraudProbability,
      color: colors.financial.fraudHigh,
      label: 'High Risk',
      level: 'high',
    };
  }
};

/**
 * Risk Level Color Utilities
 */
export const getRiskLevelColor = (level: 'low' | 'medium' | 'high' | 'critical'): string => {
  switch (level) {
    case 'low':
      return colors.financial.riskLow;
    case 'medium':
      return colors.financial.riskMedium;
    case 'high':
      return colors.financial.riskHigh;
    case 'critical':
      return colors.financial.riskCritical;
    default:
      return colors.neutral[500];
  }
};

/**
 * Compliance Status Color Utilities
 */
export const getComplianceStatusColor = (status: 'compliant' | 'nonCompliant' | 'pending' | 'underReview'): string => {
  switch (status) {
    case 'compliant':
      return colors.financial.compliant;
    case 'nonCompliant':
      return colors.financial.nonCompliant;
    case 'pending':
      return colors.financial.pending;
    case 'underReview':
      return colors.financial.underReview;
    default:
      return colors.neutral[500];
  }
};

/**
 * Market Trend Color Utilities
 */
export const getMarketTrendColor = (trend: 'bullish' | 'bearish' | 'neutral'): string => {
  switch (trend) {
    case 'bullish':
      return colors.financial.bullish;
    case 'bearish':
      return colors.financial.bearish;
    case 'neutral':
      return colors.financial.neutral;
    default:
      return colors.neutral[500];
  }
};

/**
 * Fraud Level Color Utilities
 */
export const getFraudLevelColor = (level: 'none' | 'low' | 'medium' | 'high'): string => {
  switch (level) {
    case 'none':
      return colors.financial.fraudNone;
    case 'low':
      return colors.financial.fraudLow;
    case 'medium':
      return colors.financial.fraudMedium;
    case 'high':
      return colors.financial.fraudHigh;
    default:
      return colors.neutral[500];
  }
};

/**
 * Chart Color Palettes for Financial Data
 */
export const chartColorPalettes = {
  // Risk assessment chart colors
  risk: [
    colors.financial.riskLow,
    colors.financial.riskMedium,
    colors.financial.riskHigh,
    colors.financial.riskCritical,
  ],
  
  // Compliance status chart colors
  compliance: [
    colors.financial.compliant,
    colors.financial.pending,
    colors.financial.underReview,
    colors.financial.nonCompliant,
  ],
  
  // Market trend chart colors
  market: [
    colors.financial.bullish,
    colors.financial.neutral,
    colors.financial.bearish,
  ],
  
  // Fraud detection chart colors
  fraud: [
    colors.financial.fraudNone,
    colors.financial.fraudLow,
    colors.financial.fraudMedium,
    colors.financial.fraudHigh,
  ],
  
  // General financial chart colors
  financial: [
    colors.primary[500],
    colors.secondary[500],
    colors.info[500],
    colors.warning[500],
    colors.error[500],
  ],
  
  // Multi-series chart colors (for comparing multiple metrics)
  multiSeries: [
    colors.primary[500],
    colors.secondary[500],
    colors.info[500],
    colors.warning[500],
    colors.error[500],
    colors.primary[300],
    colors.secondary[300],
    colors.info[300],
  ],
} as const;

/**
 * Get chart color palette by type
 */
export const getChartColorPalette = (type: keyof typeof chartColorPalettes): readonly string[] => {
  return chartColorPalettes[type];
};

/**
 * Gauge Chart Configuration
 * Standard configuration for gauge/speedometer charts
 */
export interface GaugeChartConfig {
  min: number;
  max: number;
  value: number;
  thresholds: {
    value: number;
    color: string;
    label: string;
  }[];
}

export const complianceGaugeConfig: GaugeChartConfig = {
  min: 0,
  max: 100,
  value: 0,
  thresholds: [
    { value: 50, color: colors.financial.riskCritical, label: 'Critical' },
    { value: 70, color: colors.financial.riskMedium, label: 'Warning' },
    { value: 90, color: colors.financial.riskLow, label: 'Good' },
    { value: 100, color: colors.financial.compliant, label: 'Excellent' },
  ],
};

export const creditScoreGaugeConfig: GaugeChartConfig = {
  min: 300,
  max: 850,
  value: 0,
  thresholds: [
    { value: 580, color: colors.financial.riskCritical, label: 'Poor' },
    { value: 670, color: colors.financial.riskMedium, label: 'Fair' },
    { value: 740, color: colors.financial.riskLow, label: 'Good' },
    { value: 800, color: colors.financial.compliant, label: 'Very Good' },
    { value: 850, color: colors.financial.compliant, label: 'Excellent' },
  ],
};

/**
 * Format percentage for display
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Format currency for display
 */
export const formatCurrency = (value: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

/**
 * Format large numbers with abbreviations (K, M, B)
 */
export const formatLargeNumber = (value: number): string => {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  } else if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  } else if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  } else {
    return value.toFixed(0);
  }
};

/**
 * Get risk score label
 */
export const getRiskScoreLabel = (score: number): string => {
  if (score < 25) return 'Low Risk';
  if (score < 50) return 'Medium Risk';
  if (score < 75) return 'High Risk';
  return 'Critical Risk';
};

/**
 * Get compliance score label
 */
export const getComplianceScoreLabel = (score: number): string => {
  if (score < 50) return 'Critical';
  if (score < 70) return 'Needs Improvement';
  if (score < 90) return 'Good';
  return 'Excellent';
};

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type ComplianceStatus = 'compliant' | 'nonCompliant' | 'pending' | 'underReview';
export type MarketTrend = 'bullish' | 'bearish' | 'neutral';
export type FraudLevel = 'none' | 'low' | 'medium' | 'high';
