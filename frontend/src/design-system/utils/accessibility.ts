/**
 * RiskIntel360 Design System - Accessibility Utilities
 * WCAG 2.1 AA compliance utilities and helpers
 */

// Color contrast utilities
export const getContrastRatio = (foreground: string, background: string): number => {
  const getLuminance = (color: string): number => {
    // Convert hex to RGB
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16) / 255;
    const g = parseInt(hex.substr(2, 2), 16) / 255;
    const b = parseInt(hex.substr(4, 2), 16) / 255;

    // Calculate relative luminance
    const sRGB = [r, g, b].map((c) => {
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * sRGB[0] + 0.7152 * sRGB[1] + 0.0722 * sRGB[2];
  };

  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
};

export const meetsContrastRequirement = (
  foreground: string,
  background: string,
  level: 'AA' | 'AAA' = 'AA',
  size: 'normal' | 'large' = 'normal'
): boolean => {
  const ratio = getContrastRatio(foreground, background);
  
  if (level === 'AAA') {
    return size === 'large' ? ratio >= 4.5 : ratio >= 7;
  }
  
  return size === 'large' ? ratio >= 3 : ratio >= 4.5;
};

// Focus management utilities
export const createFocusTrap = (element: HTMLElement): (() => void) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ) as NodeListOf<HTMLElement>;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  };

  const handleEscapeKey = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      element.dispatchEvent(new CustomEvent('escape'));
    }
  };

  element.addEventListener('keydown', handleTabKey);
  element.addEventListener('keydown', handleEscapeKey);

  // Focus first element
  firstElement?.focus();

  // Return cleanup function
  return () => {
    element.removeEventListener('keydown', handleTabKey);
    element.removeEventListener('keydown', handleEscapeKey);
  };
};

export const restoreFocus = (previousActiveElement: Element | null) => {
  if (previousActiveElement && 'focus' in previousActiveElement) {
    (previousActiveElement as HTMLElement).focus();
  }
};

// ARIA utilities
export const generateId = (prefix: string = 'riskintel'): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

// Keyboard navigation utilities
export const isNavigationKey = (key: string): boolean => {
  return ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(key);
};

export const isActionKey = (key: string): boolean => {
  return ['Enter', ' ', 'Space'].includes(key);
};

export const handleKeyboardNavigation = (
  event: KeyboardEvent,
  items: HTMLElement[],
  currentIndex: number,
  options: {
    orientation?: 'horizontal' | 'vertical' | 'both';
    wrap?: boolean;
    onSelect?: (index: number) => void;
  } = {}
): number => {
  const { orientation = 'vertical', wrap = true, onSelect } = options;
  const { key } = event;

  let newIndex = currentIndex;

  switch (key) {
    case 'ArrowUp':
      if (orientation === 'vertical' || orientation === 'both') {
        newIndex = currentIndex > 0 ? currentIndex - 1 : wrap ? items.length - 1 : currentIndex;
        event.preventDefault();
      }
      break;
    case 'ArrowDown':
      if (orientation === 'vertical' || orientation === 'both') {
        newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : wrap ? 0 : currentIndex;
        event.preventDefault();
      }
      break;
    case 'ArrowLeft':
      if (orientation === 'horizontal' || orientation === 'both') {
        newIndex = currentIndex > 0 ? currentIndex - 1 : wrap ? items.length - 1 : currentIndex;
        event.preventDefault();
      }
      break;
    case 'ArrowRight':
      if (orientation === 'horizontal' || orientation === 'both') {
        newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : wrap ? 0 : currentIndex;
        event.preventDefault();
      }
      break;
    case 'Home':
      newIndex = 0;
      event.preventDefault();
      break;
    case 'End':
      newIndex = items.length - 1;
      event.preventDefault();
      break;
    case 'Enter':
    case ' ':
      onSelect?.(currentIndex);
      event.preventDefault();
      break;
  }

  if (newIndex !== currentIndex && items[newIndex]) {
    items[newIndex].focus();
  }

  return newIndex;
};

// Screen reader utilities
export const hideFromScreenReader = (element: HTMLElement) => {
  element.setAttribute('aria-hidden', 'true');
};

export const showToScreenReader = (element: HTMLElement) => {
  element.removeAttribute('aria-hidden');
};

