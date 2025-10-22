/**
 * KYC Verification Dashboard Component
 * Customer risk scoring and verification status
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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Badge,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  Person as PersonIcon,
  Verified as VerifiedIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Security as SecurityIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { 
  KYCVerificationResult, 
  FinancialAlert 
} from '../../types/fintech';
import { fintechService } from '../../services/fintechService';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';

interface KYCVerificationDashboardProps {
  customerId?: string;
  onAlertClick?: (alert: FinancialAlert) => void;
  refreshInterval?: number;
}

interface KYCCustomer {
  customer_id: string;
  name: string;
  email: string;
  phone: string;
  registration_date: string;
  verification_status: string;
  risk_score: number;
  documents_submitted: string[];
  verification_level: string;
  last_updated: string;
}

interface KYCSummary {
  totalCustomers: number;
  verifiedCustomers: number;
  pendingVerification: number;
  rejectedCustomers: number;
  avgRiskScore: number;
  avgProcessingTime: number;
  lastUpdated: string;
}

interface VerificationStep {
  step: string;
  status: 'completed' | 'pending' | 'failed';
  description: string;
  timestamp?: string;
  details?: string;
}

export const KYCVerificationDashboard: React.FC<KYCVerificationDashboardProps> = ({
  customerId,
  onAlertClick,
  refreshInterval = 30000, // 30 seconds
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kycResults, setKycResults] = useState<KYCVerificationResult[]>([]);
  const [customers, setCustomers] = useState<KYCCustomer[]>([]);
  const [alerts, setAlerts] = useState<FinancialAlert[]>([]);
  const [summary, setSummary] = useState<KYCSummary | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<KYCVerificationResult | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [verificationSteps, setVerificationSteps] = useState<VerificationStep[]>([]);

  // Fetch KYC verification data
  const fetchKYCData = useCallback(async () => {
    try {
      setError(null);
      
      const response = await fintechService.verifyKYC({
        customer_id: customerId || 'all',
        verification_level: 'standard',
        document_types: ['id', 'address_proof', 'income_verification'],
        risk_tolerance: 'medium',
      });

      // Mock KYC verification results
      const mockKYCResults: KYCVerificationResult[] = [
        {
          customer_id: 'CUST-001',
          verification_status: 'verified',
          risk_score: 0.25,
          verification_level: 'enhanced',
          documents_verified: ['government_id', 'address_proof', 'income_statement'],
          sanctions_screening: {
            status: 'clear',
            lists_checked: ['OFAC', 'EU_Sanctions', 'UN_Sanctions'],
            last_checked: new Date().toISOString(),
          },
          pep_screening: {
            status: 'clear',
            risk_level: 'low',
            last_checked: new Date().toISOString(),
          },
          adverse_media_screening: {
            status: 'clear',
            articles_found: 0,
            last_checked: new Date().toISOString(),
          },
          recommended_action: 'approve',
          confidence_score: 0.92,
        },
        {
          customer_id: 'CUST-002',
          verification_status: 'pending',
          risk_score: 0.65,
          verification_level: 'standard',
          documents_verified: ['government_id'],
          sanctions_screening: {
            status: 'clear',
            lists_checked: ['OFAC'],
            last_checked: new Date().toISOString(),
          },
          pep_screening: {
            status: 'flagged',
            risk_level: 'medium',
            details: 'Potential PEP match requires manual review',
            last_checked: new Date().toISOString(),
          },
          adverse_media_screening: {
            status: 'pending',
            articles_found: 2,
            last_checked: new Date().toISOString(),
          },
          recommended_action: 'manual_review',
          confidence_score: 0.78,
        },
        {
          customer_id: 'CUST-003',
          verification_status: 'rejected',
          risk_score: 0.89,
          verification_level: 'basic',
          documents_verified: [],
          sanctions_screening: {
            status: 'flagged',
            lists_checked: ['OFAC', 'EU_Sanctions'],
            details: 'Match found on sanctions list',
            last_checked: new Date().toISOString(),
          },
          pep_screening: {
            status: 'clear',
            risk_level: 'low',
            last_checked: new Date().toISOString(),
          },
          adverse_media_screening: {
            status: 'flagged',
            articles_found: 5,
            details: 'Multiple negative articles found',
            last_checked: new Date().toISOString(),
          },
          recommended_action: 'reject',
          confidence_score: 0.95,
        },
      ];

      setKycResults(mockKYCResults);

      // Mock customer data
      const mockCustomers: KYCCustomer[] = [
        {
          customer_id: 'CUST-001',
          name: 'John Smith',
          email: 'john.smith@email.com',
          phone: '+1-555-0123',
          registration_date: new Date(Date.now() - 86400000).toISOString(),
          verification_status: 'verified',
          risk_score: 0.25,
          documents_submitted: ['government_id', 'address_proof', 'income_statement'],
          verification_level: 'enhanced',
          last_updated: new Date().toISOString(),
        },
        {
          customer_id: 'CUST-002',
          name: 'Sarah Johnson',
          email: 'sarah.johnson@email.com',
          phone: '+1-555-0456',
          registration_date: new Date(Date.now() - 172800000).toISOString(),
          verification_status: 'pending',
          risk_score: 0.65,
          documents_submitted: ['government_id'],
          verification_level: 'standard',
          last_updated: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          customer_id: 'CUST-003',
          name: 'Michael Brown',
          email: 'michael.brown@email.com',
          phone: '+1-555-0789',
          registration_date: new Date(Date.now() - 259200000).toISOString(),
          verification_status: 'rejected',
          risk_score: 0.89,
          documents_submitted: [],
          verification_level: 'basic',
          last_updated: new Date(Date.now() - 7200000).toISOString(),
        },
      ];

      setCustomers(mockCustomers);

      // Calculate summary
      const totalCustomers = mockKYCResults.length;
      const verifiedCustomers = mockKYCResults.filter(r => r.verification_status === 'verified').length;
      const pendingVerification = mockKYCResults.filter(r => r.verification_status === 'pending').length;
      const rejectedCustomers = mockKYCResults.filter(r => r.verification_status === 'rejected').length;
      const avgRiskScore = mockKYCResults.reduce((sum, r) => sum + r.risk_score, 0) / totalCustomers;

      setSummary({
        totalCustomers,
        verifiedCustomers,
        pendingVerification,
        rejectedCustomers,
        avgRiskScore: avgRiskScore * 100,
        avgProcessingTime: 24, // Mock: 24 hours average
        lastUpdated: new Date().toISOString(),
      });

      // Mock alerts for high-risk customers
      const highRiskAlerts: FinancialAlert[] = mockKYCResults
        .filter(result => result.risk_score > 0.7 || result.verification_status === 'rejected')
        .map(result => ({
          alert_id: `KYC-${result.customer_id}`,
          alert_type: 'kyc_verification',
          severity: result.risk_score > 0.8 ? 'high' : 'medium',
          title: `High Risk Customer - ${result.customer_id}`,
          description: `Customer flagged with ${(result.risk_score * 100).toFixed(1)}% risk score`,
          created_at: new Date().toISOString(),
          metadata: { 
            customer_id: result.customer_id,
            risk_score: result.risk_score,
            verification_status: result.verification_status,
          },
        }));

      setAlerts(highRiskAlerts);

      // Mock verification steps for detailed view
      setVerificationSteps([
        {
          step: 'Document Collection',
          status: 'completed',
          description: 'Customer documents received and validated',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          details: 'Government ID, Address Proof, Income Statement',
        },
        {
          step: 'Identity Verification',
          status: 'completed',
          description: 'Identity verified against government databases',
          timestamp: new Date(Date.now() - 2700000).toISOString(),
          details: 'Match confidence: 98.5%',
        },
        {
          step: 'Sanctions Screening',
          status: 'completed',
          description: 'Screened against global sanctions lists',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          details: 'Clear on all major sanctions lists',
        },
        {
          step: 'PEP Screening',
          status: 'pending',
          description: 'Politically Exposed Person screening in progress',
          details: 'Potential match requires manual review',
        },
        {
          step: 'Adverse Media Check',
          status: 'pending',
          description: 'Checking for negative news and media coverage',
        },
        {
          step: 'Final Review',
          status: 'pending',
          description: 'Compliance team final review and decision',
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch KYC verification data');
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    fetchKYCData();
    const interval = setInterval(fetchKYCData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchKYCData, refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
        return theme.palette.success.main;
      case 'rejected':
        return theme.palette.error.main;
      case 'pending':
        return theme.palette.warning.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
        return <VerifiedIcon color="success" />;
      case 'rejected':
        return <ErrorIcon color="error" />;
      case 'pending':
        return <ScheduleIcon color="warning" />;
      default:
        return <PersonIcon color="disabled" />;
    }
  };

  const getRiskLevelColor = (riskScore: number) => {
    if (riskScore >= 0.8) return theme.palette.error.main;
    if (riskScore >= 0.6) return theme.palette.warning.main;
    if (riskScore >= 0.4) return theme.palette.info.main;
    return theme.palette.success.main;
  };

  const getRiskLevel = (riskScore: number) => {
    if (riskScore >= 0.8) return 'High';
    if (riskScore >= 0.6) return 'Medium';
    if (riskScore >= 0.4) return 'Low';
    return 'Very Low';
  };

  const handleCustomerClick = (result: KYCVerificationResult) => {
    setSelectedCustomer(result);
    setDialogOpen(true);
  };

  const handleAlertClick = (alert: FinancialAlert) => {
    onAlertClick?.(alert);
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <CancelIcon color="error" />;
      default:
        return <ScheduleIcon color="warning" />;
    }
  };

  if (loading) {
    return <LoadingState message="Loading KYC verification data..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchKYCData}>
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
          <Typography variant="h4" component="h1">
            KYC Verification Dashboard
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh Data">
              <IconButton onClick={fetchKYCData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => console.log('Export KYC report')}
            >
              Export Report
            </Button>
          </Box>
        </Box>

        {/* Summary Cards */}
        {summary && (
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <VerifiedIcon color="success" />
                    <Typography color="textSecondary" gutterBottom>
                      Verified Customers
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="success.main">
                    {summary.verifiedCustomers}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    of {summary.totalCustomers} total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ScheduleIcon color="warning" />
                    <Typography color="textSecondary" gutterBottom>
                      Pending Verification
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="warning.main">
                    {summary.pendingVerification}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    awaiting review
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SecurityIcon color="info" />
                    <Typography color="textSecondary" gutterBottom>
                      Avg Risk Score
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="info.main">
                    {summary.avgRiskScore.toFixed(1)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={summary.avgRiskScore}
                    sx={{ mt: 1 }}
                    color={summary.avgRiskScore < 40 ? 'success' : summary.avgRiskScore < 70 ? 'warning' : 'error'}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AssignmentIcon color="primary" />
                    <Typography color="textSecondary" gutterBottom>
                      Avg Processing Time
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="primary.main">
                    {summary.avgProcessingTime}h
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    end-to-end verification
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Grid container spacing={3}>
          {/* Customer Verification Table */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Customer Verification Status
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Customer</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Risk Score</TableCell>
                        <TableCell>Verification Level</TableCell>
                        <TableCell>Documents</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {customers.map((customer) => {
                        const kycResult = kycResults.find(r => r.customer_id === customer.customer_id);
                        return (
                          <TableRow key={customer.customer_id}>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Avatar sx={{ width: 32, height: 32 }}>
                                  {customer.name.charAt(0)}
                                </Avatar>
                                <Box>
                                  <Typography variant="body2" fontWeight="medium">
                                    {customer.name}
                                  </Typography>
                                  <Typography variant="caption" color="textSecondary">
                                    {customer.customer_id}
                                  </Typography>
                                </Box>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getStatusIcon(customer.verification_status)}
                                <Chip
                                  label={customer.verification_status}
                                  size="small"
                                  sx={{
                                    backgroundColor: getStatusColor(customer.verification_status),
                                    color: 'white',
                                  }}
                                />
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={customer.risk_score * 100}
                                  sx={{ 
                                    width: 60, 
                                    '& .MuiLinearProgress-bar': {
                                      backgroundColor: getRiskLevelColor(customer.risk_score)
                                    }
                                  }}
                                />
                                <Typography variant="body2">
                                  {getRiskLevel(customer.risk_score)}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={customer.verification_level}
                                size="small"
                                variant="outlined"
                                color="primary"
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {customer.documents_submitted.length} docs
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <IconButton
                                size="small"
                                onClick={() => kycResult && handleCustomerClick(kycResult)}
                              >
                                <VisibilityIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Alerts and Quick Actions */}
          <Grid item xs={12} md={4}>
            {/* KYC Alerts */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <WarningIcon />
                  <Typography variant="h6">
                    KYC Alerts
                  </Typography>
                  <Badge badgeContent={alerts.length} color="error" />
                </Box>
                <List dense>
                  {alerts.map((alert) => (
                    <ListItem
                      key={alert.alert_id}
                      button
                      onClick={() => handleAlertClick(alert)}
                      sx={{
                        border: 1,
                        borderColor: alert.severity === 'high' ? 'error.main' : 'warning.main',
                        borderRadius: 1,
                        mb: 1,
                      }}
                    >
                      <ListItemIcon>
                        {alert.severity === 'high' ? <ErrorIcon color="error" /> : <WarningIcon color="warning" />}
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
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Button variant="outlined" fullWidth startIcon={<PersonIcon />}>
                    Add New Customer
                  </Button>
                  <Button variant="outlined" fullWidth startIcon={<AssignmentIcon />}>
                    Bulk Verification
                  </Button>
                  <Button variant="outlined" fullWidth startIcon={<SecurityIcon />}>
                    Risk Assessment
                  </Button>
                  <Button variant="outlined" fullWidth startIcon={<DownloadIcon />}>
                    Export Reports
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Customer Detail Dialog */}
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            KYC Verification Details
          </DialogTitle>
          <DialogContent>
            {selectedCustomer && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Customer: {selectedCustomer.customer_id}
                </Typography>
                
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Verification Status</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(selectedCustomer.verification_status)}
                      <Typography variant="h6" sx={{ color: getStatusColor(selectedCustomer.verification_status) }}>
                        {selectedCustomer.verification_status}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Risk Score</Typography>
                    <Typography variant="h6" color={getRiskLevelColor(selectedCustomer.risk_score)}>
                      {(selectedCustomer.risk_score * 100).toFixed(1)}% ({getRiskLevel(selectedCustomer.risk_score)})
                    </Typography>
                  </Grid>
                </Grid>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>Documents Verified</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedCustomer.documents_verified.map((doc) => (
                      <Chip key={doc} label={doc.replace('_', ' ')} size="small" color="success" />
                    ))}
                  </Box>
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>Screening Results</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ p: 2 }}>
                          <Typography variant="caption" color="textSecondary">
                            Sanctions
                          </Typography>
                          <Typography variant="body2" 
                            color={selectedCustomer.sanctions_screening.status === 'clear' ? 'success.main' : 'error.main'}>
                            {selectedCustomer.sanctions_screening.status}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ p: 2 }}>
                          <Typography variant="caption" color="textSecondary">
                            PEP
                          </Typography>
                          <Typography variant="body2" 
                            color={selectedCustomer.pep_screening.status === 'clear' ? 'success.main' : 'warning.main'}>
                            {selectedCustomer.pep_screening.status}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={4}>
                      <Card variant="outlined">
                        <CardContent sx={{ p: 2 }}>
                          <Typography variant="caption" color="textSecondary">
                            Adverse Media
                          </Typography>
                          <Typography variant="body2" 
                            color={selectedCustomer.adverse_media_screening.status === 'clear' ? 'success.main' : 'warning.main'}>
                            {selectedCustomer.adverse_media_screening.status}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>Verification Process</Typography>
                  <Stepper orientation="vertical">
                    {verificationSteps.map((step, index) => (
                      <Step key={step.step} active={true} completed={step.status === 'completed'}>
                        <StepLabel 
                          icon={getStepIcon(step.status)}
                          error={step.status === 'failed'}
                        >
                          {step.step}
                        </StepLabel>
                        <StepContent>
                          <Typography variant="body2" color="textSecondary">
                            {step.description}
                          </Typography>
                          {step.details && (
                            <Typography variant="caption" color="textSecondary">
                              {step.details}
                            </Typography>
                          )}
                          {step.timestamp && (
                            <Typography variant="caption" color="textSecondary" display="block">
                              {new Date(step.timestamp).toLocaleString()}
                            </Typography>
                          )}
                        </StepContent>
                      </Step>
                    ))}
                  </Stepper>
                </Box>

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Chip 
                    label={`Recommended: ${selectedCustomer.recommended_action}`} 
                    color={selectedCustomer.recommended_action === 'approve' ? 'success' : 
                           selectedCustomer.recommended_action === 'reject' ? 'error' : 'warning'}
                  />
                  <Chip 
                    label={`Confidence: ${(selectedCustomer.confidence_score * 100).toFixed(1)}%`}
                    color="info"
                  />
                </Box>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>
              Close
            </Button>
            <Button variant="contained" color="error">
              Reject Customer
            </Button>
            <Button variant="contained" color="success">
              Approve Customer
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ErrorBoundary>
  );
};

export default KYCVerificationDashboard;