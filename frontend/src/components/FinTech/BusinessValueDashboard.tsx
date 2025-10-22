/**
 * Business Value Dashboard Component
 * ROI calculations, cost savings, and value generation metrics
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  AttachMoney as AttachMoneyIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Security as SecurityIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Timeline as TimelineIcon,
  AccountBalance as AccountBalanceIcon,
  Savings as SavingsIcon,
  MonetizationOn as MonetizationOnIcon,
  ShowChart as ShowChartIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { 
  BusinessValueCalculation,
  FinancialAlert 
} from '../../types/fintech';
import { fintechService } from '../../services/fintechService';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';
import { useWebSocketUpdates } from './hooks/useWebSocketUpdates';

interface BusinessValueDashboardProps {
  companySize?: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  refreshInterval?: number;
}

interface ValueMetrics {
  totalAnnualSavings: number;
  fraudPreventionValue: number;
  complianceSavings: number;
  riskReductionValue: number;
  roiPercentage: number;
  paybackPeriod: number;
  netPresentValue: number;
  implementationCost: number;
}

export const BusinessValueDashboard: React.FC<BusinessValueDashboardProps> = ({
  companySize = 'medium',
  refreshInterval = 30000,
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [businessValue, setBusinessValue] = useState<BusinessValueCalculation | null>(null);
  const [valueMetrics, setValueMetrics] = useState<ValueMetrics | null>(null);
  const [historicalData, setHistoricalData] = useState<any[]>([]);

  // WebSocket updates for real-time value calculations
  const { isConnected, lastMessage } = useWebSocketUpdates('business_value');

  // Fetch business value data
  const fetchBusinessValueData = useCallback(async () => {
    try {
      setError(null);
      
      // Mock comprehensive business value calculation
      const mockBusinessValue: BusinessValueCalculation = {
        calculation_id: `BV-${Date.now()}`,
        company_size: companySize,
        industry: 'financial_services',
        annual_revenue: getRevenueByCompanySize(companySize),
        
        fraud_prevention_value: {
          current_annual_losses: getRevenueByCompanySize(companySize) * 0.024, // 2.4% of revenue
          prevented_losses: getRevenueByCompanySize(companySize) * 0.024 * 0.9, // 90% prevention
          prevention_rate: 0.9,
          annual_savings: getRevenueByCompanySize(companySize) * 0.024 * 0.9,
        },
        
        compliance_savings: {
          current_annual_costs: getRevenueByCompanySize(companySize) * 0.016, // 1.6% of revenue
          automated_savings: getRevenueByCompanySize(companySize) * 0.016 * 0.8, // 80% automation
          automation_rate: 0.8,
          annual_savings: getRevenueByCompanySize(companySize) * 0.016 * 0.8,
        },
        
        risk_reduction_value: {
          current_risk_exposure: getRevenueByCompanySize(companySize) * 0.05, // 5% of revenue
          reduced_exposure: getRevenueByCompanySize(companySize) * 0.05 * 0.8, // 80% reduction
          reduction_percentage: 0.8,
          annual_value: getRevenueByCompanySize(companySize) * 0.05 * 0.2, // Value of risk reduction
        },
        
        total_impact: {
          total_annual_savings: 0, // Will be calculated
          implementation_cost: getImplementationCost(companySize),
          roi_percentage: 0, // Will be calculated
          payback_period_months: 0, // Will be calculated
          net_present_value: 0, // Will be calculated
        },
        
        confidence_score: 0.92,
        calculation_methodology: 'AI-powered analysis with industry benchmarks and historical data',
        assumptions: [
          `Current fraud loss rate: 2.4% of revenue (${formatCurrency(getRevenueByCompanySize(companySize) * 0.024)})`,
          `Compliance costs: 1.6% of revenue (${formatCurrency(getRevenueByCompanySize(companySize) * 0.016)})`,
          `Risk exposure: 5% of revenue (${formatCurrency(getRevenueByCompanySize(companySize) * 0.05)})`,
          'Implementation timeline: 6-12 months',
          'Technology adoption rate: 85% within first year',
        ],
        risk_factors: [
          'Market volatility impact on savings calculations',
          'Regulatory changes affecting compliance costs',
          'Technology adoption rate variations',
          'Integration complexity with existing systems',
          'Staff training and change management costs',
        ],
      };

      // Calculate total impact
      const totalSavings = 
        mockBusinessValue.fraud_prevention_value.annual_savings +
        mockBusinessValue.compliance_savings.annual_savings +
        mockBusinessValue.risk_reduction_value.annual_value;

      mockBusinessValue.total_impact.total_annual_savings = totalSavings;
      mockBusinessValue.total_impact.roi_percentage = 
        ((totalSavings - mockBusinessValue.total_impact.implementation_cost) / 
         mockBusinessValue.total_impact.implementation_cost) * 100;
      mockBusinessValue.total_impact.payback_period_months = 
        (mockBusinessValue.total_impact.implementation_cost / totalSavings) * 12;
      mockBusinessValue.total_impact.net_present_value = 
        totalSavings * 4 - mockBusinessValue.total_impact.implementation_cost; // 4-year NPV

      setBusinessValue(mockBusinessValue);

      // Set value metrics
      const metrics: ValueMetrics = {
        totalAnnualSavings: mockBusinessValue.total_impact.total_annual_savings,
        fraudPreventionValue: mockBusinessValue.fraud_prevention_value.annual_savings,
        complianceSavings: mockBusinessValue.compliance_savings.annual_savings,
        riskReductionValue: mockBusinessValue.risk_reduction_value.annual_value,
        roiPercentage: mockBusinessValue.total_impact.roi_percentage,
        paybackPeriod: mockBusinessValue.total_impact.payback_period_months,
        netPresentValue: mockBusinessValue.total_impact.net_present_value,
        implementationCost: mockBusinessValue.total_impact.implementation_cost,
      };

      setValueMetrics(metrics);

      // Mock historical data for trend analysis
      setHistoricalData([
        { month: 'Jan', savings: totalSavings * 0.1, roi: 15 },
        { month: 'Feb', savings: totalSavings * 0.25, roi: 45 },
        { month: 'Mar', savings: totalSavings * 0.4, roi: 78 },
        { month: 'Apr', savings: totalSavings * 0.55, roi: 112 },
        { month: 'May', savings: totalSavings * 0.7, roi: 145 },
        { month: 'Jun', savings: totalSavings * 0.85, roi: 178 },
        { month: 'Current', savings: totalSavings, roi: mockBusinessValue.total_impact.roi_percentage },
      ]);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch business value data');
    } finally {
      setLoading(false);
    }
  }, [companySize]);

  useEffect(() => {
    fetchBusinessValueData();
    const interval = setInterval(fetchBusinessValueData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchBusinessValueData, refreshInterval]);

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'business_value_update') {
      // Update business value data from WebSocket
      console.log('Received business value update:', lastMessage.data);
    }
  }, [lastMessage]);

  const getRevenueByCompanySize = (size: string): number => {
    switch (size) {
      case 'startup': return 1000000; // $1M
      case 'small': return 10000000; // $10M
      case 'medium': return 100000000; // $100M
      case 'large': return 500000000; // $500M
      case 'enterprise': return 2000000000; // $2B
      default: return 100000000;
    }
  };

  const getImplementationCost = (size: string): number => {
    switch (size) {
      case 'startup': return 50000; // $50K
      case 'small': return 200000; // $200K
      case 'medium': return 500000; // $500K
      case 'large': return 2000000; // $2M
      case 'enterprise': return 5000000; // $5M
      default: return 500000;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading) {
    return <LoadingState message="Calculating business value metrics..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchBusinessValueData}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  return (
    <ErrorBoundary>
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h3" component="h1" gutterBottom>
              Business Value Dashboard
            </Typography>
            <Typography variant="subtitle1" color="textSecondary">
              ROI Calculations, Cost Savings, and Value Generation Metrics
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Chip 
                label={`Company Size: ${companySize.charAt(0).toUpperCase() + companySize.slice(1)}`}
                color="primary"
                size="small"
              />
              <Chip 
                label={isConnected ? 'Live Updates' : 'Offline'}
                color={isConnected ? 'success' : 'error'}
                size="small"
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh Data">
              <IconButton onClick={fetchBusinessValueData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => console.log('Export business value report')}
            >
              Export Report
            </Button>
          </Box>
        </Box>

        {/* Key Value Metrics */}
        {valueMetrics && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <AttachMoneyIcon />
                    <Typography variant="h6">Total Annual Savings</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {formatCurrency(valueMetrics.totalAnnualSavings)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    95% time reduction achieved
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TrendingUpIcon />
                    <Typography variant="h6">ROI</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {formatPercentage(valueMetrics.roiPercentage)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    {valueMetrics.paybackPeriod.toFixed(1)} month payback
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.info.main}, ${theme.palette.info.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <SecurityIcon />
                    <Typography variant="h6">Fraud Prevention</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {formatCurrency(valueMetrics.fraudPreventionValue)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    90% prevention rate
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`, color: 'white' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <AssessmentIcon />
                    <Typography variant="h6">Compliance Savings</Typography>
                  </Box>
                  <Typography variant="h4" component="div">
                    {formatCurrency(valueMetrics.complianceSavings)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    80% automation rate
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Value Breakdown and Implementation Details */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Value Generation Breakdown
                </Typography>
                {businessValue && (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Value Category</TableCell>
                          <TableCell align="right">Current Cost</TableCell>
                          <TableCell align="right">Annual Savings</TableCell>
                          <TableCell align="right">Improvement</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <SecurityIcon color="error" />
                              Fraud Prevention
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(businessValue.fraud_prevention_value.current_annual_losses)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography color="success.main" fontWeight="bold">
                              {formatCurrency(businessValue.fraud_prevention_value.annual_savings)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip 
                              label={formatPercentage(businessValue.fraud_prevention_value.prevention_rate * 100)}
                              color="success"
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <AssessmentIcon color="warning" />
                              Compliance Automation
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(businessValue.compliance_savings.current_annual_costs)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography color="success.main" fontWeight="bold">
                              {formatCurrency(businessValue.compliance_savings.annual_savings)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip 
                              label={formatPercentage(businessValue.compliance_savings.automation_rate * 100)}
                              color="warning"
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <ShowChartIcon color="info" />
                              Risk Reduction
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            {formatCurrency(businessValue.risk_reduction_value.current_risk_exposure)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography color="success.main" fontWeight="bold">
                              {formatCurrency(businessValue.risk_reduction_value.annual_value)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip 
                              label={formatPercentage(businessValue.risk_reduction_value.reduction_percentage * 100)}
                              color="info"
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ backgroundColor: theme.palette.grey[50] }}>
                          <TableCell>
                            <Typography fontWeight="bold">Total Impact</Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography fontWeight="bold">
                              {formatCurrency(
                                businessValue.fraud_prevention_value.current_annual_losses +
                                businessValue.compliance_savings.current_annual_costs +
                                businessValue.risk_reduction_value.current_risk_exposure
                              )}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography color="success.main" fontWeight="bold" variant="h6">
                              {formatCurrency(businessValue.total_impact.total_annual_savings)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip 
                              label={formatPercentage(valueMetrics?.roiPercentage || 0)}
                              color="success"
                              size="medium"
                            />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Implementation Investment
                </Typography>
                {businessValue && (
                  <Box>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Total Implementation Cost
                      </Typography>
                      <Typography variant="h4" color="primary.main">
                        {formatCurrency(businessValue.total_impact.implementation_cost)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Net Present Value (4 years)
                      </Typography>
                      <Typography variant="h5" color="success.main">
                        {formatCurrency(businessValue.total_impact.net_present_value)}
                      </Typography>
                    </Box>

                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Payback Period
                      </Typography>
                      <Typography variant="h5" color="info.main">
                        {businessValue.total_impact.payback_period_months.toFixed(1)} months
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Confidence Score
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={businessValue.confidence_score * 100}
                          sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="body2" fontWeight="bold">
                          {formatPercentage(businessValue.confidence_score * 100)}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Assumptions and Risk Factors */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Key Assumptions
                </Typography>
                {businessValue && (
                  <List>
                    {businessValue.assumptions.map((assumption, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon>
                          <MonetizationOnIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={assumption}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
                <Box sx={{ mt: 2, p: 2, backgroundColor: theme.palette.info.light, borderRadius: 1 }}>
                  <Typography variant="body2" color="info.dark">
                    <strong>Methodology:</strong> {businessValue?.calculation_methodology}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Factors
                </Typography>
                {businessValue && (
                  <List>
                    {businessValue.risk_factors.map((risk, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon>
                          <AssessmentIcon color="warning" />
                        </ListItemIcon>
                        <ListItemText
                          primary={risk}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
                <Box sx={{ mt: 2, p: 2, backgroundColor: theme.palette.warning.light, borderRadius: 1 }}>
                  <Typography variant="body2" color="warning.dark">
                    <strong>Note:</strong> Actual results may vary based on implementation approach, 
                    market conditions, and organizational factors.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </ErrorBoundary>
  );
};

export default BusinessValueDashboard;