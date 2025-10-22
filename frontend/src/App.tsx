import React, { Suspense, lazy, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import ValidationWizard from './pages/ValidationWizard/ValidationWizard';
import ValidationResults from './pages/ValidationResults';
import ValidationProgress from './pages/ValidationProgress/ValidationProgress';
import Results from './pages/Results/Results';
import Settings from './pages/Settings/Settings';
import CredentialsManagement from './pages/CredentialsManagement/CredentialsManagement';
import Login from './pages/Login/Login';
import CompetitionDemo from './pages/CompetitionDemo/CompetitionDemo';
import LoadingSpinner from './components/Common/LoadingSpinner';
import { ErrorBoundary } from './design-system/components/ErrorBoundary/ErrorBoundary';
import { ProtectedRoute } from './components/Common/ProtectedRoute';
import { OnboardingFlow } from './components/Common/OnboardingFlow';
import { logInfo } from './utils/logger';

// Lazy load pages
const LogsPage = lazy(() => import('./pages/Logs/LogsPage'));

// Lazy load FinTech dashboards for better performance
const RiskIntelDashboard = lazy(() => import('./components/FinTech/RiskIntelDashboard').then(m => ({ default: m.RiskIntelDashboard })));
// @ts-ignore
const ComplianceMonitoringDashboard = lazy(() => import('./components/FinTech/ComplianceMonitoringDashboard'));
const FraudDetectionDashboard = lazy(() => import('./components/FinTech/FraudDetectionDashboard').then(m => ({ default: m.FraudDetectionDashboard })));
const MarketIntelligenceDashboard = lazy(() => import('./components/FinTech/MarketIntelligenceDashboard').then(m => ({ default: m.MarketIntelligenceDashboard })));
const KYCVerificationDashboard = lazy(() => import('./components/FinTech/KYCVerificationDashboard').then(m => ({ default: m.KYCVerificationDashboard })));
const BusinessValueDashboard = lazy(() => import('./components/FinTech/BusinessValueDashboard').then(m => ({ default: m.BusinessValueDashboard })));
const PerformanceDashboard = lazy(() => import('./components/FinTech/PerformanceDashboard').then(m => ({ default: m.PerformanceDashboard })));

function App() {
  const { user, loading } = useAuth();

  // Initialize logging on app start
  useEffect(() => {
    logInfo('RiskIntel360 Application Started', 'App', {
      version: process.env.REACT_APP_VERSION || '1.0.0',
      environment: process.env.NODE_ENV,
      apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000'
    });
  }, []);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <LoadingSpinner size={60} />
      </Box>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <ErrorBoundary>
      <Layout>
        <Suspense fallback={<LoadingSpinner size={60} message="Loading dashboard..." />}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            
            {/* FinTech Dashboards with Role-Based Access */}
            <Route 
              path="/fintech/risk-intel" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'analyst', 'executive']}>
                  <RiskIntelDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/fintech/compliance" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'compliance_officer', 'analyst']}>
                  <ComplianceMonitoringDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/fintech/fraud" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'security_analyst', 'analyst']}>
                  <FraudDetectionDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/fintech/market" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'analyst', 'trader']}>
                  <MarketIntelligenceDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/fintech/kyc" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'compliance_officer', 'kyc_specialist']}>
                  <KYCVerificationDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/fintech/business-value" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'executive', 'analyst']}>
                  <BusinessValueDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/fintech/performance" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'analyst']}>
                  <PerformanceDashboard />
                </ProtectedRoute>
              } 
            />
            
            {/* Existing Routes */}
            <Route path="/validation/new" element={<ValidationWizard />} />
            <Route path="/validation/:id/progress" element={<ValidationProgress />} />
            <Route path="/validation/:id/results" element={<ValidationResults />} />
            <Route path="/results" element={<Results />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/credentials" element={<CredentialsManagement />} />
            <Route path="/competition-demo" element={<CompetitionDemo />} />
            <Route path="/logs" element={<LogsPage />} />
            
            {/* Onboarding */}
            <Route path="/onboarding" element={<OnboardingFlow />} />
            
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </ErrorBoundary>
  );
}

export default App;