/**
 * RiskIntel360 Design System - Error Boundary Component
 * Comprehensive error handling with fallback UI
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Alert,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material';

// Error boundary props
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  showRefresh?: boolean;
  title?: string;
  message?: string;
  level?: 'page' | 'component' | 'widget';
}

// Error boundary state
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showDetails: boolean;
  retryCount: number;
}

// Error fallback component props
interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  onRetry: () => void;
  showDetails: boolean;
  onToggleDetails: () => void;
  title: string;
  message: string;
  level: 'page' | 'component' | 'widget';
  showRefresh: boolean;
}

// Error fallback component
const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  onRetry,
  showDetails,
  onToggleDetails,
  title,
  message,
  level,
  showRefresh,
}) => {
  const isPageLevel = level === 'page';
  const isComponentLevel = level === 'component';

  // Page-level error (full screen)
  if (isPageLevel) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 3,
          bgcolor: 'background.default',
        }}
      >
        <Card sx={{ maxWidth: 600, width: '100%' }}>
          <CardContent sx={{ textAlign: 'center', p: 4 }}>
            <ErrorIcon
              sx={{
                fontSize: 64,
                color: 'error.main',
                mb: 2,
              }}
            />
            <Typography variant="h4" component="h1" gutterBottom>
              {title}
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
              {message}
            </Typography>
            
            <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
              <Typography variant="body2">
                <strong>Error:</strong> {error?.message || 'Unknown error occurred'}
              </Typography>
            </Alert>

            {error && (
              <Box sx={{ mb: 3 }}>
                <Button
                  startIcon={showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  onClick={onToggleDetails}
                  size="small"
                  color="inherit"
                >
                  {showDetails ? 'Hide' : 'Show'} Technical Details
                </Button>
                
                <Collapse in={showDetails}>
                  <Box
                    sx={{
                      mt: 2,
                      p: 2,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      textAlign: 'left',
                      maxHeight: 200,
                      overflow: 'auto',
                    }}
                  >
                    <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {error.stack}
                    </Typography>
                  </Box>
                </Collapse>
              </Box>
            )}
          </CardContent>
          
          <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
            {showRefresh && (
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={onRetry}
                size="large"
              >
                Try Again
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<BugReportIcon />}
              onClick={() => {
                // Report error to monitoring service
                console.error('Error reported:', error, errorInfo);
              }}
            >
              Report Issue
            </Button>
          </CardActions>
        </Card>
      </Box>
    );
  }

  // Component-level error (card format)
  if (isComponentLevel) {
    return (
      <Card sx={{ m: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <ErrorIcon color="error" />
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" gutterBottom>
                {title}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                {message}
              </Typography>
              
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  {error?.message || 'Unknown error occurred'}
                </Typography>
              </Alert>

              {error && (
                <Box>
                  <IconButton
                    size="small"
                    onClick={onToggleDetails}
                    aria-label="toggle details"
                  >
                    {showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                  
                  <Collapse in={showDetails}>
                    <Box
                      sx={{
                        mt: 1,
                        p: 1,
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                        fontSize: '0.75rem',
                        fontFamily: 'monospace',
                        maxHeight: 150,
                        overflow: 'auto',
                      }}
                    >
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {error.stack}
                      </pre>
                    </Box>
                  </Collapse>
                </Box>
              )}
            </Box>
          </Box>
        </CardContent>
        
        {showRefresh && (
          <CardActions>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={onRetry}
            >
              Retry
            </Button>
          </CardActions>
        )}
      </Card>
    );
  }

  // Widget-level error (minimal format)
  return (
    <Box
      sx={{
        p: 2,
        textAlign: 'center',
        border: 1,
        borderColor: 'error.main',
        borderRadius: 1,
        bgcolor: 'error.light',
        color: 'error.contrastText',
      }}
    >
      <ErrorIcon sx={{ fontSize: 32, mb: 1 }} />
      <Typography variant="body2" sx={{ mb: 1 }}>
        {title}
      </Typography>
      {showRefresh && (
        <Button
          size="small"
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
          sx={{ color: 'inherit', borderColor: 'currentColor' }}
        >
          Retry
        </Button>
      )}
    </Box>
  );
};

// Error boundary class component
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Report error to monitoring service
    this.reportError(error, errorInfo);
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      window.clearTimeout(this.retryTimeoutId);
    }
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // In a real application, you would send this to your error reporting service
    // e.g., Sentry, LogRocket, Bugsnag, etc.
    console.error('Error reported to monitoring service:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    });
  };

  private handleRetry = () => {
    const { retryCount } = this.state;
    
    // Limit retry attempts
    if (retryCount >= 3) {
      console.warn('Maximum retry attempts reached');
      return;
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
      retryCount: retryCount + 1,
    });

    // Reset retry count after successful render
    this.retryTimeoutId = window.setTimeout(() => {
      this.setState({ retryCount: 0 });
    }, 30000); // Reset after 30 seconds
  };

  private handleToggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails,
    }));
  };

  render() {
    const { hasError, error, errorInfo, showDetails } = this.state;
    const {
      children,
      fallback,
      showDetails: showDetailsProps = true,
      showRefresh = true,
      title = 'Something went wrong',
      message = 'An unexpected error occurred. Please try refreshing the page.',
      level = 'component',
    } = this.props;

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Use default error fallback
      return (
        <ErrorFallback
          error={error}
          errorInfo={errorInfo}
          onRetry={this.handleRetry}
          showDetails={showDetails && showDetailsProps}
          onToggleDetails={this.handleToggleDetails}
          title={title}
          message={message}
          level={level}
          showRefresh={showRefresh}
        />
      );
    }

    return children;
  }
}

export default ErrorBoundary;