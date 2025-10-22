import type { Meta, StoryObj } from '@storybook/react';
import MarketAnalysisChart from './MarketAnalysisChart';

const meta: Meta<typeof MarketAnalysisChart> = {
  title: 'Charts/MarketAnalysisChart',
  component: MarketAnalysisChart,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'A comprehensive chart component for displaying market analysis data including market size, trends, and segments.',
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

const mockMarketData = {
  market_size: {
    current: 1000000000,
    projected_3_year: 1500000000,
    growth_rate: 15.0,
  },
  trends: [
    {
      name: 'Digital Transformation',
      impact: 'high',
      timeline: '2024-2026',
      description: 'Increasing adoption of digital solutions',
    },
    {
      name: 'Remote Work',
      impact: 'medium',
      timeline: '2024-2025',
      description: 'Continued remote work trends',
    },
  ],
  segments: [
    { name: 'Enterprise', size: 600000000, growth: 12.0 },
    { name: 'SMB', size: 300000000, growth: 18.0 },
    { name: 'Startup', size: 100000000, growth: 25.0 },
  ],
  confidence_score: 0.85,
};

const smallMarketData = {
  market_size: {
    current: 50000000,
    projected_3_year: 75000000,
    growth_rate: 8.5,
  },
  trends: [
    {
      name: 'Niche Market Growth',
      impact: 'medium',
      timeline: '2024-2025',
      description: 'Specialized market expansion',
    },
  ],
  segments: [
    { name: 'Specialized', size: 30000000, growth: 10.0 },
    { name: 'General', size: 20000000, growth: 6.0 },
  ],
  confidence_score: 0.72,
};

const highGrowthData = {
  market_size: {
    current: 500000000,
    projected_3_year: 2000000000,
    growth_rate: 58.7,
  },
  trends: [
    {
      name: 'AI Revolution',
      impact: 'high',
      timeline: '2024-2027',
      description: 'Rapid AI adoption across industries',
    },
    {
      name: 'Automation Trend',
      impact: 'high',
      timeline: '2024-2026',
      description: 'Increasing process automation',
    },
  ],
  segments: [
    { name: 'AI/ML', size: 200000000, growth: 75.0 },
    { name: 'Traditional', size: 300000000, growth: 45.0 },
  ],
  confidence_score: 0.91,
};

export const Default: Story = {
  args: {
    data: mockMarketData,
  },
};

export const SmallMarket: Story = {
  args: {
    data: smallMarketData,
  },
};

export const HighGrowthMarket: Story = {
  args: {
    data: highGrowthData,
  },
};

export const NoData: Story = {
  args: {
    data: null,
  },
};

export const LowConfidence: Story = {
  args: {
    data: {
      ...mockMarketData,
      confidence_score: 0.45,
    },
  },
};

export const HighConfidence: Story = {
  args: {
    data: {
      ...mockMarketData,
      confidence_score: 0.95,
    },
  },
};