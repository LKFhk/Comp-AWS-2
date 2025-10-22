/**
 * RiskIntel360 Design System - Theme Provider
 * Context provider for theme management with light/dark mode support
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { lightTheme, darkTheme, type RiskIntelTheme } from './theme';

// Theme mode type
export type ThemeMode = 'light' | 'dark' | 'system';

// Theme context interface
interface ThemeContextValue {
  mode: ThemeMode;
  actualMode: 'light' | 'dark';
  theme: RiskIntelTheme;
  toggleTheme: () => void;
  setThemeMode: (mode: ThemeMode) => void;
}

// Create theme context
const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

// Theme provider props
interface ThemeProviderProps {
  children: ReactNode;
  defaultMode?: ThemeMode;
  storageKey?: string;
}

// Local storage key for theme preference
const DEFAULT_STORAGE_KEY = 'riskintel360-theme-mode';

// Hook to detect system theme preference
const useSystemTheme = (): 'light' | 'dark' => {
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      try {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        return mediaQuery.matches ? 'dark' : 'light';
      } catch (error) {
        // Fallback for test environments or unsupported browsers
        return 'light';
      }
    }
    return 'light';
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;

    try {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e: MediaQueryListEvent) => {
        setSystemTheme(e.matches ? 'dark' : 'light');
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } catch (error) {
      // Ignore errors in test environments
      console.warn('matchMedia not supported:', error);
    }
  }, []);

  return systemTheme;
};

// Theme provider component
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultMode = 'system',
  storageKey = DEFAULT_STORAGE_KEY,
}) => {
  const systemTheme = useSystemTheme();
  
  // Initialize theme mode from localStorage or default
  const [mode, setMode] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') return defaultMode;
    
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored && ['light', 'dark', 'system'].includes(stored)) {
        return stored as ThemeMode;
      }
    } catch (error) {
      console.warn('Failed to read theme preference from localStorage:', error);
    }
    
    return defaultMode;
  });

  // Calculate actual theme mode (resolve 'system' to 'light' or 'dark')
  const actualMode: 'light' | 'dark' = mode === 'system' ? systemTheme : mode;

  // Get current theme based on actual mode
  const theme = actualMode === 'dark' ? darkTheme : lightTheme;

  // Save theme preference to localStorage
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(storageKey, mode);
    } catch (error) {
      console.warn('Failed to save theme preference to localStorage:', error);
    }
  }, [mode, storageKey]);

  // Toggle between light and dark (skips system)
  const toggleTheme = () => {
    setMode(prevMode => {
      if (prevMode === 'system') {
        return systemTheme === 'dark' ? 'light' : 'dark';
      }
      return prevMode === 'light' ? 'dark' : 'light';
    });
  };

  // Set specific theme mode
  const setThemeMode = (newMode: ThemeMode) => {
    setMode(newMode);
  };

  // Context value
  const contextValue: ThemeContextValue = {
    mode,
    actualMode,
    theme,
    toggleTheme,
    setThemeMode,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

// Hook to use theme context
export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Hook to get current theme mode
export const useThemeMode = () => {
  const { mode, actualMode, toggleTheme, setThemeMode } = useTheme();
  return { mode, actualMode, toggleTheme, setThemeMode };
};

// Hook to get theme-aware colors
export const useThemeColors = () => {
  const { theme } = useTheme();
  return {
    palette: theme.palette,
    financial: theme.financial.colors,
  };
};

// Hook to get financial theme utilities
export const useFinancialTheme = () => {
  const { theme } = useTheme();
  return theme.financial;
};

export default ThemeProvider;