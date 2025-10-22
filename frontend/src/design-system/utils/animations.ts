/**
 * RiskIntel360 Design System - Animation Utilities
 * Consistent animations and micro-interactions
 */

import { keyframes } from '@mui/material/styles';
import { respectsReducedMotion } from './accessibility';

// Animation durations (in milliseconds)
export const durations = {
  shortest: 150,
  shorter: 200,
  short: 250,
  standard: 300,
  complex: 375,
  enteringScreen: 225,
  leavingScreen: 195,
} as const;

// Easing functions
export const easing = {
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  // Financial-specific easing
  smooth: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
} as const;

// Keyframe animations
export const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const fadeOut = keyframes`
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-20px);
  }
`;

export const slideInLeft = keyframes`
  from {
    opacity: 0;
    transform: translateX(-100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

export const slideInRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

export const slideInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const slideInDown = keyframes`
  from {
    opacity: 0;
    transform: translateY(-100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const scaleIn = keyframes`
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

export const scaleOut = keyframes`
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.8);
  }
`;

export const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

export const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
`;

export const bounce = keyframes`
  0%, 20%, 53%, 80%, 100% {
    animation-timing-function: cubic-bezier(0.215, 0.61, 0.355, 1);
    transform: translate3d(0, 0, 0);
  }
  40%, 43% {
    animation-timing-function: cubic-bezier(0.755, 0.05, 0.855, 0.06);
    transform: translate3d(0, -30px, 0);
  }
  70% {
    animation-timing-function: cubic-bezier(0.755, 0.05, 0.855, 0.06);
    transform: translate3d(0, -15px, 0);
  }
  90% {
    transform: translate3d(0, -4px, 0);
  }
`;

export const shake = keyframes`
  10%, 90% {
    transform: translate3d(-1px, 0, 0);
  }
  20%, 80% {
    transform: translate3d(2px, 0, 0);
  }
  30%, 50%, 70% {
    transform: translate3d(-4px, 0, 0);
  }
  40%, 60% {
    transform: translate3d(4px, 0, 0);
  }
`;

// Financial-specific animations
export const countUp = keyframes`
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
`;

export const trendUp = keyframes`
  from {
    transform: translateY(10px) rotate(-5deg);
    opacity: 0;
  }
  to {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
`;

export const trendDown = keyframes`
  from {
    transform: translateY(-10px) rotate(5deg);
    opacity: 0;
  }
  to {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
`;

export const chartDraw = keyframes`
  from {
    stroke-dashoffset: 1000;
  }
  to {
    stroke-dashoffset: 0;
  }
`;

export const progressFill = keyframes`
  from {
    width: 0%;
  }
  to {
    width: var(--progress-width, 100%);
  }
`;

// Animation utility functions
export const createTransition = (
  property: string | string[],
  duration: keyof typeof durations = 'standard',
  easingFunction: keyof typeof easing = 'easeInOut',
  delay: number = 0
): string => {
  const props = Array.isArray(property) ? property : [property];
  const durationMs = respectsReducedMotion() ? 0 : durations[duration];
  
  return props
    .map(prop => `${prop} ${durationMs}ms ${easing[easingFunction]} ${delay}ms`)
    .join(', ');
};

export const createAnimation = (
  name: string,
  duration: keyof typeof durations = 'standard',
  easingFunction: keyof typeof easing = 'easeInOut',
  delay: number = 0,
  iterationCount: number | 'infinite' = 1,
  direction: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse' = 'normal',
  fillMode: 'none' | 'forwards' | 'backwards' | 'both' = 'both'
): string => {
  const durationMs = respectsReducedMotion() ? 0 : durations[duration];
  
  return `${name} ${durationMs}ms ${easing[easingFunction]} ${delay}ms ${iterationCount} ${direction} ${fillMode}`;
};

// Hover and interaction animations
export const hoverLift = {
  transition: createTransition(['transform', 'box-shadow']),
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08)',
  },
};

export const hoverScale = {
  transition: createTransition('transform'),
  '&:hover': {
    transform: 'scale(1.02)',
  },
};

export const hoverGlow = (color: string = 'rgba(33, 150, 243, 0.3)') => ({
  transition: createTransition('box-shadow'),
  '&:hover': {
    boxShadow: `0 0 20px ${color}`,
  },
});

