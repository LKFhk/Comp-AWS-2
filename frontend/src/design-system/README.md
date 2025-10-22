# RiskIntel360 Design System

A comprehensive, modern design system built specifically for fintech applications with WCAG 2.1 AA accessibility compliance.

## 🎯 Overview

The RiskIntel360 Design System provides a unified set of design tokens, components, and utilities to create consistent, accessible, and professional financial interfaces. Built with TypeScript and Material-UI, it offers both light and dark themes with fintech-specific color palettes and components.

## ✨ Features

- **🎨 Comprehensive Design Tokens**: Colors, typography, spacing, shadows, and breakpoints
- **🌓 Light/Dark Theme Support**: Automatic system preference detection with manual override
- **📱 Responsive Grid System**: Flexible layouts for all screen sizes
- **♿ Accessibility First**: WCAG 2.1 AA compliant with comprehensive utilities
- **💰 Financial Components**: Specialized components for fintech applications
- **🎭 Animation System**: Smooth, performant animations with reduced motion support
- **📚 Storybook Integration**: Complete component documentation and testing
- **🔧 TypeScript Support**: Full type safety and IntelliSense

## 🚀 Quick Start

### Installation

```bash
# The design system is included in the RiskIntel360 frontend
cd frontend
npm install
```

### Basic Usage

```tsx
import React from 'react';
import { ThemeProvider, Button, Card } from '../design-system';

function App() {
  return (
    <ThemeProvider>
      <Card title="Welcome to RiskIntel360">
        <Button variant="financial" financialAction="buy">
          Buy Stock
        </Button>
      </Card>
    </ThemeProvider>
  );
}
```

## 📖 Documentation

### Design Tokens

#### Colors

The color system includes semantic colors for financial applications:

```tsx
import { colors } from '../design-system';

// Primary brand colors
colors.primary[500] // Main brand blue
colors.secondary[500] // Success green

// Financial-specific colors
colors.financial.bullish // Green for positive trends
colors.financial.bearish // Red for negative trends
colors.financial.riskHigh // High risk indicator
```

#### Typography

Professional typography system with financial data support:

```tsx
import { typography } from '../design-system';

// Font families
typography.fontFamily.primary // Inter for UI
typography.fontFamily.financial // IBM Plex Mono for numbers

// Typography scales
typography.scale.heading.h1 // Large headings
typography.scale.financial.medium // Financial data display
```

#### Spacing

Consistent spacing system based on 4px grid:

```tsx
import { spacing } from '../design-system';

// Base spacing scale
spacing.scale[4] // 16px (1rem)
spacing.scale[8] // 32px (2rem)

// Component-specific spacing
spacing.component.card.padding.medium // Card padding
spacing.component.financial.kpiGap // KPI card spacing
```

### Theme System

#### Theme Provider

Wrap your application with the ThemeProvider:

```tsx
import { ThemeProvider } from '../design-system';

function App() {
  return (
    <ThemeProvider defaultMode="system">
      {/* Your app content */}
    </ThemeProvider>
  );
}
```

#### Theme Hooks

```tsx
import { useTheme, useThemeMode, useFinancialTheme } from '../design-system';

function MyComponent() {
  const { theme } = useTheme();
  const { mode, toggleTheme } = useThemeMode();
  const financialTheme = useFinancialTheme();
  
  return (
    <div style={{ color: financialTheme.colors.risk.high }}>
      Current theme: {mode}
    </div>
  );
}
```

### Components

#### Button

Enhanced button with financial variants:

```tsx
import { Button } from '../design-system';

// Financial actions
<Button variant="financial" financialAction="buy">Buy</Button>
<Button variant="financial" financialAction="sell">Sell</Button>

// Risk levels
<Button variant="risk" riskLevel="high">High Risk</Button>

// With loading state
<Button loading loadingText="Processing...">Submit</Button>
```

#### Card

Flexible card component with KPI support:

```tsx
import { Card } from '../design-system';

// KPI Card
<Card
  variant="kpi"
  title="Total Revenue"
  value="$2,847,392"
  change="+$247,392"
  changePercent="+9.5"
  trend="up"
  status="success"
/>

// Financial Card
<Card
  variant="financial"
  title="Portfolio Performance"
  riskLevel="low"
  interactive
>
  Content here
</Card>
```

#### Grid System

Responsive grid layouts:

```tsx
import { GridContainer, GridItem, FlexGrid } from '../design-system';

// CSS Grid
<GridContainer columns={{ xs: 1, sm: 2, md: 3 }} spacing={3}>
  <GridItem xs={12} md={6}>Content</GridItem>
  <GridItem xs={12} md={6}>Content</GridItem>
</GridContainer>

// Flexible Grid
<FlexGrid columns={{ xs: 1, sm: 2, lg: 4 }} spacing={2}>
  <div>Item 1</div>
  <div>Item 2</div>
</FlexGrid>
```

#### Navigation

Modern navigation components:

```tsx
import { Header, Sidebar, defaultNavigationItems } from '../design-system';

<Header
  title="RiskIntel360"
  user={{ name: "John Doe", email: "john@example.com" }}
  notifications={5}
  onNotificationClick={() => {}}
  onUserMenuClick={(action) => console.log(action)}
/>

<Sidebar
  open={sidebarOpen}
  onClose={() => setSidebarOpen(false)}
  items={defaultNavigationItems}
  onItemClick={(item) => navigate(item.path)}
  activeItem="dashboard"
/>
```

