import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from './LoadingSpinner';

describe('LoadingSpinner', () => {
  test('renders loading spinner with default message', () => {
    render(<LoadingSpinner />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Analyzing financial risk...')).toBeInTheDocument();
  });

  test('renders loading spinner with custom message', () => {
    render(<LoadingSpinner message="Processing risk analysis..." />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Processing risk analysis...')).toBeInTheDocument();
  });

  test('renders loading spinner without message', () => {
    render(<LoadingSpinner message="" />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.queryByText('Analyzing financial risk...')).not.toBeInTheDocument();
  });
});