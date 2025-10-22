import type { Meta, StoryObj } from '@storybook/react';
import LoadingSpinner from './LoadingSpinner';

const meta: Meta<typeof LoadingSpinner> = {
  title: 'Common/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A loading spinner component used throughout the application to indicate loading states.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: { type: 'number', min: 20, max: 100, step: 10 },
      description: 'Size of the loading spinner in pixels',
    },
    color: {
      control: { type: 'select' },
      options: ['primary', 'secondary', 'inherit'],
      description: 'Color of the loading spinner',
    },
    message: {
      control: { type: 'text' },
      description: 'Optional message to display below the spinner',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const Small: Story = {
  args: {
    size: 24,
  },
};

export const Medium: Story = {
  args: {
    size: 40,
  },
};

export const Large: Story = {
  args: {
    size: 60,
  },
};

export const WithMessage: Story = {
  args: {
    message: 'Loading validation results...',
  },
};

export const PrimaryColor: Story = {
  args: {
    color: 'primary',
    message: 'Processing your request...',
  },
};

export const SecondaryColor: Story = {
  args: {
    color: 'secondary',
    message: 'Analyzing market data...',
  },
};

export const LargeWithMessage: Story = {
  args: {
    size: 60,
    color: 'primary',
    message: 'Running comprehensive business validation...',
  },
};