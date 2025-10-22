/**
 * RiskIntel360 Design System - Spacing Tokens
 * Consistent spacing system for layouts and components
 */

export const spacing = {
  // Base spacing unit (4px)
  base: 4,

  // Spacing scale (multiples of base unit)
  scale: {
    0: '0px',
    1: '0.25rem',  // 4px
    2: '0.5rem',   // 8px
    3: '0.75rem',  // 12px
    4: '1rem',     // 16px
    5: '1.25rem',  // 20px
    6: '1.5rem',   // 24px
    7: '1.75rem',  // 28px
    8: '2rem',     // 32px
    9: '2.25rem',  // 36px
    10: '2.5rem',  // 40px
    11: '2.75rem', // 44px
    12: '3rem',    // 48px
    14: '3.5rem',  // 56px
    16: '4rem',    // 64px
    20: '5rem',    // 80px
    24: '6rem',    // 96px
    28: '7rem',    // 112px
    32: '8rem',    // 128px
    36: '9rem',    // 144px
    40: '10rem',   // 160px
    44: '11rem',   // 176px
    48: '12rem',   // 192px
    52: '13rem',   // 208px
    56: '14rem',   // 224px
    60: '15rem',   // 240px
    64: '16rem',   // 256px
    72: '18rem',   // 288px
    80: '20rem',   // 320px
    96: '24rem',   // 384px
  },

  // Component-specific spacing
  component: {
    // Button spacing
    button: {
      paddingX: {
        small: '0.75rem',   // 12px
        medium: '1rem',     // 16px
        large: '1.5rem',    // 24px
      },
      paddingY: {
        small: '0.375rem',  // 6px
        medium: '0.5rem',   // 8px
        large: '0.75rem',   // 12px
      },
      gap: '0.5rem', // 8px between icon and text
    },

    // Card spacing
    card: {
      padding: {
        small: '1rem',      // 16px
        medium: '1.5rem',   // 24px
        large: '2rem',      // 32px
      },
      gap: '1rem', // 16px between card elements
    },

    // Form spacing
    form: {
      fieldGap: '1rem',     // 16px between form fields
      sectionGap: '2rem',   // 32px between form sections
      labelGap: '0.5rem',   // 8px between label and input
      helperGap: '0.25rem', // 4px between input and helper text
    },

    // List spacing
    list: {
      itemGap: '0.5rem',    // 8px between list items
      itemPadding: '0.75rem', // 12px padding inside list items
      nestedIndent: '1.5rem', // 24px for nested items
    },

    // Navigation spacing
    navigation: {
      itemGap: '0.25rem',   // 4px between nav items
      itemPadding: '0.75rem', // 12px padding inside nav items
      sectionGap: '1.5rem', // 24px between nav sections
    },

    // Table spacing
    table: {
      cellPadding: '0.75rem', // 12px cell padding
      rowGap: '0.25rem',      // 4px between rows
      headerPadding: '1rem',  // 16px header padding
    },

    // Modal/Dialog spacing
    modal: {
      padding: '2rem',        // 32px modal padding
      headerGap: '1rem',      // 16px between header elements
      contentGap: '1.5rem',   // 24px between content sections
      actionGap: '0.75rem',   // 12px between action buttons
    },

    // Dashboard spacing
    dashboard: {
      widgetGap: '1.5rem',    // 24px between dashboard widgets
      widgetPadding: '1.5rem', // 24px inside widgets
      sectionGap: '2rem',     // 32px between dashboard sections
      headerGap: '1rem',      // 16px between header elements
    },

    // Financial data spacing
    financial: {
      metricGap: '1rem',      // 16px between financial metrics
      chartPadding: '1rem',   // 16px around charts
      tableRowHeight: '3rem', // 48px for financial data rows
      kpiGap: '1.5rem',       // 24px between KPI cards
    },
  },

  // Layout spacing
  layout: {
    // Container spacing
    container: {
      paddingX: {
        mobile: '1rem',     // 16px
        tablet: '1.5rem',   // 24px
        desktop: '2rem',    // 32px
      },
      maxWidth: {
        small: '640px',
        medium: '768px',
        large: '1024px',
        xlarge: '1280px',
        xxlarge: '1536px',
      },
    },

    // Grid spacing
    grid: {
      gap: {
        small: '1rem',      // 16px
        medium: '1.5rem',   // 24px
        large: '2rem',      // 32px
      },
      columnGap: {
        small: '1rem',      // 16px
        medium: '1.5rem',   // 24px
        large: '2rem',      // 32px
      },
      rowGap: {
        small: '1rem',      // 16px
        medium: '1.5rem',   // 24px
        large: '2rem',      // 32px
      },
    },

    // Section spacing
    section: {
      paddingY: {
        small: '2rem',      // 32px
        medium: '3rem',     // 48px
        large: '4rem',      // 64px
        xlarge: '6rem',     // 96px
      },
      gap: {
        small: '1.5rem',    // 24px
        medium: '2rem',     // 32px
        large: '3rem',      // 48px
      },
    },

    // Header/Footer spacing
    header: {
      height: '4rem',       // 64px
      padding: '1rem',      // 16px
    },
    footer: {
      paddingY: '2rem',     // 32px
      paddingX: '1rem',     // 16px
    },

    // Sidebar spacing
    sidebar: {
      width: {
        collapsed: '4rem',  // 64px
        expanded: '16rem',  // 256px
      },
      padding: '1rem',      // 16px
      itemGap: '0.5rem',    // 8px
    },
  },

  // Responsive spacing adjustments
  responsive: {
    mobile: {
      container: { paddingX: '1rem' },
      section: { paddingY: '1.5rem' },
      card: { padding: '1rem' },
      modal: { padding: '1rem' },
    },
    tablet: {
      container: { paddingX: '1.5rem' },
      section: { paddingY: '2rem' },
      card: { padding: '1.25rem' },
      modal: { padding: '1.5rem' },
    },
    desktop: {
      container: { paddingX: '2rem' },
      section: { paddingY: '3rem' },
      card: { padding: '1.5rem' },
      modal: { padding: '2rem' },
    },
  },
} as const;

export type SpacingToken = typeof spacing;
export type SpacingScale = keyof typeof spacing.scale;