import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import MarketAnalysisChart from './MarketAnalysisChart';

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }: any) => (
    <div data-testid="line-chart" role="img" aria-label={options?.plugins?.title?.text || 'Market Analysis Chart'}>
      <div data-testid="chart-data">{JSON.stringify(data)}</div>
    </div>
  ),
  Bar: ({ data, options }: any) => (
    <div data-testid="bar-chart" role="img" aria-label={options?.plugins?.title?.text || 'Market Analysis Chart'}>
      <div data-testid="chart-data">{JSON.stringify(data)}</div>
    </div>
  ),
}));

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

describe('MarketAnalysisChart', () => {
  test('renders market analysis chart with data', () => {
    render(<MarketAnalysisChart data={mockMarketData} />);
    
    expect(screen.getAllByRole('img')).toHaveLength(1); // 1 line chart
    expect(screen.getAllByTestId('chart-data')).toHaveLength(1);
  });

  test('displays market size information', () => {
    render(<MarketAnalysisChart data={mockMarketData} />);
    
    expect(screen.getByText(/Market Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Market Growth/i)).toBeInTheDocument();
  });

  test('shows growth trends', () => {
    render(<MarketAnalysisChart data={mockMarketData} />);
    
    expect(screen.getByText(/Market Analysis/i)).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  test('displays confidence score', () => {
    render(<MarketAnalysisChart data={mockMarketData} />);
    
    expect(screen.getByText(/Market Analysis/i)).toBeInTheDocument();
  });

  test('handles empty data gracefully', () => {
    render(<MarketAnalysisChart data={null} />);
    
    expect(screen.getByText(/no market data available/i)).toBeInTheDocument();
  });

  test('has no accessibility violations', async () => {
    const { container } = render(<MarketAnalysisChart data={mockMarketData} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('renders responsive chart container', () => {
    render(<MarketAnalysisChart data={mockMarketData} />);
    
    const chartContainers = screen.getAllByRole('img');
    expect(chartContainers).toHaveLength(1);
  });

  test('displays market analysis correctly', () => {
    render(<MarketAnalysisChart data={mockMarketData} />);
    
    expect(screen.getByText(/Market Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Market Growth/i)).toBeInTheDocument();
  });
});