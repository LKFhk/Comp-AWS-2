/**
 * RiskIntel360 Design System - Breakpoint Tokens
 * Responsive design breakpoints for consistent layouts
 */

export const breakpoints = {
  // Breakpoint values (in pixels)
  values: {
    xs: 0,      // Extra small devices (phones)
    sm: 600,    // Small devices (large phones, small tablets)
    md: 900,    // Medium devices (tablets)
    lg: 1200,   // Large devices (desktops)
    xl: 1536,   // Extra large devices (large desktops)
  },

  // Media query strings
  up: {
    xs: '@media (min-width: 0px)',
    sm: '@media (min-width: 600px)',
    md: '@media (min-width: 900px)',
    lg: '@media (min-width: 1200px)',
    xl: '@media (min-width: 1536px)',
  },

  down: {
    xs: '@media (max-width: 599.95px)',
    sm: '@media (max-width: 899.95px)',
    md: '@media (max-width: 1199.95px)',
    lg: '@media (max-width: 1535.95px)',
    xl: '@media (max-width: 9999px)', // No upper limit
  },

  between: {
    'xs-sm': '@media (min-width: 0px) and (max-width: 899.95px)',
    'sm-md': '@media (min-width: 600px) and (max-width: 1199.95px)',
    'md-lg': '@media (min-width: 900px) and (max-width: 1535.95px)',
    'lg-xl': '@media (min-width: 1200px)',
  },

  only: {
    xs: '@media (min-width: 0px) and (max-width: 599.95px)',
    sm: '@media (min-width: 600px) and (max-width: 899.95px)',
    md: '@media (min-width: 900px) and (max-width: 1199.95px)',
    lg: '@media (min-width: 1200px) and (max-width: 1535.95px)',
    xl: '@media (min-width: 1536px)',
  },

  // Container max-widths for each breakpoint
  container: {
    xs: '100%',
    sm: '540px',
    md: '720px',
    lg: '960px',
    xl: '1140px',
  },

  // Grid columns for each breakpoint
  columns: {
    xs: 4,   // 4 columns on mobile
    sm: 8,   // 8 columns on small tablets
    md: 12,  // 12 columns on tablets and up
    lg: 12,  // 12 columns on desktop
    xl: 12,  // 12 columns on large desktop
  },

  // Component-specific breakpoint behaviors
  components: {
    // Navigation breakpoints
    navigation: {
      mobileBreakpoint: 'md', // Switch to mobile nav below md
      collapsedSidebar: 'lg',  // Collapse sidebar below lg
    },

    // Dashboard breakpoints
    dashboard: {
      singleColumn: 'sm',     // Single column below sm
      twoColumn: 'md',        // Two columns from sm to md
      threeColumn: 'lg',      // Three columns from md to lg
      fourColumn: 'xl',       // Four columns from lg up
    },

    // Table breakpoints
    table: {
      stackColumns: 'sm',     // Stack table columns below sm
      hideColumns: 'md',      // Hide less important columns below md
      fullFeatures: 'lg',     // Show all features from lg up
    },

    // Modal breakpoints
    modal: {
      fullscreen: 'sm',       // Fullscreen modals below sm
      centered: 'md',         // Centered modals from md up
    },

    // Chart breakpoints
    chart: {
      simplified: 'sm',       // Simplified charts below sm
      interactive: 'md',      // Interactive features from md up
      fullFeatures: 'lg',     // All features from lg up
    },
  },

  // Financial dashboard specific breakpoints
  financial: {
    // KPI cards layout
    kpi: {
      singleColumn: 'xs',     // 1 KPI per row on mobile
      twoColumn: 'sm',        // 2 KPIs per row on small screens
      threeColumn: 'md',      // 3 KPIs per row on tablets
      fourColumn: 'lg',       // 4 KPIs per row on desktop
    },

    // Chart layouts
    charts: {
      stacked: 'sm',          // Stack charts vertically below sm
      sideBySide: 'md',       // Side-by-side charts from md up
      dashboard: 'lg',        // Full dashboard layout from lg up
    },

    // Data table layouts
    dataTables: {
      minimal: 'xs',          // Show only essential columns
      standard: 'sm',         // Show standard columns
      detailed: 'md',         // Show detailed columns
      comprehensive: 'lg',    // Show all columns
    },
  },
} as const;

// Utility functions for breakpoint usage
export const createMediaQuery = (breakpoint: keyof typeof breakpoints.values, direction: 'up' | 'down' = 'up') => {
  const value = breakpoints.values[breakpoint];
  if (direction === 'up') {
    return `@media (min-width: ${value}px)`;
  }
  return `@media (max-width: ${value - 0.05}px)`;
};

export const isBreakpointUp = (breakpoint: keyof typeof breakpoints.values, width: number) => {
  return width >= breakpoints.values[breakpoint];
};

export const isBreakpointDown = (breakpoint: keyof typeof breakpoints.values, width: number) => {
  return width < breakpoints.values[breakpoint];
};

export type BreakpointToken = typeof breakpoints;
export type Breakpoint = keyof typeof breakpoints.values;