/**
 * Jest type definitions for test files
 * Ensures all test files have proper Jest and Testing Library types
 */

/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

// Extend global namespace with Jest globals
declare global {
  // Jest globals
  const describe: jest.Describe;
  const it: jest.It;
  const test: jest.It;
  const expect: jest.Expect;
  const beforeEach: jest.Lifecycle;
  const afterEach: jest.Lifecycle;
  const beforeAll: jest.Lifecycle;
  const afterAll: jest.Lifecycle;

  // Jest namespace
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toHaveTextContent(text: string | RegExp): R;
      toHaveClass(className: string): R;
      toHaveStyle(style: Record<string, any>): R;
      toBeVisible(): R;
      toBeDisabled(): R;
      toBeEnabled(): R;
      toHaveAttribute(attr: string, value?: string): R;
    }
  }

  // Global test utilities
  namespace NodeJS {
    interface Global {
      fetch: jest.MockedFunction<typeof fetch>;
      WebSocket: jest.MockedFunction<any>;
      gc?: () => void;
    }
  }
}

export {};
