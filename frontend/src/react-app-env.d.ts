/// <reference types="react-scripts" />
/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />
/// <reference types="react" />
/// <reference types="react-dom" />

// Extend Jest matchers for jest-axe
declare namespace jest {
  interface Matchers<R = void> {
    toHaveNoViolations(): R;
  }
}

// Ensure JSX namespace is available
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}
