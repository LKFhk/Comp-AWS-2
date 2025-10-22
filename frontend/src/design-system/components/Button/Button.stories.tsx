/**
 * RiskIntel360 Design System - Button Stories
 * Storybook stories for Button component
 */

import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { Button } from './Button';
import { ThemeProvider } from '../../theme/ThemeProvider';
import {
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

const meta: Meta<typeof Button> = {
  title: 'Design System/Components/Button',
  component: Button,
  decorators: [
    (Story) => (
      <ThemeProvider>
        <Story />
      </ThemeProvider>
    ),
  ],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Enhanced button component with fintech-specific variants and loading states.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['contained', 'outlined', 'text', 'financial', 'risk', 'success', 'warning', 'error'],
      description: 'Button variant',
    },
    size: {
      control: 'select',
      options: ['small', 'medium', 'large'],
      description: 'Button size',
    },
    loading: {
      control: 'boolean',
      description: 'Show loading state',
    },
    disabled: {
      control: 'boolean',
      description: 'Disable button',
    },
    fullWidth: {
      control: 'boolean',
      description: 'Full width button',
    },
    riskLevel: {
      control: 'select',
      options: ['low', 'medium', 'high', 'critical'],
      description: 'Risk level for risk variant',
    },
    financialAction: {
      control: 'select',
      options: ['buy', 'sell', 'hold', 'alert'],
      description: 'Financial action for financial variant',
    },
    iconPosition: {
      control: 'select',
      options: ['start', 'end'],
      description: 'Icon position',
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

// Basic variants
export const Default: Story = {
  args: {
    children: 'Default Button',
    onClick: action('clicked'),
  },
};

export const Contained: Story = {
  args: {
    variant: 'contained',
    children: 'Contained Button',
    onClick: action('clicked'),
  },
};

export const Outlined: Story = {
  args: {
    variant: 'outlined',
    children: 'Outlined Button',
    onClick: action('clicked'),
  },
};

export const Text: Story = {
  args: {
    variant: 'text',
    children: 'Text Button',
    onClick: action('clicked'),
  },
};

// Sizes
export const Sizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
      <Button size="small" onClick={action('small clicked')}>
        Small
      </Button>
      <Button size="medium" onClick={action('medium clicked')}>
        Medium
      </Button>
      <Button size="large" onClick={action('large clicked')}>
        Large
      </Button>
    </div>
  ),
};

// Financial variants
export const FinancialActions: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      <Button variant="financial" financialAction="buy" onClick={action('buy clicked')}>
        Buy
      </Button>
      <Button variant="financial" financialAction="sell" onClick={action('sell clicked')}>
        Sell
      </Button>
      <Button variant="financial" financialAction="hold" onClick={action('hold clicked')}>
        Hold
      </Button>
      <Button variant="financial" financialAction="alert" onClick={action('alert clicked')}>
        Alert
      </Button>
    </div>
  ),
};

// Risk levels
export const RiskLevels: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      <Button variant="risk" riskLevel="low" onClick={action('low risk clicked')}>
        Low Risk
      </Button>
      <Button variant="risk" riskLevel="medium" onClick={action('medium risk clicked')}>
        Medium Risk
      </Button>
      <Button variant="risk" riskLevel="high" onClick={action('high risk clicked')}>
        High Risk
      </Button>
      <Button variant="risk" riskLevel="critical" onClick={action('critical risk clicked')}>
        Critical Risk
      </Button>
    </div>
  ),
};

// Status variants
export const StatusVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      <Button variant="success" onClick={action('success clicked')}>
        Success
      </Button>
      <Button variant="warning" onClick={action('warning clicked')}>
        Warning
      </Button>
      <Button variant="error" onClick={action('error clicked')}>
        Error
      </Button>
    </div>
  ),
};

// With icons
export const WithIcons: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <Button
          icon={<TrendingUpIcon />}
          iconPosition="start"
          onClick={action('icon start clicked')}
        >
          Trend Analysis
        </Button>
        <Button
          icon={<SecurityIcon />}
          iconPosition="end"
          onClick={action('icon end clicked')}
        >
          Security Check
        </Button>
      </div>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <Button
          variant="outlined"
          icon={<DownloadIcon />}
          iconPosition="start"
          onClick={action('download clicked')}
        >
          Download Report
        </Button>
      </div>
    </div>
  ),
};

// Loading states
export const LoadingStates: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <Button loading onClick={action('loading clicked')}>
          Loading
        </Button>
        <Button loading loadingText="Processing..." onClick={action('loading with text clicked')}>
          Process Data
        </Button>
      </div>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <Button variant="outlined" loading onClick={action('outlined loading clicked')}>
          Loading Outlined
        </Button>
        <Button size="small" loading onClick={action('small loading clicked')}>
          Small Loading
        </Button>
      </div>
    </div>
  ),
};

// Disabled states
export const DisabledStates: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      <Button disabled onClick={action('disabled clicked')}>
        Disabled
      </Button>
      <Button variant="outlined" disabled onClick={action('outlined disabled clicked')}>
        Disabled Outlined
      </Button>
      <Button variant="financial" financialAction="buy" disabled onClick={action('financial disabled clicked')}>
        Disabled Buy
      </Button>
    </div>
  ),
};

// Full width
export const FullWidth: Story = {
  render: () => (
    <div style={{ width: '300px' }}>
      <Button fullWidth onClick={action('full width clicked')}>
        Full Width Button
      </Button>
    </div>
  ),
};

// Interactive playground
export const Playground: Story = {
  args: {
    children: 'Playground Button',
    variant: 'contained',
    size: 'medium',
    loading: false,
    disabled: false,
    fullWidth: false,
    onClick: action('playground clicked'),
  },
};