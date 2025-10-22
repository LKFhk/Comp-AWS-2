/**
 * RiskIntel360 Design System - Button Tests
 * Unit tests for Button component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from './Button';
import { ThemeProvider } from '../../theme/ThemeProvider';

// Test wrapper with theme provider
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>{children}</ThemeProvider>
);

describe('Button Component', () => {
  it('renders with default props', () => {
    render(
      <TestWrapper>
        <Button>Default Button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button')).toBeInTheDocument();
    expect(screen.getByText('Default Button')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(
      <TestWrapper>
        <Button onClick={handleClick}>Click Me</Button>
      </TestWrapper>
    );
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(
      <TestWrapper>
        <Button loading>Loading Button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders financial variants', () => {
    render(
      <TestWrapper>
        <Button variant="financial" financialAction="buy">
          Buy Stock
        </Button>
      </TestWrapper>
    );
    
    expect(screen.getByText('Buy Stock')).toBeInTheDocument();
  });

  it('renders risk variants', () => {
    render(
      <TestWrapper>
        <Button variant="risk" riskLevel="high">
          High Risk
        </Button>
      </TestWrapper>
    );
    
    expect(screen.getByText('High Risk')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(
      <TestWrapper>
        <Button disabled>Disabled Button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders with different sizes', () => {
    const { rerender } = render(
      <TestWrapper>
        <Button size="small">Small Button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByText('Small Button')).toBeInTheDocument();
    
    rerender(
      <TestWrapper>
        <Button size="large">Large Button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByText('Large Button')).toBeInTheDocument();
  });

  it('renders with icons', () => {
    const TestIcon = () => <span data-testid="test-icon">Icon</span>;
    
    render(
      <TestWrapper>
        <Button icon={<TestIcon />} iconPosition="start">
          Button with Icon
        </Button>
      </TestWrapper>
    );
    
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    expect(screen.getByText('Button with Icon')).toBeInTheDocument();
  });
});