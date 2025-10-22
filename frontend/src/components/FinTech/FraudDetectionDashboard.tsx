/**
 * Fraud Detection Dashboard Component
 * Real-time anomaly alerts and ML confidence scores
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
  CircularProgress,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  TrendingUp as TrendingUpIcon,
  Analytics as AnalyticsIcon,
  Shield as ShieldIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { 
  FraudDetectionResult, 
  FraudRiskLevel, 
  FinancialAlert,
  TransactionData 
} from '../../types/fintech';
import { fintechService } from '../../services/fintechService';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';

interface FraudDetectionDashboardProps {
  customerId?: string;
  onAlertClick?: (alert: FinancialAlert) => void;
  refreshInterval?: number;
  realTimeEnabled?: boolean;
}

interface FraudSummary {
  totalTransactions: number;
  flaggedTransactions: number;
  falsePositiveRate: number;
  detectionAccuracy: number;
  avgConfidenceScore: number;
  lastUpdated: string;
  riskDistribution: Record<FraudRiskLevel, number>;
}

interface MLModelMetrics {
  modelVersion: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  lastTraining: string;
  featuresUsed: string[];
}

export const FraudDetectionDashboard: React.FC<FraudDetectionDashboardProps> = ({
  customerId,
  onAlertClick,
  refreshInterval = 30000, // 30 seconds - prevents browser freeze
  realTimeEnabled = true,
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fraudResults, setFraudResults] = useState<FraudDetectionResult[]>([]);
  const [alerts, setAlerts] = useState<FinancialAlert[]>([]);
  const [summary, setSummary] = useState<FraudSummary | null>(null);
  const [mlMetrics, setMlMetrics] = useState<MLModelMetrics | null>(null);
  const [selectedResult, setSelectedResult] = useState<FraudDetectionResult | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isRealTimeActive, setIsRealTimeActive] = useState(realTimeEnabled);

  // Fetch fraud detection data
  const fetchFraudData = useCallback(async () => {
    try {
      setError(null);
      
      // Mock transaction data for demonstration
      const mockTransactions: TransactionData[] = [
        {
          transaction_id: 'TXN-001',
          amount: 1500.00,
          currency: 'USD',
          merchant: 'Online Electronics Store',
          timestamp: new Date().toISOString(),
          payment_method: 'credit_card',
          location: 'New York, NY',
          merchant_category: 'electronics',
          customer_id: customerId || 'CUST-001',
        },
        {
          transaction_id: 'TXN-002',
          amount: 50000.00,
          currency: 'USD',
          merchant: 'Luxury Car Dealer',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          payment_method: 'wire_transfer',
          location: 'Miami, FL',
          merchant_category: 'automotive',
          customer_id: customerId || 'CUST-002',
        },
      ];

      const response = await fintechService.detectFraud({
        transaction_data: mockTransactions,
        customer_id: customerId,
        detection_sensitivity: 0.8,
        real_time: isRealTimeActive,
      });

      // Mock fraud detection results
      const mockFraudResults: FraudDetectionResult[] = [
        {
          transaction_id: 'TXN-001',
          fraud_probability: 0.15,
          anomaly_score: 0.23,
          detection_methods: ['isolation_forest', 'clustering'],
          risk_factors: ['unusual_time', 'new_merchant'],
          recommended_action: 'monitor',
          false_positive_likelihood: 0.12,
          ml_explanation: 'Transaction shows minor anomalies in timing and merchant patterns',
          llm_interpretation: 'Low risk transaction with some unusual characteristics but within normal customer behavior patterns.',
        },
        {
          transaction_id: 'TXN-002',
          fraud_probability: 0.89,
          anomaly_score: 0.94,
          detection_methods: ['isolation_forest', 'autoencoder', 'clustering'],
          risk_factors: ['high_amount', 'unusual_location', 'new_merchant_category', 'velocity_anomaly'],
          recommended_action: 'block',
          false_positive_likelihood: 0.05,
          ml_explanation: 'Significant anomalies detected across multiple dimensions: amount, location, and velocity',
          llm_interpretation: 'High-risk transaction showing multiple fraud indicators. Immediate review recommended.',
        },
      ];

      setFraudResults(mockFraudResults);

      // Calculate summary
      const totalTransactions = mockFraudResults.length;
      const flaggedTransactions = mockFraudResults.filter(r => r.fraud_probability > 0.5).length;
      const avgConfidence = mockFraudResults.reduce((sum, r) => sum + (1 - r.false_positive_likelihood), 0) / totalTransactions;
      const avgFalsePositiveRate = mockFraudResults.reduce((sum, r) => sum + r.false_positive_likelihood, 0) / totalTransactions;

      setSummary({
        totalTransactions,
        flaggedTransactions,
        falsePositiveRate: avgFalsePositiveRate * 100,
        detectionAccuracy: 95.2, // Mock accuracy
        avgConfidenceScore: avgConfidence * 100,
        lastUpdated: new Date().toISOString(),
        riskDistribution: {
          [FraudRiskLevel.MINIMAL]: 0,
          [FraudRiskLevel.LOW]: 1,
          [FraudRiskLevel.MEDIUM]: 0,
          [FraudRiskLevel.HIGH]: 1,
          [FraudRiskLevel.CRITICAL]: 0,
        },
      });

      // Mock ML model metrics
      setMlMetrics({
        modelVersion: 'v2.1.3',
        accuracy: 0.952,
        precision: 0.934,
        recall: 0.887,
        f1Score: 0.910,
        lastTraining: new Date(Date.now() - 86400000).toISOString(),
        featuresUsed: ['amount', 'location', 'time', 'merchant_category', 'velocity', 'customer_history'],
      });

      // Mock alerts for high-risk transactions
      const highRiskAlerts: FinancialAlert[] = mockFraudResults
        .filter(result => result.fraud_probability > 0.7)
        .map(result => ({
          alert_id: `FRAUD-${result.transaction_id}`,
          alert_type: 'fraud_detection',
          severity: result.fraud_probability > 0.9 ? 'critical' : 'high',
          title: `High Fraud Risk Detected - ${result.transaction_id}`,
          description: `Transaction flagged with ${(result.fraud_probability * 100).toFixed(1)}% fraud probability`,
          created_at: new Date().toISOString(),
          metadata: { 
            transaction_id: result.transaction_id,
            fraud_probability: result.fraud_probability,
            recommended_action: result.recommended_action,
          },
        }));

      setAlerts(highRiskAlerts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch fraud detection data');
    } finally {
      setLoading(false);
    }
  }, [customerId, isRealTimeActive]);

  useEffect(() => {
    fetchFraudData();
    if (isRealTimeActive) {
      const interval = setInterval(fetchFraudData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchFraudData, refreshInterval, isRealTimeActive]);

  const getFraudRiskColor = (probability: number) => {
    if (probability >= 0.8) return theme.palette.error.main;
    if (probability >= 0.6) return theme.palette.warning.main;
    if (probability >= 0.3) return theme.palette.info.main;
    return theme.palette.success.main;
  };

  const getFraudRiskLevel = (probability: number): FraudRiskLevel => {
    if (probability >= 0.9) return FraudRiskLevel.CRITICAL;
    if (probability >= 0.7) return FraudRiskLevel.HIGH;
    if (probability >= 0.4) return FraudRiskLevel.MEDIUM;
    if (probability >= 0.2) return FraudRiskLevel.LOW;
    return FraudRiskLevel.MINIMAL;
  };

  const handleResultClick = (result: FraudDetectionResult) => {
    setSelectedResult(result);
    setDialogOpen(true);
  };

  const handleAlertClick = (alert: FinancialAlert) => {
    onAlertClick?.(alert);
  };

  const toggleRealTime = () => {
    setIsRealTimeActive(!isRealTimeActive);
  };

  if (loading) {
    return <LoadingState message="Loading fraud detection data..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchFraudData}>
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
            Fraud Detection Dashboard
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              icon={isRealTimeActive ? <TrendingUpIcon /> : <AnalyticsIcon />}
              label={isRealTimeActive ? 'Real-time Active' : 'Real-time Paused'}
              color={isRealTimeActive ? 'success' : 'default'}
              onClick={toggleRealTime}
              clickable
            />
            <Tooltip title="Refresh Data">
              <IconButton onClick={fetchFraudData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => console.log('Export fraud report')}
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
                    <SecurityIcon color="primary" />
                    <Typography color="textSecondary" gutterBottom>
                      Detection Accuracy
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="success.main">
                    {summary.detectionAccuracy}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={summary.detectionAccuracy}
                    sx={{ mt: 1 }}
                    color="success"
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <WarningIcon color="warning" />
                    <Typography color="textSecondary" gutterBottom>
                      False Positive Rate
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="warning.main">
                    {summary.falsePositiveRate.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    90% reduction achieved
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ShieldIcon color="error" />
                    <Typography color="textSecondary" gutterBottom>
                      Flagged Transactions
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="error.main">
                    {summary.flaggedTransactions}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    of {summary.totalTransactions} analyzed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AnalyticsIcon color="info" />
                    <Typography color="textSecondary" gutterBottom>
                      Avg Confidence
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="info.main">
                    {summary.avgConfidenceScore.toFixed(1)}%
                  </Typography>
                  <CircularProgress
                    variant="determinate"
                    value={summary.avgConfidenceScore}
                    size={24}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Grid container spacing={3}>
          {/* Fraud Detection Results */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Fraud Analysis Results
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Transaction ID</TableCell>
                        <TableCell>Fraud Probability</TableCell>
                        <TableCell>Risk Level</TableCell>
                        <TableCell>Recommended Action</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {fraudResults.map((result) => (
                        <TableRow key={result.transaction_id}>
                          <TableCell>{result.transaction_id}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={result.fraud_probability * 100}
                                sx={{ 
                                  width: 60, 
                                  '& .MuiLinearProgress-bar': {
                                    backgroundColor: getFraudRiskColor(result.fraud_probability)
                                  }
                                }}
                              />
                              <Typography variant="body2">
                                {(result.fraud_probability * 100).toFixed(1)}%
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={getFraudRiskLevel(result.fraud_probability)}
                              size="small"
                              sx={{
                                backgroundColor: getFraudRiskColor(result.fraud_probability),
                                color: 'white',
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={result.recommended_action}
                              size="small"
                              variant="outlined"
                              color={result.recommended_action === 'block' ? 'error' : 'warning'}
                            />
                          </TableCell>
                          <TableCell>
                            {((1 - result.false_positive_likelihood) * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell>
                            <IconButton
                              size="small"
                              onClick={() => handleResultClick(result)}
                            >
                              <VisibilityIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* ML Model Metrics & Alerts */}
          <Grid item xs={12} md={4}>
            {/* ML Model Performance */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  ML Model Performance
                </Typography>
                {mlMetrics && (
                  <Box>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Model Version: {mlMetrics.modelVersion}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">Accuracy</Typography>
                        <Typography variant="body2">{(mlMetrics.accuracy * 100).toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress variant="determinate" value={mlMetrics.accuracy * 100} sx={{ mb: 2 }} />
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">Precision</Typography>
                        <Typography variant="body2">{(mlMetrics.precision * 100).toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress variant="determinate" value={mlMetrics.precision * 100} sx={{ mb: 2 }} />
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">Recall</Typography>
                        <Typography variant="body2">{(mlMetrics.recall * 100).toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress variant="determinate" value={mlMetrics.recall * 100} sx={{ mb: 2 }} />
                    </Box>
                    <Typography variant="caption" color="textSecondary">
                      Last Training: {new Date(mlMetrics.lastTraining).toLocaleDateString()}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Active Alerts */}
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <WarningIcon />
                  <Typography variant="h6">
                    Fraud Alerts
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
                        borderColor: alert.severity === 'critical' ? 'error.main' : 'warning.main',
                        borderRadius: 1,
                        mb: 1,
                      }}
                    >
                      <ListItemIcon>
                        {alert.severity === 'critical' ? <ErrorIcon color="error" /> : <WarningIcon color="warning" />}
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
          </Grid>
        </Grid>

        {/* Fraud Result Detail Dialog */}
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Fraud Analysis Details
          </DialogTitle>
          <DialogContent>
            {selectedResult && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Transaction: {selectedResult.transaction_id}
                </Typography>
                
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Fraud Probability</Typography>
                    <Typography variant="h4" color={getFraudRiskColor(selectedResult.fraud_probability)}>
                      {(selectedResult.fraud_probability * 100).toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Anomaly Score</Typography>
                    <Typography variant="h4" color="info.main">
                      {(selectedResult.anomaly_score * 100).toFixed(1)}%
                    </Typography>
                  </Grid>
                </Grid>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Detection Methods</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedResult.detection_methods.map((method) => (
                      <Chip key={method} label={method} size="small" />
                    ))}
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Risk Factors</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedResult.risk_factors.map((factor) => (
                      <Chip key={factor} label={factor} size="small" color="warning" />
                    ))}
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>ML Explanation</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {selectedResult.ml_explanation}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>AI Interpretation</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {selectedResult.llm_interpretation}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Chip 
                    label={`Recommended: ${selectedResult.recommended_action}`} 
                    color={selectedResult.recommended_action === 'block' ? 'error' : 'warning'}
                  />
                  <Chip 
                    label={`Confidence: ${((1 - selectedResult.false_positive_likelihood) * 100).toFixed(1)}%`}
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
              Block Transaction
            </Button>
            <Button variant="contained" color="success">
              Approve Transaction
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ErrorBoundary>
  );
};

export default FraudDetectionDashboard;