export const pressEffect = {
  transition: createTransition('transform', 'shortest'),
  '&:active': {
    transform: 'scale(0.98)',
  },
};

// Loading animations
export const skeletonPulse = {
  animation: createAnimation('pulse', 'standard', 'easeInOut', 0, 'infinite'),
  animationKeyframes: pulse,
};

export const spinnerRotate = {
  animation: createAnimation('spin', 'standard', 'easeInOut', 0, 'infinite', 'normal'),
  animationKeyframes: spin,
};

// Financial data animations
export const numberCountUp = (duration: number = 1000) => ({
  animation: createAnimation('countUp', 'complex'),
  animationKeyframes: countUp,
});

export const trendIndicator = (direction: 'up' | 'down') => ({
  animation: createAnimation(direction === 'up' ? 'trendUp' : 'trendDown', 'standard'),
  animationKeyframes: direction === 'up' ? trendUp : trendDown,
});

export const chartAnimation = {
  strokeDasharray: 1000,
  strokeDashoffset: 1000,
  animation: createAnimation('chartDraw', 'complex', 'easeOut'),
  animationKeyframes: chartDraw,
};

export const progressAnimation = (width: string) => ({
  animation: createAnimation('progressFill', 'complex', 'easeOut'),
  animationKeyframes: progressFill,
  '--progress-width': width,
});

// Stagger animations for lists
export const staggerChildren = (delay: number = 50) => ({
  '& > *': {
    animation: createAnimation('fadeIn', 'standard', 'easeOut'),
    animationKeyframes: fadeIn,
  },
  '& > *:nth-child(1)': { animationDelay: `${delay * 0}ms` },
  '& > *:nth-child(2)': { animationDelay: `${delay * 1}ms` },
  '& > *:nth-child(3)': { animationDelay: `${delay * 2}ms` },
  '& > *:nth-child(4)': { animationDelay: `${delay * 3}ms` },
  '& > *:nth-child(5)': { animationDelay: `${delay * 4}ms` },
  '& > *:nth-child(6)': { animationDelay: `${delay * 5}ms` },
  '& > *:nth-child(7)': { animationDelay: `${delay * 6}ms` },
  '& > *:nth-child(8)': { animationDelay: `${delay * 7}ms` },
  '& > *:nth-child(9)': { animationDelay: `${delay * 8}ms` },
  '& > *:nth-child(10)': { animationDelay: `${delay * 9}ms` },
});

// Page transition animations
export const pageTransitions = {
  fadeIn: {
    animation: createAnimation('fadeIn', 'standard'),
    animationKeyframes: fadeIn,
  },
  slideInLeft: {
    animation: createAnimation('slideInLeft', 'standard'),
    animationKeyframes: slideInLeft,
  },
  slideInRight: {
    animation: createAnimation('slideInRight', 'standard'),
    animationKeyframes: slideInRight,
  },
  slideInUp: {
    animation: createAnimation('slideInUp', 'standard'),
    animationKeyframes: slideInUp,
  },
  slideInDown: {
    animation: createAnimation('slideInDown', 'standard'),
    animationKeyframes: slideInDown,
  },
  scaleIn: {
    animation: createAnimation('scaleIn', 'standard'),
    animationKeyframes: scaleIn,
  },
};

// Export all animations
export const animations = {
  // Keyframes
  fadeIn,
  fadeOut,
  slideInLeft,
  slideInRight,
  slideInUp,
  slideInDown,
  scaleIn,
  scaleOut,
  spin,
  pulse,
  bounce,
  shake,
  countUp,
  trendUp,
  trendDown,
  chartDraw,
  progressFill,
  
  // Utilities
  createTransition,
  createAnimation,
  
  // Interactions
  hoverLift,
  hoverScale,
  hoverGlow,
  pressEffect,
  
  // Loading
  skeletonPulse,
  spinnerRotate,
  
  // Financial
  numberCountUp,
  trendIndicator,
  chartAnimation,
  progressAnimation,
  
  // Layout
  staggerChildren,
  pageTransitions,
  
  // Constants
  durations,
  easing,
};

export default animations;