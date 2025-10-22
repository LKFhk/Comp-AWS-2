/// <reference types="jest" />
/// <reference types="@testing-library/jest-dom" />

import { AxeResults } from 'axe-core';

declare global {
  namespace jest {
    interface Matchers<R = void> {
      /**
       * Asserts that the given AxeResults object has no accessibility violations
       */
      toHaveNoViolations(): R;
    }
  }
}

export {};
