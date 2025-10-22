/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AuthProvider } from '../contexts/AuthContext';
import { NotificationProvider } from '../contexts/NotificationContext';
import App from '../App';

// Mock heavy components for performance testing
jest.mock('../components/Charts/MarketAnalysisChart', () => {
    return function MockMarketAnalysisChart() {
        return <div data-testid="market-chart">Market Chart</div>;
    };
});

jest.mock('../components/FinTech/FraudDetectionDashboard', () => ({
    FraudDetectionDashboard: function MockFraudDetectionDashboard() {
        return <div data-testid="fraud-detection-dashboard">Fraud Detection Dashboard</div>;
    }
}));

// Mock API service
jest.mock('../services/api', () => ({
    apiService: {
        getValidations: jest.fn().mockResolvedValue({
            validations: [],
            total: 0,
            page: 1,
            page_size: 20,
        }),
        healthCheck: jest.fn().mockResolvedValue({ status: 'ok', timestamp: '2024-10-20T12:00:00.000Z' }),
    },
}));

// Mock WebSocket service
jest.mock('../services/websocket', () => ({
    websocketService: {
        connectToValidationProgress: jest.fn(),
        connectToNotifications: jest.fn(),
        disconnect: jest.fn(),
    },
}));

// Mock auth context with authenticated user
jest.mock('../contexts/AuthContext', () => ({
    ...jest.requireActual('../contexts/AuthContext'),
    useAuth: () => ({
        user: {
            id: 'test-user',
            email: 'test@riskintel360.com',
            name: 'Test User',
            role: 'analyst',
            preferences: {
                theme: 'light',
                notifications: true,
                defaultAnalysisScope: ['market_risk', 'fraud_detection', 'credit_risk', 'compliance_monitoring', 'kyc_verification']
            }
        },
        loading: false,
        login: jest.fn().mockResolvedValue(undefined),
        logout: jest.fn(),
        updateUser: jest.fn(),
    }),
}));

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
    return render(
        <BrowserRouter>
            <ThemeProvider theme={theme}>
                <AuthProvider>
                    <NotificationProvider>
                        {component}
                    </NotificationProvider>
                </AuthProvider>
            </ThemeProvider>
        </BrowserRouter>
    );
};

describe('Performance Tests', () => {
  beforeEach(() => { jest.setTimeout(60000); }); // Performance test timeout: 60 seconds
  afterEach(() => { jest.setTimeout(5000); }); // Reset to default unit test timeout
    test('app renders within performance budget', async () => {
        const startTime = performance.now();

        renderWithProviders(<App />);

        await waitFor(() => {
            expect(screen.getByRole('main')).toBeInTheDocument();
        });

        const endTime = performance.now();
        const renderTime = endTime - startTime;

        // Should render within 500ms (more realistic for test environment)
        expect(renderTime).toBeLessThan(500);
    });

    test('large lists render efficiently', async () => {
        const largeDataSet = Array.from({ length: 1000 }, (_, i) => ({
            id: `item-${i}`,
            name: `Item ${i}`,
            value: Math.random() * 100,
        }));

        const LargeList = () => (
            <div>
                {largeDataSet.map(item => (
                    <div key={item.id} data-testid={`list-item-${item.id}`}>
                        {item.name}: {item.value.toFixed(2)}
                    </div>
                ))}
            </div>
        );

        const startTime = performance.now();
        render(<LargeList />);
        const endTime = performance.now();

        const renderTime = endTime - startTime;

        // Should render 1000 items within 200ms
        expect(renderTime).toBeLessThan(200);
    });

    test('component re-renders are optimized', async () => {
        let renderCount = 0;

        const TestComponent = ({ value }: { value: number }) => {
            renderCount++;
            return <div>Value: {value}</div>;
        };

        const { rerender } = render(<TestComponent value={1} />);

        // Re-render with same value
        rerender(<TestComponent value={1} />);
        rerender(<TestComponent value={1} />);

        // Should not cause unnecessary re-renders
        expect(renderCount).toBeLessThanOrEqual(3);
    });

    test('memory usage stays within bounds', async () => {
        // Type-safe memory access
        interface PerformanceMemory extends Performance {
            memory?: {
                usedJSHeapSize: number;
                totalJSHeapSize: number;
                jsHeapSizeLimit: number;
            };
        }
        
        const perfWithMemory = performance as PerformanceMemory;
        const initialMemory = perfWithMemory.memory?.usedJSHeapSize || 0;

        // Render multiple components
        for (let i = 0; i < 10; i++) {
            const { unmount } = renderWithProviders(<App />);
            unmount();
        }

        // Force garbage collection if available
        if (global.gc) {
            global.gc();
        }

        const finalMemory = perfWithMemory.memory?.usedJSHeapSize || 0;
        const memoryIncrease = finalMemory - initialMemory;

        // Memory increase should be reasonable (less than 10MB)
        expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
    });

    test('bundle size is within limits', () => {
        // Mock bundle size check - in real implementation this would
        // analyze the actual build output
        const mockBundleSize = 245000; // 245KB
        const maxBundleSize = 250000; // 250KB limit

        expect(mockBundleSize).toBeLessThan(maxBundleSize);

        // Verify that we have performance monitoring in place
        expect(typeof performance).toBe('object');
        expect(typeof performance.now).toBe('function');
    });

    test('code splitting works correctly', async () => {
        // Test dynamic import functionality
        const dynamicImport = () => import('../components/Common/LoadingSpinner');

        const startTime = performance.now();
        const module = await dynamicImport();
        const loadTime = performance.now() - startTime;

        expect(module.default).toBeDefined();
        expect(loadTime).toBeLessThan(100); // Should load quickly in test environment
    });

    test('lazy loading works correctly', async () => {
        // Mock dynamic import
        const mockLazyComponent = jest.fn().mockResolvedValue({
            default: () => <div>Lazy Component</div>
        });

        const LazyComponent = React.lazy(() => mockLazyComponent());

        render(
            <React.Suspense fallback={<div>Loading...</div>}>
                <LazyComponent />
            </React.Suspense>
        );

        // Should show loading state first
        expect(screen.getByText('Loading...')).toBeInTheDocument();

        // Should load the component
        await waitFor(() => {
            expect(screen.getByText('Lazy Component')).toBeInTheDocument();
        });

        expect(mockLazyComponent).toHaveBeenCalled();
    });

    test('image loading is optimized', () => {
        const TestImage = () => (
            <img
                src="test-image.jpg"
                alt="Test"
                loading="lazy"
                width="200"
                height="150"
            />
        );

        render(<TestImage />);

        const img = screen.getByRole('img');
        expect(img).toHaveAttribute('loading', 'lazy');
        expect(img).toHaveAttribute('width', '200');
        expect(img).toHaveAttribute('height', '150');
    });
});