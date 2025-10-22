declare module 'jest-axe' {
  import type { AxeResults } from 'axe-core';

  export function axe(
    html: Element | Document | string,
    options?: any
  ): Promise<AxeResults>;

  export const toHaveNoViolations: jest.ExpectExtendMap;

  export function configureAxe(options?: any): typeof axe;
}
