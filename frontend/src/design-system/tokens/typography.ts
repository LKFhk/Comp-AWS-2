/**
 * RiskIntel360 Design System - Typography Tokens
 * Professional typography system for financial interfaces
 */

export const typography = {
  // Font Families
  fontFamily: {
    primary: '"Inter", "Roboto", "Helvetica Neue", "Arial", sans-serif',
    secondary: '"Roboto", "Helvetica", "Arial", sans-serif',
    mono: '"Fira Code", "Monaco", "Consolas", "Courier New", monospace',
    financial: '"IBM Plex Sans", "Inter", "Roboto", sans-serif', // For financial data
  },

  // Font Weights
  fontWeight: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },

  // Font Sizes (rem units for accessibility)
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
    '6xl': '3.75rem', // 60px
  },

  // Line Heights
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },

  // Letter Spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },

  // Typography Scales for Different Use Cases
  scale: {
    // Display Typography (Large headings, hero text)
    display: {
      large: {
        fontSize: '3.75rem', // 60px
        lineHeight: 1.1,
        fontWeight: 700,
        letterSpacing: '-0.025em',
      },
      medium: {
        fontSize: '3rem', // 48px
        lineHeight: 1.2,
        fontWeight: 700,
        letterSpacing: '-0.025em',
      },
      small: {
        fontSize: '2.25rem', // 36px
        lineHeight: 1.25,
        fontWeight: 600,
        letterSpacing: '-0.025em',
      },
    },

    // Heading Typography
    heading: {
      h1: {
        fontSize: '1.875rem', // 30px
        lineHeight: 1.3,
        fontWeight: 600,
        letterSpacing: '-0.025em',
      },
      h2: {
        fontSize: '1.5rem', // 24px
        lineHeight: 1.35,
        fontWeight: 600,
        letterSpacing: '-0.025em',
      },
      h3: {
        fontSize: '1.25rem', // 20px
        lineHeight: 1.4,
        fontWeight: 600,
        letterSpacing: 'normal',
      },
      h4: {
        fontSize: '1.125rem', // 18px
        lineHeight: 1.45,
        fontWeight: 600,
        letterSpacing: 'normal',
      },
      h5: {
        fontSize: '1rem', // 16px
        lineHeight: 1.5,
        fontWeight: 600,
        letterSpacing: 'normal',
      },
      h6: {
        fontSize: '0.875rem', // 14px
        lineHeight: 1.5,
        fontWeight: 600,
        letterSpacing: '0.025em',
      },
    },

    // Body Typography
    body: {
      large: {
        fontSize: '1.125rem', // 18px
        lineHeight: 1.6,
        fontWeight: 400,
        letterSpacing: 'normal',
      },
      medium: {
        fontSize: '1rem', // 16px
        lineHeight: 1.5,
        fontWeight: 400,
        letterSpacing: 'normal',
      },
      small: {
        fontSize: '0.875rem', // 14px
        lineHeight: 1.5,
        fontWeight: 400,
        letterSpacing: 'normal',
      },
    },

    // Caption and Label Typography
    caption: {
      large: {
        fontSize: '0.875rem', // 14px
        lineHeight: 1.4,
        fontWeight: 500,
        letterSpacing: '0.025em',
      },
      medium: {
        fontSize: '0.75rem', // 12px
        lineHeight: 1.4,
        fontWeight: 500,
        letterSpacing: '0.025em',
      },
      small: {
        fontSize: '0.6875rem', // 11px
        lineHeight: 1.4,
        fontWeight: 500,
        letterSpacing: '0.05em',
      },
    },

    // Financial Data Typography (Monospace for numbers)
    financial: {
      large: {
        fontSize: '1.125rem', // 18px
        lineHeight: 1.4,
        fontWeight: 600,
        letterSpacing: 'normal',
        fontFamily: '"IBM Plex Mono", "Fira Code", monospace',
      },
      medium: {
        fontSize: '1rem', // 16px
        lineHeight: 1.4,
        fontWeight: 500,
        letterSpacing: 'normal',
        fontFamily: '"IBM Plex Mono", "Fira Code", monospace',
      },
      small: {
        fontSize: '0.875rem', // 14px
        lineHeight: 1.4,
        fontWeight: 500,
        letterSpacing: 'normal',
        fontFamily: '"IBM Plex Mono", "Fira Code", monospace',
      },
    },

    // Button Typography
    button: {
      large: {
        fontSize: '1rem', // 16px
        lineHeight: 1.5,
        fontWeight: 600,
        letterSpacing: '0.025em',
        textTransform: 'none' as const,
      },
      medium: {
        fontSize: '0.875rem', // 14px
        lineHeight: 1.5,
        fontWeight: 600,
        letterSpacing: '0.025em',
        textTransform: 'none' as const,
      },
      small: {
        fontSize: '0.75rem', // 12px
        lineHeight: 1.5,
        fontWeight: 600,
        letterSpacing: '0.05em',
        textTransform: 'none' as const,
      },
    },
  },

  // Responsive Typography Breakpoints
  responsive: {
    mobile: {
      display: {
        large: { fontSize: '2.5rem' }, // Smaller on mobile
        medium: { fontSize: '2rem' },
        small: { fontSize: '1.75rem' },
      },
      heading: {
        h1: { fontSize: '1.5rem' },
        h2: { fontSize: '1.25rem' },
        h3: { fontSize: '1.125rem' },
      },
    },
    tablet: {
      display: {
        large: { fontSize: '3rem' },
        medium: { fontSize: '2.5rem' },
        small: { fontSize: '2rem' },
      },
      heading: {
        h1: { fontSize: '1.75rem' },
        h2: { fontSize: '1.375rem' },
        h3: { fontSize: '1.1875rem' },
      },
    },
  },
} as const;

export type TypographyToken = typeof typography;
export type FontSize = keyof typeof typography.fontSize;
export type FontWeight = keyof typeof typography.fontWeight;
export type LineHeight = keyof typeof typography.lineHeight;