export const setScreenReaderLabel = (element: HTMLElement, label: string) => {
  element.setAttribute('aria-label', label);
};

export const setScreenReaderDescription = (element: HTMLElement, description: string, descriptionId?: string) => {
  const id = descriptionId || generateId('description');
  element.setAttribute('aria-describedby', id);
  
  // Create description element if it doesn't exist
  if (!document.getElementById(id)) {
    const descElement = document.createElement('div');
    descElement.id = id;
    descElement.className = 'sr-only';
    descElement.textContent = description;
    document.body.appendChild(descElement);
  }
};

// Form accessibility utilities
export const associateLabel = (input: HTMLElement, label: HTMLElement) => {
  const inputId = input.id || generateId('input');
  const labelId = label.id || generateId('label');
  
  input.id = inputId;
  label.id = labelId;
  label.setAttribute('for', inputId);
  input.setAttribute('aria-labelledby', labelId);
};

export const setFieldError = (input: HTMLElement, errorMessage: string, errorId?: string) => {
  const id = errorId || generateId('error');
  input.setAttribute('aria-describedby', id);
  input.setAttribute('aria-invalid', 'true');
  
  // Create or update error element
  let errorElement = document.getElementById(id);
  if (!errorElement) {
    errorElement = document.createElement('div');
    errorElement.id = id;
    errorElement.className = 'error-message';
    errorElement.setAttribute('role', 'alert');
    input.parentNode?.appendChild(errorElement);
  }
  
  errorElement.textContent = errorMessage;
};

export const clearFieldError = (input: HTMLElement, errorId?: string) => {
  input.removeAttribute('aria-describedby');
  input.removeAttribute('aria-invalid');
  
  if (errorId) {
    const errorElement = document.getElementById(errorId);
    errorElement?.remove();
  }
};

// Financial data accessibility utilities
export const formatCurrencyForScreenReader = (amount: number, currency: string = 'USD'): string => {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  });
  
  const formatted = formatter.format(amount);
  
  // Add additional context for screen readers
  if (amount < 0) {
    return `negative ${formatted.replace('-', '')}`;
  }
  
  return formatted;
};

export const formatPercentageForScreenReader = (value: number, precision: number = 2): string => {
  const formatted = `${value.toFixed(precision)}%`;
  
  if (value > 0) {
    return `positive ${formatted}`;
  } else if (value < 0) {
    return `negative ${formatted.replace('-', '')}`;
  }
  
  return formatted;
};

export const formatRiskLevelForScreenReader = (level: 'low' | 'medium' | 'high' | 'critical'): string => {
  const descriptions = {
    low: 'low risk level',
    medium: 'medium risk level',
    high: 'high risk level',
    critical: 'critical risk level, immediate attention required',
  };
  
  return descriptions[level];
};

// Motion and animation utilities
export const respectsReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

export const getAnimationDuration = (defaultDuration: number): number => {
  return respectsReducedMotion() ? 0 : defaultDuration;
};

// High contrast mode utilities
export const supportsHighContrast = (): boolean => {
  return window.matchMedia('(prefers-contrast: high)').matches;
};

export const getHighContrastStyles = () => {
  if (!supportsHighContrast()) return {};
  
  return {
    border: '2px solid',
    outline: '1px solid',
    backgroundColor: 'Canvas',
    color: 'CanvasText',
  };
};

// Export all utilities
export const a11y = {
  // Color contrast
  getContrastRatio,
  meetsContrastRequirement,
  
  // Focus management
  createFocusTrap,
  restoreFocus,
  
  // ARIA utilities
  generateId,
  announceToScreenReader,
  hideFromScreenReader,
  showToScreenReader,
  setScreenReaderLabel,
  setScreenReaderDescription,
  
  // Keyboard navigation
  isNavigationKey,
  isActionKey,
  handleKeyboardNavigation,
  
  // Form accessibility
  associateLabel,
  setFieldError,
  clearFieldError,
  
  // Financial data
  formatCurrencyForScreenReader,
  formatPercentageForScreenReader,
  formatRiskLevelForScreenReader,
  
  // Motion and animation
  respectsReducedMotion,
  getAnimationDuration,
  
  // High contrast
  supportsHighContrast,
  getHighContrastStyles,
};

export default a11y;