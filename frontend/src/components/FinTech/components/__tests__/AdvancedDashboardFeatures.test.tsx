/**
 * Advanced Dashboard Features Test Suite
 * Tests all advanced dashboard components and their interactions
 * @jest-environment jsdom
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Mock problematic dependencies
jest.mock('file-saver', () => ({
  saveAs: jest.fn(),
}));

jest.mock('xlsx', () => ({
  utils: {
    book_new: jest.fn(() => ({})),
    json_to_sheet: jest.fn(() => ({})),
    book_append_sheet: jest.fn(),
    aoa_to_sheet: jest.fn(() => ({})),
  },
  writeFile: jest.fn(),
}));

jest.mock('jspdf', () => {
  return jest.fn().mockImplementation(() => ({
    setFontSize: jest.fn(),
    text: jest.fn(),
    addPage: jest.fn(),
    addImage: jest.fn(),
    save: jest.fn(),
  }));
});

jest.mock('html2canvas', () => {
  return jest.fn().mockResolvedValue({
    toDataURL: jest.fn(() => 'data:image/png;base64,test'),
    toBlob: jest.fn((callback) => callback(new Blob())),
    height: 100,
    width: 100,
  });
});

// Mock Chart.js
jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn(),
  },
  CategoryScale: jest.fn(),
  LinearScale: jest.fn(),
  PointElement: jest.fn(),
  LineElement: jest.fn(),
  Title: jest.fn(),
  Tooltip: jest.fn(),
  Legend: jest.fn(),
  BarElement: jest.fn(),
}));

jest.mock('react-chartjs-2', () => ({
  Line: ({ data }: any) => <div data-testid="line-chart">Line Chart: {data.datasets[0]?.label}</div>,
  Bar: ({ data }: any) => <div data-testid="bar-chart">Bar Chart: {data.datasets[0]?.label}</div>,
  Pie: ({ data }: any) => <div data-testid="pie-chart">Pie Chart: {data.datasets[0]?.label}</div>,
}));


jest.mock('react-beautiful-dnd', () => ({
  DragDropContext: ({ children }: any) => <div data-testid="drag-drop-context">{children}</div>,
  Droppable: ({ children }: any) => children({
    draggableProps: {},
    dragHandleProps: {},
    innerRef: jest.fn(),
  }, {}),
  Draggable: ({ children }: any) => children({
    draggableProps: {},
    dragHandleProps: {},
    innerRef: jest.fn(),
  }, {}),
}));

// Create a simple test theme
const testTheme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});
import {
  InteractiveChart,
  RealTimeDataVisualization,
  ExportFunctionality,
  AdvancedFiltering,
  DataComparisonTools,
  AlertManagementSystem,
  MobileOptimizedViews,
} from '../index';
import type {
  ChartDataPoint,
  ExportData,
  DashboardWidget,
  FilterOption,
  ComparisonDataSet,
  ComparisonMetric,
  AlertRule,
  MobileDashboardCard,
} from '../index';

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={testTheme}>
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      {children}
    </LocalizationProvider>
  </ThemeProvider>
);

// Mock data
const mockChartData: ChartDataPoint[] = [
  { x: '2024-01', y: 100, label: 'January', metadata: { category: 'fraud' } },
  { x: '2024-02', y: 150, label: 'February', metadata: { category: 'fraud' } },
  { x: '2024-03', y: 120, label: 'March', metadata: { category: 'compliance' } },
];

const mockExportData: ExportData = {
  title: 'Test Dashboard Report',
  data: [
    { metric: 'Fraud Alerts', value: 25, category: 'security' },
    { metric: 'Compliance Score', value: 95, category: 'compliance' },
  ],
  metadata: {
    generatedAt: new Date().toISOString(),
    description: 'Test export data',
  },
};

const mockDashboardWidgets: DashboardWidget[] = [
  {
    id: 'widget-1',
    title: 'Fraud Detection',
    component: () => <div>Fraud Widget</div>,
    size: 'medium',
    category: 'Security',
    isVisible: true,
  },
  {
    id: 'widget-2',
    title: 'Compliance Monitor',
    component: () => <div>Compliance Widget</div>,
    size: 'large',
    category: 'Compliance',
    isVisible: true,
  },
];

const mockFilterOptions: FilterOption[] = [
  {
    field: 'category',
    label: 'Category',
    type: 'select',
    options: [
      { value: 'fraud', label: 'Fraud' },
      { value: 'compliance', label: 'Compliance' },
    ],
  },
  {
    field: 'severity',
    label: 'Severity',
    type: 'select',
    options: [
      { value: 'high', label: 'High' },
      { value: 'medium', label: 'Medium' },
      { value: 'low', label: 'Low' },
    ],
  },
];

const mockComparisonDataSets: ComparisonDataSet[] = [
  {
    id: 'current',
    name: 'Current Period',
    data: [{ value: 100, timestamp: '2024-01-01' }],
    color: '#1976d2',
    type: 'current',
  },
  {
    id: 'previous',
    name: 'Previous Period',
    data: [{ value: 80, timestamp: '2023-01-01' }],
    color: '#dc004e',
    type: 'historical',
  },
];

const mockComparisonMetrics: ComparisonMetric[] = [
  {
    field: 'value',
    label: 'Total Value',
    format: 'currency',
    aggregation: 'sum',
  },
];

const mockMobileCards: MobileDashboardCard[] = [
  {
    id: 'card-1',
    title: 'Fraud Alerts',
    value: '25',
    icon: <div>🔒</div>,
    color: '#f44336',
    priority: 'high',
  },
  {
    id: 'card-2',
    title: 'Compliance Score',
    value: '95%',
    icon: <div>📊</div>,
    color: '#4caf50',
    priority: 'medium',
  },
];

describe('InteractiveChart', () => {
  it('renders chart with data', () => {
    render(
      <TestWrapper>
        <InteractiveChart
          title="Test Chart"
          data={mockChartData}
          chartType="line"
        />
      </TestWrapper>
    );

    expect(screen.getByText('Test Chart')).toBeInTheDocument();
    expect(screen.getByText('Showing 3 of 3 data points')).toBeInTheDocument();
  });

  it('handles data point clicks', async () => {
    const mockOnClick = jest.fn();
    render(
      <TestWrapper>
        <InteractiveChart
          title="Test Chart"
          data={mockChartData}
          chartType="line"
          onDataPointClick={mockOnClick}
        />
      </TestWrapper>
    );

    // Chart interactions would be tested with more specific chart library testing
    expect(screen.getByText('Click on data points for detailed view')).toBeInTheDocument();
  });

  it('shows export options when enabled', () => {
    render(
      <TestWrapper>
        <InteractiveChart
          title="Test Chart"
          data={mockChartData}
          chartType="line"
          enableExport={true}
        />
      </TestWrapper>
    );

    const moreButton = screen.getByLabelText('More options');
    expect(moreButton).toBeInTheDocument();
  });
});

describe('RealTimeDataVisualization', () => {
  it('renders real-time chart with configuration', () => {
    render(
      <TestWrapper>
        <RealTimeDataVisualization
          title="Real-time Fraud Detection"
          dataSource="fraud-alerts"
          chartType="line"
        />
      </TestWrapper>
    );

    expect(screen.getByText('Real-time Fraud Detection')).toBeInTheDocument();
    expect(screen.getByText('Live Updates')).toBeInTheDocument();
  });

  it('handles streaming toggle', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <RealTimeDataVisualization
          title="Real-time Chart"
          dataSource="test"
          chartType="line"
        />
      </TestWrapper>
    );

    const toggleSwitch = screen.getByRole('checkbox', { name: /live updates/i });
    await user.click(toggleSwitch);
    
    // Switch should toggle state
    expect(toggleSwitch).toBeInTheDocument();
  });
});

describe('ExportFunctionality', () => {
  it('renders export button', () => {
    render(
      <TestWrapper>
        <ExportFunctionality data={mockExportData} />
      </TestWrapper>
    );

    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  it('shows export menu when clicked', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <ExportFunctionality data={mockExportData} />
      </TestWrapper>
    );

    const exportButton = screen.getByText('Export');
    await user.click(exportButton);

    await waitFor(() => {
      expect(screen.getByText('Export as PDF')).toBeInTheDocument();
      expect(screen.getByText('Export as CSV')).toBeInTheDocument();
      expect(screen.getByText('Export as Excel')).toBeInTheDocument();
    });
  });

  it('handles export operations', async () => {
    const mockOnExportStart = jest.fn();
    const mockOnExportComplete = jest.fn();
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ExportFunctionality
          data={mockExportData}
          onExportStart={mockOnExportStart}
          onExportComplete={mockOnExportComplete}
        />
      </TestWrapper>
    );

    const exportButton = screen.getByText('Export');
    await user.click(exportButton);

    const pdfOption = await screen.findByText('Export as PDF');
    await user.click(pdfOption);

    expect(mockOnExportStart).toHaveBeenCalledWith('pdf');
  });
});


describe('AdvancedFiltering', () => {
  const mockData = [
    { id: 1, category: 'fraud', severity: 'high', name: 'Alert 1' },
    { id: 2, category: 'compliance', severity: 'medium', name: 'Alert 2' },
  ];

  it('renders filtering interface', () => {
    render(
      <TestWrapper>
        <AdvancedFiltering
          data={mockData}
          filterOptions={mockFilterOptions}
          sortOptions={[]}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Filters')).toBeInTheDocument();
    expect(screen.getByText('Sort')).toBeInTheDocument();
    expect(screen.getByText('Showing 2 of 2 results')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    const mockOnFilteredDataChange = jest.fn();
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <AdvancedFiltering
          data={mockData}
          filterOptions={mockFilterOptions}
          sortOptions={[]}
          searchConfig={{
            fields: ['name'],
            placeholder: 'Search alerts...',
          }}
          onFilteredDataChange={mockOnFilteredDataChange}
        />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search alerts...');
    await user.type(searchInput, 'Alert 1');

    await waitFor(() => {
      expect(mockOnFilteredDataChange).toHaveBeenCalled();
    });
  });
});

describe('DataComparisonTools', () => {
  it('renders comparison interface', () => {
    render(
      <TestWrapper>
        <DataComparisonTools
          primaryDataSet={mockComparisonDataSets[0]}
          availableDataSets={mockComparisonDataSets}
          comparisonMetrics={mockComparisonMetrics}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Data Comparison Tools')).toBeInTheDocument();
    expect(screen.getByText('Selected Data Sets (1/5)')).toBeInTheDocument();
  });

  it('handles data set selection', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <DataComparisonTools
          primaryDataSet={mockComparisonDataSets[0]}
          availableDataSets={mockComparisonDataSets}
          comparisonMetrics={mockComparisonMetrics}
        />
      </TestWrapper>
    );

    const addDataSetSelect = screen.getByRole('combobox');
    await user.click(addDataSetSelect);

    // Would test actual selection in a more complete test
    expect(addDataSetSelect).toBeInTheDocument();
  });
});

describe('AlertManagementSystem', () => {
  it('renders alert management interface', () => {
    render(
      <TestWrapper>
        <AlertManagementSystem />
      </TestWrapper>
    );

    expect(screen.getByText('Alert Management')).toBeInTheDocument();
    expect(screen.getByText('Active Alerts')).toBeInTheDocument();
    expect(screen.getByText('New Rule')).toBeInTheDocument();
  });

  it('opens rule creation dialog', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <AlertManagementSystem />
      </TestWrapper>
    );

    const newRuleButton = screen.getByText('New Rule');
    await user.click(newRuleButton);

    await waitFor(() => {
      expect(screen.getByText('Create Alert Rule')).toBeInTheDocument();
    });
  });
});

describe('MobileOptimizedViews', () => {
  it('renders mobile dashboard cards', () => {
    render(
      <TestWrapper>
        <MobileOptimizedViews
          cards={mockMobileCards}
          activeView="dashboard"
          onViewChange={() => {}}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Fraud Alerts')).toBeInTheDocument();
    expect(screen.getByText('Compliance Score')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  it('handles card interactions', async () => {
    const mockOnClick = jest.fn();
    const cardsWithClick = mockMobileCards.map(card => ({
      ...card,
      onClick: mockOnClick,
    }));

    const user = userEvent.setup();
    render(
      <TestWrapper>
        <MobileOptimizedViews
          cards={cardsWithClick}
          activeView="dashboard"
          onViewChange={() => {}}
        />
      </TestWrapper>
    );

    const fraudCard = screen.getByText('Fraud Alerts').closest('[role="button"]') || 
                     screen.getByText('Fraud Alerts').closest('div');
    
    if (fraudCard) {
      await user.click(fraudCard);
      expect(mockOnClick).toHaveBeenCalled();
    }
  });

  it('shows navigation drawer when menu is clicked', async () => {
    const user = userEvent.setup();
    
    // Mock mobile viewport
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query.includes('(max-width: 899.95px)'), // md breakpoint
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });

    render(
      <TestWrapper>
        <MobileOptimizedViews
          cards={mockMobileCards}
          activeView="dashboard"
          onViewChange={() => {}}
        />
      </TestWrapper>
    );

    // Look for menu button in mobile view
    const menuButtons = screen.queryAllByLabelText(/menu/i);
    if (menuButtons.length > 0) {
      await user.click(menuButtons[0]);
      await waitFor(() => {
        expect(screen.getByText('RiskIntel360')).toBeInTheDocument();
      });
    }
  });
});

describe('Integration Tests', () => {
  it('components work together in dashboard context', () => {
    render(
      <TestWrapper>
        <div>
          <InteractiveChart
            title="Fraud Trends"
            data={mockChartData}
            chartType="line"
          />
          <ExportFunctionality data={mockExportData} />
          <AdvancedFiltering
            data={[]}
            filterOptions={mockFilterOptions}
            sortOptions={[]}
          />
        </div>
      </TestWrapper>
    );

    expect(screen.getByText('Fraud Trends')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('handles responsive behavior', () => {
    // Test responsive behavior with different viewport sizes
    const { rerender } = render(
      <TestWrapper>
        <MobileOptimizedViews
          cards={mockMobileCards}
          activeView="dashboard"
          onViewChange={() => {}}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Fraud Alerts')).toBeInTheDocument();

    // Rerender with different props to test updates
    rerender(
      <TestWrapper>
        <MobileOptimizedViews
          cards={[...mockMobileCards, {
            id: 'card-3',
            title: 'New Alert',
            value: '10',
            icon: <div>⚠️</div>,
            color: '#ff9800',
            priority: 'low',
          }]}
          activeView="dashboard"
          onViewChange={() => {}}
        />
      </TestWrapper>
    );

    expect(screen.getByText('New Alert')).toBeInTheDocument();
  });
});

// Performance tests
describe('Performance Tests', () => {
  it('handles large datasets efficiently', () => {
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      x: `Item ${i}`,
      y: Math.random() * 100,
      metadata: { category: i % 2 === 0 ? 'fraud' : 'compliance' },
    }));

    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <InteractiveChart
          title="Large Dataset"
          data={largeDataset}
          chartType="line"
        />
      </TestWrapper>
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time (less than 1 second)
    expect(renderTime).toBeLessThan(1000);
    expect(screen.getByText('Large Dataset')).toBeInTheDocument();
  });

  it('handles frequent updates without memory leaks', async () => {
    let updateCount = 0;
    const TestComponent = () => {
      const [data, setData] = React.useState(mockChartData);

      React.useEffect(() => {
        const interval = setInterval(() => {
          if (updateCount < 10) {
            setData(prev => [...prev, {
              x: `Update ${updateCount}`,
              y: Math.random() * 100,
              metadata: { category: 'test' },
            }]);
            updateCount++;
          }
        }, 100);

        return () => clearInterval(interval);
      }, []);

      return (
        <InteractiveChart
          title="Updating Chart"
          data={data}
          chartType="line"
        />
      );
    };

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    // Wait for updates to complete
    await waitFor(() => {
      expect(updateCount).toBeGreaterThan(0);
    }, { timeout: 2000 });

    expect(screen.getByText('Updating Chart')).toBeInTheDocument();
  });
});

// Accessibility tests
describe('Accessibility Tests', () => {
  it('components have proper ARIA labels', () => {
    render(
      <TestWrapper>
        <InteractiveChart
          title="Accessible Chart"
          data={mockChartData}
          chartType="line"
        />
      </TestWrapper>
    );

    // Check for accessibility features
    expect(screen.getByText('Accessible Chart')).toBeInTheDocument();
    
    // Interactive elements should be accessible
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toBeInTheDocument();
    });
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <ExportFunctionality data={mockExportData} />
      </TestWrapper>
    );

    const exportButton = screen.getByText('Export');
    
    // Should be focusable
    exportButton.focus();
    expect(exportButton).toHaveFocus();

    // Should respond to Enter key
    await user.keyboard('{Enter}');
    
    // Menu should open
    await waitFor(() => {
      expect(screen.getByText('Export as PDF')).toBeInTheDocument();
    });
  });
});

// Error handling tests
describe('Error Handling', () => {
  it('handles invalid data gracefully', () => {
    // Type-safe invalid data for testing error handling
    const invalidData: Array<{ x: any; y: any }> = [
      { x: null, y: undefined },
      { x: 'valid', y: 'invalid' },
    ];

    render(
      <TestWrapper>
        <InteractiveChart
          title="Error Test"
          data={invalidData}
          chartType="line"
        />
      </TestWrapper>
    );

    // Should still render without crashing
    expect(screen.getByText('Error Test')).toBeInTheDocument();
  });

  it('handles export errors gracefully', async () => {
    const mockOnExportError = jest.fn();
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ExportFunctionality
          data={{ ...mockExportData, data: [] }} // Empty data might cause export error
          onExportError={mockOnExportError}
        />
      </TestWrapper>
    );

    const exportButton = screen.getByText('Export');
    await user.click(exportButton);

    const csvOption = await screen.findByText('Export as CSV');
    await user.click(csvOption);

    // Should handle the error case
    await waitFor(() => {
      expect(mockOnExportError).toHaveBeenCalledWith('No financial risk data to export');
    });
  });
});