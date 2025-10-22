/**
 * RiskIntel360 Design System - Shadow Tokens
 * Elevation system for depth and hierarchy
 */

export const shadows = {
  // Base shadow system (Material Design inspired)
  elevation: {
    0: 'none',
    1: '0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)',
    2: '0px 3px 1px -2px rgba(0,0,0,0.2), 0px 2px 2px 0px rgba(0,0,0,0.14), 0px 1px 5px 0px rgba(0,0,0,0.12)',
    3: '0px 3px 3px -2px rgba(0,0,0,0.2), 0px 3px 4px 0px rgba(0,0,0,0.14), 0px 1px 8px 0px rgba(0,0,0,0.12)',
    4: '0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)',
    6: '0px 3px 5px -1px rgba(0,0,0,0.2), 0px 6px 10px 0px rgba(0,0,0,0.14), 0px 1px 18px 0px rgba(0,0,0,0.12)',
    8: '0px 5px 5px -3px rgba(0,0,0,0.2), 0px 8px 10px 1px rgba(0,0,0,0.14), 0px 3px 14px 2px rgba(0,0,0,0.12)',
    12: '0px 7px 8px -4px rgba(0,0,0,0.2), 0px 12px 17px 2px rgba(0,0,0,0.14), 0px 5px 22px 4px rgba(0,0,0,0.12)',
    16: '0px 8px 10px -5px rgba(0,0,0,0.2), 0px 16px 24px 2px rgba(0,0,0,0.14), 0px 6px 30px 5px rgba(0,0,0,0.12)',
    24: '0px 11px 15px -7px rgba(0,0,0,0.2), 0px 24px 38px 3px rgba(0,0,0,0.14), 0px 9px 46px 8px rgba(0,0,0,0.12)',
  },

  // Semantic shadows for different use cases
  semantic: {
    // Card shadows
    card: {
      resting: '0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)',
      hover: '0px 3px 3px -2px rgba(0,0,0,0.2), 0px 3px 4px 0px rgba(0,0,0,0.14), 0px 1px 8px 0px rgba(0,0,0,0.12)',
      active: '0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)',
    },

    // Button shadows
    button: {
      resting: '0px 3px 1px -2px rgba(0,0,0,0.2), 0px 2px 2px 0px rgba(0,0,0,0.14), 0px 1px 5px 0px rgba(0,0,0,0.12)',
      hover: '0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)',
      active: '0px 5px 5px -3px rgba(0,0,0,0.2), 0px 8px 10px 1px rgba(0,0,0,0.14), 0px 3px 14px 2px rgba(0,0,0,0.12)',
    },

    // Modal/Dialog shadows
    modal: {
      backdrop: '0px 11px 15px -7px rgba(0,0,0,0.2), 0px 24px 38px 3px rgba(0,0,0,0.14), 0px 9px 46px 8px rgba(0,0,0,0.12)',
      content: '0px 7px 8px -4px rgba(0,0,0,0.2), 0px 12px 17px 2px rgba(0,0,0,0.14), 0px 5px 22px 4px rgba(0,0,0,0.12)',
    },

    // Dropdown/Menu shadows
    dropdown: {
      menu: '0px 5px 5px -3px rgba(0,0,0,0.2), 0px 8px 10px 1px rgba(0,0,0,0.14), 0px 3px 14px 2px rgba(0,0,0,0.12)',
      tooltip: '0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)',
    },

    // Navigation shadows
    navigation: {
      header: '0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)',
      sidebar: '0px 3px 5px -1px rgba(0,0,0,0.2), 0px 6px 10px 0px rgba(0,0,0,0.14), 0px 1px 18px 0px rgba(0,0,0,0.12)',
    },

    // Financial component shadows
    financial: {
      kpiCard: '0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)',
      chartContainer: '0px 3px 3px -2px rgba(0,0,0,0.2), 0px 3px 4px 0px rgba(0,0,0,0.14), 0px 1px 8px 0px rgba(0,0,0,0.12)',
      alertCard: '0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)',
    },
  },

  // Colored shadows for specific states
  colored: {
    // Success shadows (green tint)
    success: {
      light: '0px 2px 4px -1px rgba(76, 175, 80, 0.2), 0px 4px 5px 0px rgba(76, 175, 80, 0.14), 0px 1px 10px 0px rgba(76, 175, 80, 0.12)',
      medium: '0px 3px 5px -1px rgba(76, 175, 80, 0.2), 0px 6px 10px 0px rgba(76, 175, 80, 0.14), 0px 1px 18px 0px rgba(76, 175, 80, 0.12)',
    },

    // Error shadows (red tint)
    error: {
      light: '0px 2px 4px -1px rgba(244, 67, 54, 0.2), 0px 4px 5px 0px rgba(244, 67, 54, 0.14), 0px 1px 10px 0px rgba(244, 67, 54, 0.12)',
      medium: '0px 3px 5px -1px rgba(244, 67, 54, 0.2), 0px 6px 10px 0px rgba(244, 67, 54, 0.14), 0px 1px 18px 0px rgba(244, 67, 54, 0.12)',
    },

    // Warning shadows (orange tint)
    warning: {
      light: '0px 2px 4px -1px rgba(255, 152, 0, 0.2), 0px 4px 5px 0px rgba(255, 152, 0, 0.14), 0px 1px 10px 0px rgba(255, 152, 0, 0.12)',
      medium: '0px 3px 5px -1px rgba(255, 152, 0, 0.2), 0px 6px 10px 0px rgba(255, 152, 0, 0.14), 0px 1px 18px 0px rgba(255, 152, 0, 0.12)',
    },

    // Info shadows (blue tint)
    info: {
      light: '0px 2px 4px -1px rgba(33, 150, 243, 0.2), 0px 4px 5px 0px rgba(33, 150, 243, 0.14), 0px 1px 10px 0px rgba(33, 150, 243, 0.12)',
      medium: '0px 3px 5px -1px rgba(33, 150, 243, 0.2), 0px 6px 10px 0px rgba(33, 150, 243, 0.14), 0px 1px 18px 0px rgba(33, 150, 243, 0.12)',
    },

    // Primary shadows (brand blue tint)
    primary: {
      light: '0px 2px 4px -1px rgba(33, 150, 243, 0.2), 0px 4px 5px 0px rgba(33, 150, 243, 0.14), 0px 1px 10px 0px rgba(33, 150, 243, 0.12)',
      medium: '0px 3px 5px -1px rgba(33, 150, 243, 0.2), 0px 6px 10px 0px rgba(33, 150, 243, 0.14), 0px 1px 18px 0px rgba(33, 150, 243, 0.12)',
    },
  },

  // Dark theme shadows
  dark: {
    elevation: {
      0: 'none',
      1: '0px 2px 1px -1px rgba(0,0,0,0.4), 0px 1px 1px 0px rgba(0,0,0,0.28), 0px 1px 3px 0px rgba(0,0,0,0.24)',
      2: '0px 3px 1px -2px rgba(0,0,0,0.4), 0px 2px 2px 0px rgba(0,0,0,0.28), 0px 1px 5px 0px rgba(0,0,0,0.24)',
      3: '0px 3px 3px -2px rgba(0,0,0,0.4), 0px 3px 4px 0px rgba(0,0,0,0.28), 0px 1px 8px 0px rgba(0,0,0,0.24)',
      4: '0px 2px 4px -1px rgba(0,0,0,0.4), 0px 4px 5px 0px rgba(0,0,0,0.28), 0px 1px 10px 0px rgba(0,0,0,0.24)',
      6: '0px 3px 5px -1px rgba(0,0,0,0.4), 0px 6px 10px 0px rgba(0,0,0,0.28), 0px 1px 18px 0px rgba(0,0,0,0.24)',
      8: '0px 5px 5px -3px rgba(0,0,0,0.4), 0px 8px 10px 1px rgba(0,0,0,0.28), 0px 3px 14px 2px rgba(0,0,0,0.24)',
      12: '0px 7px 8px -4px rgba(0,0,0,0.4), 0px 12px 17px 2px rgba(0,0,0,0.28), 0px 5px 22px 4px rgba(0,0,0,0.24)',
      16: '0px 8px 10px -5px rgba(0,0,0,0.4), 0px 16px 24px 2px rgba(0,0,0,0.28), 0px 6px 30px 5px rgba(0,0,0,0.24)',
      24: '0px 11px 15px -7px rgba(0,0,0,0.4), 0px 24px 38px 3px rgba(0,0,0,0.28), 0px 9px 46px 8px rgba(0,0,0,0.24)',
    },
  },

  // Inner shadows for inset effects
  inset: {
    light: 'inset 0px 1px 2px rgba(0, 0, 0, 0.1)',
    medium: 'inset 0px 2px 4px rgba(0, 0, 0, 0.15)',
    heavy: 'inset 0px 4px 8px rgba(0, 0, 0, 0.2)',
  },

  // Focus shadows for accessibility
  focus: {
    default: '0 0 0 2px rgba(33, 150, 243, 0.2)',
    error: '0 0 0 2px rgba(244, 67, 54, 0.2)',
    success: '0 0 0 2px rgba(76, 175, 80, 0.2)',
    warning: '0 0 0 2px rgba(255, 152, 0, 0.2)',
  },
} as const;

export type ShadowToken = typeof shadows;
export type ElevationLevel = keyof typeof shadows.elevation;