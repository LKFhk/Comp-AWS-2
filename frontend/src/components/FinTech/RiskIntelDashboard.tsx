/**
 * RiskIntel360 Main Dashboard Component
 * Executive overview with KPI metrics and navigation to specialized dashboards
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  CircularProgress,
  Dialog,
  AppBar,
  Toolbar,
  useMediaQuery,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Timeline as TimelineIcon,
  AttachMoney as AttachMoneyIcon,
  Close as CloseIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { 
  FinTechDashboardData, 
  FinancialAlert,
  BusinessValueCalculation 
} from '../../types/fintech';
import { fintechService } from '../../services/fintechService';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';
import { 
  InteractiveChart, 
  ExportFunctionality, 
  MobileOptimizedViews,
  AlertManagementSystem,
  type MobileDashboardCard,
  type ExportData 
} from './components';

interface RiskIntelDashboardProps {
  onNavigateTo?: (dashboard: string) => void;
  refreshInterval?: number;
  enableMobileView?: boolean;
  enableAdvancedFeatures?: boolean;
}

interface DashboardMetrics {
  totalAnalyses: number;
  activeAlerts: number;
  systemHealth: number;
  costSavings: number;
  fraudPrevented: number;
  complianceScore: number;
  processingTime: number;
  accuracy: number;
}

export const RiskIntelDashboard: React.FC<RiskIntelDashboardProps> = ({
  onNavigateTo,
  refreshInterval = 30000, // 30 seconds
  enableMobileView = true,
  enableAdvancedFeatures = true,
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<FinTechDashboardData | null>(null);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [businessValue, setBusinessValue] = useState<BusinessValueCalculation | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<FinancialAlert[]>([]);
  const [currentView, setCurrentView] = useState('dashboard');
  const [showAlertManagement, setShowAlertManagement] = useState(false);

  // Check if mobile view should be used
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Simulate async data fetch with a small delay
      await new Promise(resolve => setTimeout(resolve, 10));
      
      // Mock comprehensive dashboard data for financial risk validation
      const mockDashboardData: FinTechDashboardData = {
        summary: {
          active_analyses: 12,
          completed_today: 45,
          fraud_alerts: 3,
          compliance_issues: 1,
        },
        recent_analyses: [
          {
            analysis_id: 'RISK-VAL-001',
            status: 'completed',
            message: 'FinTech Startup - Credit risk validation completed (Risk Score: 0.32)',
            estimated_completion: '2024-10-20T12:00:00.000Z',
          },
          {
            analysis_id: 'FRAUD-VAL-002',
            status: 'in_progress',
            message: 'Payment Gateway - Fraud pattern detection in progress',
            estimated_completion: '2024-10-20T12:05:00.000Z',
          },
          {
            analysis_id: 'COMP-VAL-003',
            status: 'completed',
            message: 'Regional Bank - Regulatory compliance validation completed (Score: 94.2%)',
            estimated_completion: '2024-10-20T11:30:00.000Z',
          },
        ],
        active_alerts: [
          {
            alert_id: 'ALERT-001',
            alert_type: 'fraud_detection',
            severity: 'high',
            title: 'High-Risk Transaction Pattern Detected',
            description: 'Cryptocurrency Exchange - Unusual transaction pattern flagged with 89% fraud probability',
            created_at: '2024-10-20T12:00:00.000Z',
          },
          {
            alert_id: 'ALERT-002',
            alert_type: 'compliance',
            severity: 'medium',
            title: 'Regulatory Compliance Gap Identified',
            description: 'Investment Fund - CFPB regulation compliance gap requires remediation',
            created_at: '2024-10-20T11:30:00.000Z',
          },
          {
            alert_id: 'ALERT-003',
            alert_type: 'risk_assessment',
            severity: 'medium',
            title: 'Elevated Credit Risk Detected',
            description: 'P2P Lending Platform - Portfolio credit risk score increased to 0.68',
            created_at: '2024-10-20T11:00:00.000Z',
          },
        ],
        performance_metrics: {
          average_response_time: 3.2,
          success_rate: 98.5,
          fraud_detection_accuracy: 95.2,
          compliance_score: 87.3,
        },
        business_value: {
          monthly_savings: 850000,
          fraud_prevented: 2100000,
          compliance_cost_reduction: 450000,
          roi_percentage: 340,
        },
      };

      setDashboardData(mockDashboardData);

      // Calculate comprehensive metrics
      const mockMetrics: DashboardMetrics = {
        totalAnalyses: mockDashboardData.summary.active_analyses + mockDashboardData.summary.completed_today,
        activeAlerts: mockDashboardData.active_alerts.length,
        systemHealth: 99.2,
        costSavings: mockDashboardData.business_value.monthly_savings,
        fraudPrevented: mockDashboardData.business_value.fraud_prevented,
        complianceScore: mockDashboardData.performance_metrics.compliance_score,
        processingTime: mockDashboardData.performance_metrics.average_response_time,
        accuracy: mockDashboardData.performance_metrics.fraud_detection_accuracy,
      };

      setMetrics(mockMetrics);

      // Mock business value calculation
      const mockBusinessValue: BusinessValueCalculation = {
        calculation_id: 'BV-001',
        company_size: 'large',
        industry: 'financial_services',
        annual_revenue: 500000000,
        fraud_prevention_value: {
          current_annual_losses: 12000000,
          prevented_losses: 10800000,
          prevention_rate: 0.9,
          annual_savings: 10800000,
        },
        compliance_savings: {
          current_annual_costs: 8000000,
          automated_savings: 6400000,
          automation_rate: 0.8,
          annual_savings: 6400000,
        },
        risk_reduction_value: {
          current_risk_exposure: 25000000,
          reduced_exposure: 20000000,
          reduction_percentage: 0.8,
          annual_value: 5000000,
        },
        total_impact: {
          total_annual_savings: 22200000,
          implementation_cost: 2000000,
          roi_percentage: 1010,
          payback_period_months: 1.1,
          net_present_value: 88800000,
        },
        confidence_score: 0.92,
        calculation_methodology: 'AI-powered analysis with industry benchmarks',
        assumptions: [
          'Current fraud loss rate: 2.4% of revenue',
          'Compliance costs: 1.6% of revenue',
          'Risk exposure: 5% of revenue',
        ],
        risk_factors: [
          'Market volatility impact',
          'Regulatory changes',
          'Technology adoption rate',
        ],
      };

      setBusinessValue(mockBusinessValue);
      setRecentAlerts(mockDashboardData.active_alerts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchDashboardData, refreshInterval]);

  const getAlertSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return theme.palette.error.main;
      case 'medium':
        return theme.palette.warning.main;
      case 'low':
        return theme.palette.info.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getAlertIcon = (alertType: string) => {
    switch (alertType) {
      case 'fraud_detection':
        return <SecurityIcon />;
      case 'compliance':
        return <AssessmentIcon />;
      case 'kyc_verification':
        return <PersonIcon />;
      default:
        return <WarningIcon />;
    }
  };

  const handleNavigate = (dashboard: string) => {
    onNavigateTo?.(dashboard);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Prepare mobile dashboard cards
  const mobileDashboardCards: MobileDashboardCard[] = useMemo(() => {
    if (!metrics) return [];
    
    return [
      {
        id: 'savings',
        title: 'Monthly Savings',
        value: formatCurrency(metrics.costSavings),
        subtitle: 'Through fraud prevention and compliance automation',
        icon: <AttachMoneyIcon />,
        color: theme.palette.primary.main,
        trend: 'up',
        trendValue: '+15%',
        priority: 'high',
        onClick: () => handleNavigate('business-value'),
      },
      {
        id: 'fraud-prevented',
        title: 'Fraud Prevented',
        value: formatCurrency(metrics.fraudPrevented),
        subtitle: 'ML-powered anomaly detection with 95% accuracy',
        icon: <SecurityIcon />,
        color: theme.palette.success.main,
        trend: 'up',
        trendValue: '+8%',
        priority: 'high',
        onClick: () => handleNavigate('fraud'),
      },
      {
        id: 'compliance',
        title: 'Compliance Score',
        value: `${metrics.complianceScore.toFixed(1)}%`,
        subtitle: 'Real-time regulatory monitoring across SEC, FINRA, CFPB',
        icon: <AssessmentIcon />,
        color: theme.palette.info.main,
        trend: 'up',
        trendValue: '+2%',
        priority: 'high',
        onClick: () => handleNavigate('compliance'),
      },
      {
        id: 'response-time',
        title: 'Avg Response Time',
        value: `${metrics.processingTime}s`,
        subtitle: 'Sub-5-second agent response for real-time risk assessment',
        icon: <TimelineIcon />,
        color: theme.palette.warning.main,
        trend: 'down',
        trendValue: '-0.3s',
        priority: 'medium',
        onClick: () => handleNavigate('performance'),
      },
      {
        id: 'system-health',
        title: 'System Health',
        value: `${metrics.systemHealth}%`,
        subtitle: 'Uptime and availability',
        icon: <CheckCircleIcon />,
        color: theme.palette.success.main,
        trend: 'neutral',
        priority: 'medium',
      },
      {
        id: 'active-analyses',
        title: 'Active Analyses',
        value: metrics.totalAnalyses.toString(),
        subtitle: 'Currently processing',
        icon: <DashboardIcon />,
        color: theme.palette.secondary.main,
        trend: 'up',
        trendValue: '+3',
        priority: 'low',
      },
    ];
  }, [metrics, theme, formatCurrency, handleNavigate]);

  // Prepare export data
  const exportData: ExportData = useMemo(() => ({
    title: 'RiskIntel360 Executive Dashboard Report',
    data: [
      { metric: 'Monthly Savings', value: metrics?.costSavings || 0, format: 'currency' },
      { metric: 'Fraud Prevented', value: metrics?.fraudPrevented || 0, format: 'currency' },
      { metric: 'Compliance Score', value: metrics?.complianceScore || 0, format: 'percentage' },
      { metric: 'Response Time', value: metrics?.processingTime || 0, format: 'seconds' },
      { metric: 'System Health', value: metrics?.systemHealth || 0, format: 'percentage' },
      { metric: 'Active Analyses', value: metrics?.totalAnalyses || 0, format: 'number' },
    ],
    metadata: {
      generatedBy: 'RiskIntel360 Platform',
      generatedAt: '2024-10-20T12:00:00.000Z',
      description: 'Executive dashboard summary with key performance indicators',
      filters: { period: 'current', view: 'executive' },
    },
  }), [metrics]);

  if (loading) {
    return <LoadingState message="Loading RiskIntel360 dashboard..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchDashboardData}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  // Mobile view
  if (isMobile && enableMobileView) {
    return (
      <ErrorBoundary>
        <MobileOptimizedViews
          cards={mobileDashboardCards}
          activeView={currentView}
          onViewChange={setCurrentView}
          onRefresh={fetchDashboardData}
          onSearch={(query) => console.log('Search:', query)}
          onFilter={() => console.log('Filter')}
          notifications={recentAlerts.length}
          config={{
            showBottomNavigation: true,
            showSpeedDial: true,
            compactMode: false,
            swipeGestures: true,
            pullToRefresh: true,
          }}
        />
        
        {/* Alert Management Dialog for Mobile */}
        {showAlertManagement && (
          <Dialog
            fullScreen
            open={showAlertManagement}
            onClose={() => setShowAlertManagement(false)}
          >
            <AppBar sx={{ position: 'relative' }}>
              <Toolbar>
                <IconButton
                  edge="start"
                  color="inherit"
                  onClick={() => setShowAlertManagement(false)}
                >
                  <CloseIcon />
                </IconButton>
                <Typography sx={{ ml: 2, flex: 1 }} variant="h6">
                  Alert Management
                </Typography>
              </Toolbar>
            </AppBar>
            <AlertManagementSystem
              enableRealTimeUpdates={true}
              onRuleCreate={(rule) => console.log('Rule created:', rule)}
              onAlertAction={(alertId, action) => console.log('Alert action:', alertId, action)}
            />
          </Dialog>
        )}
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <Box data-testid="dashboard" sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h3" component="h1" gutterBottom>
              RiskIntel360 Dashboard
            </Typography>
            <Typography variant="subtitle1" color="textSecondary">
              Real-time Fraud Detection, Compliance Monitoring, and Risk Assessment
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh Dashboard">
              <IconButton onClick={fetchDashboardData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            {enableAdvancedFeatures && (
              <ExportFunctionality
                data={exportData}
                onExportStart={(format) => console.log('Export started:', format)}
                onExportComplete={(format, success) => console.log('Export completed:', format, success)}
                onExportError={(error) => console.error('Export error:', error)}
                buttonVariant="outlined"
                buttonSize="medium"
              />
            )}
            <Button
              variant="outlined"
              startIcon={<NotificationsIcon />}
              onClick={() => setShowAlertManagement(true)}
            >
              Alerts ({recentAlerts.length})
            </Button>
          </Box>
        </Box>

        {/* Key Performance Indicators */}
        {metrics && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <AttachMoneyIcon />
                    <Typography variant="h6">Monthly Savings</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {formatCurrency(metrics.costSavings)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Through fraud prevention and compliance automation
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <SecurityIcon />
                    <Typography variant="h6">Fraud Prevented</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {formatCurrency(metrics.fraudPrevented)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    ML-powered anomaly detection with 95% accuracy
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.info.main}, ${theme.palette.info.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <AssessmentIcon />
                    <Typography variant="h6">Compliance Score</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {metrics.complianceScore.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8, mt: 1 }}>
                    Real-time regulatory monitoring across SEC, FINRA, CFPB
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TimelineIcon />
                    <Typography variant="h6">Avg Response Time</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {metrics.processingTime}s
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Sub-5-second agent response for real-time risk assessment
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* System Health and Business Value */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Health & Performance
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <CircularProgress
                        variant="determinate"
                        value={metrics?.systemHealth || 0}
                        size={80}
                        thickness={4}
                        sx={{ color: theme.palette.success.main }}
                      />
                      <Typography variant="h6" sx={{ mt: 1 }}>
                        {metrics?.systemHealth}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        System Uptime
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <CircularProgress
                        variant="determinate"
                        value={metrics?.accuracy || 0}
                        size={80}
                        thickness={4}
                        sx={{ color: theme.palette.primary.main }}
                      />
                      <Typography variant="h6" sx={{ mt: 1 }}>
                        {metrics?.accuracy}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Detection Accuracy
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Active Analyses: {metrics?.totalAnalyses}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Active Alerts: {metrics?.activeAlerts}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Business Value Generated
                </Typography>
                {businessValue && (
                  <Box>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Total Annual Savings
                      </Typography>
                      <Typography variant="h4" color="success.main">
                        {formatCurrency(businessValue.total_impact.total_annual_savings)}
                      </Typography>
                    </Box>
                    <Grid container spacing={2}>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="textSecondary">
                          ROI
                        </Typography>
                        <Typography variant="h6" color="primary.main">
                          {businessValue.total_impact.roi_percentage}%
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="textSecondary">
                          Payback
                        </Typography>
                        <Typography variant="h6" color="info.main">
                          {businessValue.total_impact.payback_period_months.toFixed(1)}mo
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="textSecondary">
                          Confidence
                        </Typography>
                        <Typography variant="h6" color="success.main">
                          {(businessValue.confidence_score * 100).toFixed(1)}%
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Dashboard Navigation */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12}>
            <Typography variant="h5" gutterBottom>
              Specialized Dashboards
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              data-testid="compliance-card"
              sx={{ cursor: 'pointer', '&:hover': { elevation: 4 } }}
              onClick={() => handleNavigate('compliance')}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <AssessmentIcon sx={{ fontSize: 48, color: theme.palette.primary.main, mb: 1 }} />
                <Typography variant="h6" gutterBottom>
                  Compliance Monitoring
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  SEC, FINRA, CFPB compliance validation with automated remediation
                </Typography>
                <Chip 
                  label={`${dashboardData?.summary.compliance_issues || 0} gaps`} 
                  size="small" 
                  color="warning" 
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              data-testid="fraud-card"
              sx={{ cursor: 'pointer', '&:hover': { elevation: 4 } }}
              onClick={() => handleNavigate('fraud')}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <SecurityIcon sx={{ fontSize: 48, color: theme.palette.error.main, mb: 1 }} />
                <Typography variant="h6" gutterBottom>
                  Fraud Detection
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Unsupervised ML fraud pattern detection with 90% false positive reduction
                </Typography>
                <Chip 
                  label={`${dashboardData?.summary.fraud_alerts || 0} alerts`} 
                  size="small" 
                  color="error" 
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              data-testid="market-card"
              sx={{ cursor: 'pointer', '&:hover': { elevation: 4 } }}
              onClick={() => handleNavigate('market')}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <TrendingUpIcon sx={{ fontSize: 48, color: theme.palette.success.main, mb: 1 }} />
                <Typography variant="h6" gutterBottom>
                  Market Intelligence
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Volatility, liquidity, and economic exposure validation
                </Typography>
                <Chip 
                  label="Real-time" 
                  size="small" 
                  color="success" 
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              data-testid="kyc-card"
              sx={{ cursor: 'pointer', '&:hover': { elevation: 4 } }}
              onClick={() => handleNavigate('kyc')}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <PersonIcon sx={{ fontSize: 48, color: theme.palette.info.main, mb: 1 }} />
                <Typography variant="h6" gutterBottom>
                  KYC Verification
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Automated customer verification with risk scoring
                </Typography>
                <Chip 
                  label="AI-Powered" 
                  size="small" 
                  color="info" 
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Recent Activity and Alerts */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Analysis Activity
                </Typography>
                <List>
                  {dashboardData?.recent_analyses.map((analysis, index) => (
                    <React.Fragment key={analysis.analysis_id}>
                      <ListItem>
                        <ListItemIcon>
                          {analysis.status === 'completed' ? 
                            <CheckCircleIcon color="success" /> : 
                            <CircularProgress size={24} />
                          }
                        </ListItemIcon>
                        <ListItemText
                          primaryTypographyProps={{ component: 'div' }}
                          secondaryTypographyProps={{ component: 'div' }}
                          primary={analysis.analysis_id}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="textSecondary">
                                {analysis.message}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {analysis.estimated_completion && 
                                  new Date(analysis.estimated_completion).toLocaleString()
                                }
                              </Typography>
                            </Box>
                          }
                        />
                        <Chip
                          label={analysis.status}
                          size="small"
                          color={analysis.status === 'completed' ? 'success' : 'warning'}
                        />
                      </ListItem>
                      {index < (dashboardData?.recent_analyses.length || 0) - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Active Alerts
                </Typography>
                <List>
                  {recentAlerts.map((alert, index) => (
                    <React.Fragment key={alert.alert_id}>
                      <ListItem>
                        <ListItemIcon>
                          <Avatar sx={{ 
                            bgcolor: getAlertSeverityColor(alert.severity), 
                            width: 32, 
                            height: 32 
                          }}>
                            {getAlertIcon(alert.alert_type)}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primaryTypographyProps={{ component: 'div' }}
                          secondaryTypographyProps={{ component: 'div' }}
                          primary={alert.title}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="textSecondary">
                                {alert.description}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {new Date(alert.created_at).toLocaleString()}
                              </Typography>
                            </Box>
                          }
                        />
                        <Chip
                          label={alert.severity}
                          size="small"
                          sx={{
                            backgroundColor: getAlertSeverityColor(alert.severity),
                            color: 'white',
                          }}
                        />
                      </ListItem>
                      {index < recentAlerts.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Alert Management System for Desktop */}
        {enableAdvancedFeatures && (
          <Dialog
            open={showAlertManagement}
            onClose={() => setShowAlertManagement(false)}
            maxWidth="lg"
            fullWidth
            PaperProps={{
              sx: { height: '80vh' }
            }}
          >
            <AlertManagementSystem
              enableRealTimeUpdates={true}
              onRuleCreate={(rule) => console.log('Rule created:', rule)}
              onAlertAction={(alertId, action) => console.log('Alert action:', alertId, action)}
            />
          </Dialog>
        )}
      </Box>
    </ErrorBoundary>
  );
};

export default RiskIntelDashboard;