### Utilities

#### Accessibility

WCAG 2.1 AA compliance utilities:

```tsx
import { a11y } from '../design-system';

// Color contrast checking
const ratio = a11y.getContrastRatio('#ffffff', '#000000');
const meetsAA = a11y.meetsContrastRequirement('#ffffff', '#000000');

// Screen reader announcements
a11y.announceToScreenReader('Data updated', 'polite');

// Financial data formatting
const currency = a11y.formatCurrencyForScreenReader(1234.56);
const percentage = a11y.formatPercentageForScreenReader(15.5);
```

#### Animations

Smooth animations with reduced motion support:

```tsx
import { animations } from '../design-system';

// CSS-in-JS animations
const MyComponent = styled.div`
  ${animations.hoverLift}
  ${animations.pageTransitions.fadeIn}
`;

// Financial animations
const TrendIndicator = styled.div`
  ${animations.trendIndicator('up')}
`;
```

## 🎨 Storybook

View all components and their variants in Storybook:

```bash
npm run storybook
```

This will open Storybook at `http://localhost:6006` with:
- Component documentation
- Interactive controls
- Accessibility testing
- Visual regression testing

## 🧪 Testing

### Accessibility Testing

```bash
# Run accessibility tests
npm run test:a11y

# Test with axe-core
npm run test -- --testPathPattern=accessibility
```

### Visual Testing

```bash
# Run visual regression tests
npm run test:visual

# Update visual baselines
npm run chromatic
```

### Component Testing

```bash
# Run component tests
npm run test:unit

# Test specific component
npm run test Button.test.tsx
```

## 📱 Responsive Design

The design system uses a mobile-first approach with these breakpoints:

- **xs**: 0px (mobile)
- **sm**: 600px (large mobile/small tablet)
- **md**: 900px (tablet)
- **lg**: 1200px (desktop)
- **xl**: 1536px (large desktop)

### Usage

```tsx
import { breakpoints } from '../design-system';

// In styled components
const ResponsiveBox = styled.div`
  padding: 1rem;
  
  ${breakpoints.up.md} {
    padding: 2rem;
  }
`;

// In component props
<GridContainer columns={{ xs: 1, sm: 2, lg: 4 }}>
```

## 🎯 Financial Components

### KPI Cards

Display key performance indicators:

```tsx
<Card
  variant="kpi"
  title="Monthly Revenue"
  value="$2,847,392"
  change="+$247,392"
  changePercent="+9.5"
  trend="up"
  status="success"
/>
```

### Risk Indicators

Show risk levels with appropriate colors:

```tsx
<Button variant="risk" riskLevel="high">
  High Risk Portfolio
</Button>

<Card variant="financial" riskLevel="critical">
  Critical risk exposure detected
</Card>
```

### Market Trends

Display market direction:

```tsx
<Card
  variant="financial"
  trend="up"
  value="$1,234.56"
  change="+2.4%"
>
  Stock is trending upward
</Card>
```

## 🔧 Customization

### Extending the Theme

```tsx
import { createTheme } from '@mui/material/styles';
import { lightTheme } from '../design-system';

const customTheme = createTheme({
  ...lightTheme,
  palette: {
    ...lightTheme.palette,
    primary: {
      main: '#your-brand-color',
    },
  },
});
```

### Custom Components

```tsx
import { styled } from '@mui/material/styles';
import { Card } from '../design-system';

const CustomCard = styled(Card)(({ theme }) => ({
  borderRadius: theme.spacing(2),
  '&:hover': {
    transform: 'translateY(-4px)',
  },
}));
```

## 📋 Best Practices

### Accessibility

1. **Always use semantic HTML**: Use proper heading hierarchy, form labels, etc.
2. **Test with screen readers**: Use the provided accessibility utilities
3. **Ensure color contrast**: Use `meetsContrastRequirement()` utility
4. **Support keyboard navigation**: All interactive elements should be keyboard accessible

### Performance

1. **Use lazy loading**: Import components only when needed
2. **Optimize animations**: Respect `prefers-reduced-motion`
3. **Bundle splitting**: Import only the components you use

### Consistency

1. **Use design tokens**: Always use spacing, colors, and typography from tokens
2. **Follow naming conventions**: Use consistent naming for props and variants
3. **Document custom components**: Add Storybook stories for custom components

## 🤝 Contributing

### Adding New Components

1. Create component in `src/design-system/components/`
2. Add TypeScript interfaces
3. Include accessibility features
4. Write Storybook stories
5. Add unit tests
6. Update documentation

### Design Token Updates

1. Update token files in `src/design-system/tokens/`
2. Update theme configuration
3. Test across all components
4. Update Storybook stories

## 📚 Resources

- [Material-UI Documentation](https://mui.com/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Storybook Documentation](https://storybook.js.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## 🐛 Troubleshooting

### Common Issues

**Theme not applying**: Ensure your app is wrapped with `ThemeProvider`

**TypeScript errors**: Make sure you're importing types correctly:
```tsx
import type { ButtonProps } from '../design-system';
```

**Accessibility warnings**: Use the provided a11y utilities and test with screen readers

**Animation performance**: Check if `prefers-reduced-motion` is respected

### Getting Help

1. Check Storybook documentation
2. Review component source code
3. Check accessibility utilities
4. Test in different browsers and screen sizes

---

Built with ❤️ for the RiskIntel360 platform