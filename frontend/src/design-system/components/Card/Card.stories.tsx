/**
 * RiskIntel360 Design System - Card Stories
 * Storybook stories for Card component
 */

import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { Card } from './Card';
import { Button } from '../Button/Button';
import { ThemeProvider } from '../../theme/ThemeProvider';
import { Typography, Box } from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

const meta: Meta<typeof Card> = {
  title: 'Design System/Components/Card',
  component: Card,
  decorators: [
    (Story) => (
      <ThemeProvider>
        <div style={{ padding: '2rem', maxWidth: '400px' }}>
          <Story />
        </div>
      </ThemeProvider>
    ),
  ],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Enhanced card component with fintech-specific variants and KPI display.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'outlined', 'elevated', 'financial', 'kpi', 'alert', 'dashboard'],
      description: 'Card variant',
    },
    loading: {
      control: 'boolean',
      description: 'Show loading state',
    },
    status: {
      control: 'select',
      options: ['success', 'warning', 'error', 'info', 'neutral'],
      description: 'Status indicator',
    },
    riskLevel: {
      control: 'select',
      options: ['low', 'medium', 'high', 'critical'],
      description: 'Risk level indicator',
    },
    trend: {
      control: 'select',
      options: ['up', 'down', 'neutral'],
      description: 'Trend indicator',
    },
    compact: {
      control: 'boolean',
      description: 'Compact layout',
    },
    interactive: {
      control: 'boolean',
      description: 'Interactive hover effects',
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Card>;

// Basic variants
export const Default: Story = {
  args: {
    title: 'Default Card',
    children: (
      <Typography variant="body2" color="textSecondary">
        This is a default card with some content. It provides a clean container for information.
      </Typography>
    ),
  },
};

export const Outlined: Story = {
  args: {
    variant: 'outlined',
    title: 'Outlined Card',
    children: (
      <Typography variant="body2" color="textSecondary">
        This is an outlined card variant with a border instead of shadow.
      </Typography>
    ),
  },
};

export const Elevated: Story = {
  args: {
    variant: 'elevated',
    title: 'Elevated Card',
    children: (
      <Typography variant="body2" color="textSecondary">
        This is an elevated card with a more prominent shadow.
      </Typography>
    ),
  },
};

// KPI Cards
export const KPICard: Story = {
  args: {
    variant: 'kpi',
    title: 'Total Revenue',
    value: '$2,847,392',
    change: '+$247,392',
    changePercent: '+9.5',
    trend: 'up',
    status: 'success',
    children: (
      <Typography variant="caption" color="textSecondary">
        Compared to last month
      </Typography>
    ),
  },
};

export const KPICardDown: Story = {
  args: {
    variant: 'kpi',
    title: 'Risk Exposure',
    value: '$1,234,567',
    change: '-$89,432',
    changePercent: '-6.8',
    trend: 'down',
    status: 'warning',
    children: (
      <Typography variant="caption" color="textSecondary">
        Requires attention
      </Typography>
    ),
  },
};

// Financial Cards
export const FinancialCard: Story = {
  args: {
    variant: 'financial',
    title: 'Portfolio Performance',
    value: '$5,847,392',
    change: '+$347,392',
    changePercent: '+6.3',
    trend: 'up',
    riskLevel: 'low',
    interactive: true,
    children: (
      <Box>
        <Typography variant="body2" color="textSecondary" gutterBottom>
          Your portfolio is performing well with low risk exposure.
        </Typography>
        <Typography variant="caption" color="textSecondary">
          Last updated: 2 minutes ago
        </Typography>
      </Box>
    ),
  },
};

// Alert Cards
export const AlertCard: Story = {
  args: {
    variant: 'alert',
    title: 'Security Alert',
    status: 'error',
    showMenu: true,
    onMenuClick: action('menu clicked'),
    children: (
      <Box>
        <Typography variant="body2" gutterBottom>
          Suspicious activity detected on account ending in 4567.
        </Typography>
        <Typography variant="caption" color="textSecondary">
          Detected 5 minutes ago
        </Typography>
      </Box>
    ),
    footer: (
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button size="small" variant="contained" onClick={action('investigate clicked')}>
          Investigate
        </Button>
        <Button size="small" variant="outlined" onClick={action('dismiss clicked')}>
          Dismiss
        </Button>
      </Box>
    ),
  },
};

// Dashboard Cards
export const DashboardCard: Story = {
  args: {
    variant: 'dashboard',
    title: 'Market Overview',
    subtitle: 'Real-time market data',
    interactive: true,
    action: (
      <Button size="small" variant="outlined" onClick={action('view all clicked')}>
        View All
      </Button>
    ),
    children: (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Box>
            <Typography variant="h6">S&P 500</Typography>
            <Typography variant="body2" color="success.main">
              +2.4% <TrendingUpIcon fontSize="small" />
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6">NASDAQ</Typography>
            <Typography variant="body2" color="error.main">
              -1.2% <TrendingDownIcon fontSize="small" />
            </Typography>
          </Box>
        </Box>
        <Typography variant="caption" color="textSecondary">
          Market closes in 2h 34m
        </Typography>
      </Box>
    ),
  },
};

// Risk Level Cards
export const RiskLevels: Story = {
  render: () => (
    <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(2, 1fr)' }}>
      <Card variant="kpi" title="Low Risk" riskLevel="low" value="15%" compact>
        <Typography variant="caption" color="textSecondary">
          Safe investments
        </Typography>
      </Card>
      <Card variant="kpi" title="Medium Risk" riskLevel="medium" value="35%" compact>
        <Typography variant="caption" color="textSecondary">
          Balanced portfolio
        </Typography>
      </Card>
      <Card variant="kpi" title="High Risk" riskLevel="high" value="25%" compact>
        <Typography variant="caption" color="textSecondary">
          Growth investments
        </Typography>
      </Card>
      <Card variant="kpi" title="Critical Risk" riskLevel="critical" value="5%" compact>
        <Typography variant="caption" color="textSecondary">
          Immediate attention
        </Typography>
      </Card>
    </div>
  ),
};

// Status Cards
export const StatusCards: Story = {
  render: () => (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <Card variant="alert" title="System Healthy" status="success" compact>
        <Typography variant="body2">All systems operational</Typography>
      </Card>
      <Card variant="alert" title="Maintenance Scheduled" status="info" compact>
        <Typography variant="body2">Scheduled maintenance at 2:00 AM</Typography>
      </Card>
      <Card variant="alert" title="High CPU Usage" status="warning" compact>
        <Typography variant="body2">CPU usage above 80%</Typography>
      </Card>
      <Card variant="alert" title="Service Down" status="error" compact>
        <Typography variant="body2">Payment service unavailable</Typography>
      </Card>
    </div>
  ),
};

// Loading States
export const LoadingStates: Story = {
  render: () => (
    <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(2, 1fr)' }}>
      <Card loading title="Loading Card" />
      <Card variant="kpi" loading />
      <Card variant="dashboard" loading />
      <Card variant="financial" loading />
    </div>
  ),
};

// Interactive Cards
export const InteractiveCards: Story = {
  render: () => (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <Card
        variant="dashboard"
        title="Click me!"
        interactive
        onClick={action('card clicked')}
        children={
          <Typography variant="body2" color="textSecondary">
            This card has hover effects and is clickable.
          </Typography>
        }
      />
      <Card
        variant="financial"
        title="Hover for effect"
        value="$1,234,567"
        trend="up"
        interactive
        children={
          <Typography variant="body2" color="textSecondary">
            Hover to see the lift effect.
          </Typography>
        }
      />
    </div>
  ),
};

// Compact Layout
export const CompactLayout: Story = {
  render: () => (
    <div style={{ display: 'grid', gap: '0.5rem', gridTemplateColumns: 'repeat(3, 1fr)' }}>
      <Card variant="kpi" title="Revenue" value="$2.4M" compact />
      <Card variant="kpi" title="Users" value="12.5K" compact />
      <Card variant="kpi" title="Growth" value="+15%" trend="up" compact />
    </div>
  ),
};

// Playground
export const Playground: Story = {
  args: {
    variant: 'default',
    title: 'Playground Card',
    subtitle: 'Experiment with different props',
    loading: false,
    compact: false,
    interactive: false,
    showMenu: false,
    onMenuClick: action('menu clicked'),
    children: (
      <Typography variant="body2" color="textSecondary">
        Use the controls to experiment with different card configurations.
      </Typography>
    ),
  },
};