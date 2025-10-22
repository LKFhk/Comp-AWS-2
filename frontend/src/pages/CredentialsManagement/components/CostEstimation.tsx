import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  Calculate as CalculateIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  MonetizationOn as MoneyIcon,
} from '@mui/icons-material';
import { credentialsService, CostEstimationRequest } from '../../../services/credentialsService';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../../components/Common/LoadingSpinner';

const CostEstimation: React.FC = () => {
  const [request, setRequest] = useState<CostEstimationRequest>({
    profile: 'development',
    business_concept: '',
    analysis_scope: ['market', 'competitive', 'financial'],
    target_market: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [estimation, setEstimation] = useState<any>(null);

  const { showNotification } = useNotification();

  const costProfiles = [
    {
      value: 'demo',
      label: 'Demo Profile',
      description: 'Optimized for testing with minimal costs (~60% savings)',
      color: 'success' as const,
    },
    {
      value: 'development',
      label: 'Development Profile',
      description: 'Balanced performance and cost (~20% savings)',
      color: 'primary' as const,
    },
    {
      value: 'production',
      label: 'Production Profile',
      description: 'Maximum performance for production workloads',
      color: 'warning' as const,
    },
  ];

  const analysisOptions = [
    { id: 'regulatory', label: 'Regulatory Compliance', description: 'Compliance monitoring and regulatory analysis' },
    { id: 'fraud', label: 'Fraud Detection', description: 'ML-powered fraud pattern detection' },
    { id: 'risk', label: 'Risk Assessment', description: 'Financial risk evaluation and mitigation' },
    { id: 'market', label: 'Market Analysis', description: 'Financial market intelligence and trends' },
    { id: 'kyc', label: 'KYC Verification', description: 'Customer verification and risk scoring' },
  ];

  const sampleBusinessConcepts = [
    'FinTech startup - Payment processing platform',
    'Regional bank - Digital banking transformation',
    'Cryptocurrency exchange - Trading platform',
    'P2P lending platform - Credit marketplace',
    'InsurTech - AI-powered underwriting platform',
  ];

  const sampleTargetMarkets = [
    'US - SEC/FINRA regulated',
    'EU - MiFID II compliant',
    'APAC - Multi-jurisdiction digital banking',
    'Global - Cross-border payment services',
    'US - State-level money transmitter licenses',
  ];

  const handleInputChange = (field: keyof CostEstimationRequest) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRequest({
      ...request,
      [field]: event.target.value,
    });
    setError('');
  };

  const handleProfileChange = (event: any) => {
    setRequest({
      ...request,
      profile: event.target.value,
    });
  };

  const handleAnalysisScopeChange = (optionId: string, checked: boolean) => {
    if (checked) {
      setRequest({
        ...request,
        analysis_scope: [...request.analysis_scope, optionId],
      });
    } else {
      setRequest({
        ...request,
        analysis_scope: request.analysis_scope.filter(id => id !== optionId),
      });
    }
  };

  const handleEstimateCost = async () => {
    try {
      setLoading(true);
      setError('');

      if (!request.business_concept || !request.target_market) {
        setError('Please fill in all required fields');
        return;
      }

      if (request.analysis_scope.length === 0) {
        setError('Please select at least one analysis scope');
        return;
      }

      const result = await credentialsService.estimateValidationCost(request);
      setEstimation(result);
      showNotification('Cost estimation completed', 'success');
    } catch (err: any) {
      console.error('Failed to estimate cost:', err);
      setError(err.message || 'Failed to estimate cost');
    } finally {
      setLoading(false);
    }
  };

  const fillSampleData = () => {
    setRequest({
      profile: 'development',
      business_concept: sampleBusinessConcepts[0],
      analysis_scope: ['regulatory', 'fraud', 'risk'],
      target_market: sampleTargetMarkets[0],
    });
  };

  const getProfileInfo = (profileValue: string) => {
    return costProfiles.find(p => p.value === profileValue);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        AWS Cost Estimation
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Estimate the AWS costs for running a validation request with different configurations.
        This helps you plan your budget and choose the right cost profile.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Input Form */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Validation Parameters
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={fillSampleData}
                >
                  Fill Sample Data
                </Button>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Cost Profile</InputLabel>
                    <Select
                      value={request.profile}
                      label="Cost Profile"
                      onChange={handleProfileChange}
                    >
                      {costProfiles.map((profile) => (
                        <MenuItem key={profile.value} value={profile.value}>
                          <Box>
                            <Typography variant="body1">{profile.label}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {profile.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  {getProfileInfo(request.profile) && (
                    <Chip
                      label={getProfileInfo(request.profile)!.label}
                      color={getProfileInfo(request.profile)!.color}
                      size="small"
                      sx={{ mt: 1 }}
                    />
                  )}
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Financial Institution Profile"
                    value={request.business_concept}
                    onChange={handleInputChange('business_concept')}
                    placeholder="Describe your financial institution..."
                    multiline
                    rows={3}
                    required
                    helperText="Brief description of your financial institution, fintech platform, or banking operation"
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Regulatory Jurisdiction"
                    value={request.target_market}
                    onChange={handleInputChange('target_market')}
                    placeholder="Specify regulatory jurisdiction..."
                    required
                    helperText="Primary regulatory jurisdiction (e.g., US SEC/FINRA, EU MiFID II, APAC regulations)"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Analysis Scope
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Select which analysis areas to include:
                  </Typography>
                  
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {analysisOptions.map((option) => (
                      <Chip
                        key={option.id}
                        label={option.label}
                        color={request.analysis_scope.includes(option.id) ? 'primary' : 'default'}
                        variant={request.analysis_scope.includes(option.id) ? 'filled' : 'outlined'}
                        onClick={() => handleAnalysisScopeChange(
                          option.id,
                          !request.analysis_scope.includes(option.id)
                        )}
                        clickable
                      />
                    ))}
                  </Box>
                </Grid>
              </Grid>

              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  startIcon={loading ? <LoadingSpinner size={20} /> : <CalculateIcon />}
                  onClick={handleEstimateCost}
                  disabled={loading}
                  fullWidth
                >
                  {loading ? 'Calculating...' : 'Estimate Cost'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Results */}
        <Grid item xs={12} md={6}>
          {estimation ? (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Cost Estimation Results
                </Typography>

                {/* Total Cost */}
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography variant="h4">
                        {credentialsService.formatCurrency(estimation.estimate.total_cost_usd)}
                      </Typography>
                      <Typography variant="body2">
                        Estimated Total Cost
                      </Typography>
                    </Box>
                    <MoneyIcon fontSize="large" />
                  </Box>
                </Paper>

                {/* Duration */}
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography variant="h5">
                        ~{estimation.estimate.estimated_duration_minutes} min
                      </Typography>
                      <Typography variant="body2">
                        Estimated Duration
                      </Typography>
                    </Box>
                    <SpeedIcon fontSize="large" />
                  </Box>
                </Paper>

                {/* Cost Breakdown */}
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                  Cost Breakdown
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="Amazon Bedrock (AI Models)"
                      secondary={`${credentialsService.formatCurrency(estimation.estimate.bedrock_cost)} - Fraud detection & compliance analysis`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Compute (ECS Fargate)"
                      secondary={`${credentialsService.formatCurrency(estimation.estimate.compute_cost)} - Risk assessment processing`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Storage (Aurora/DynamoDB)"
                      secondary={`${credentialsService.formatCurrency(estimation.estimate.storage_cost)} - Transaction & compliance data`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Data Transfer"
                      secondary={`${credentialsService.formatCurrency(estimation.estimate.data_transfer_cost)} - Regulatory data integration`}
                    />
                  </ListItem>
                </List>

                <Divider sx={{ my: 2 }} />

                {/* Profile Used */}
                <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Profile Used:
                  </Typography>
                  <Chip
                    label={estimation.profile_used}
                    color={getProfileInfo(estimation.profile_used)?.color || 'default'}
                    size="small"
                  />
                </Box>

                {/* Confidence Score */}
                <Box sx={{ mb: 2 }}>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Confidence Score:
                    </Typography>
                    <Typography variant="body2">
                      {Math.round(estimation.estimate.confidence_score * 100)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={estimation.estimate.confidence_score * 100}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                {/* Recommendations */}
                {estimation.recommendations && estimation.recommendations.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Cost Optimization Recommendations:
                    </Typography>
                    <List dense>
                      {estimation.recommendations.map((rec: string, index: number) => (
                        <ListItem key={index}>
                          <ListItemText
                            primary={rec}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent>
                <Box
                  display="flex"
                  flexDirection="column"
                  alignItems="center"
                  justifyContent="center"
                  minHeight={300}
                  color="text.secondary"
                >
                  <TrendingUpIcon fontSize="large" sx={{ mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Cost Estimation
                  </Typography>
                  <Typography variant="body2" textAlign="center">
                    Fill in the validation parameters and click "Estimate Cost" to see
                    the projected AWS costs for your validation request.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Information */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>Note:</strong> Cost estimates are based on current AWS pricing and typical usage patterns.
          Actual costs may vary depending on specific usage, data complexity, and AWS pricing changes.
          The estimates include a confidence score to indicate reliability.
        </Typography>
      </Alert>
    </Box>
  );
};

export default CostEstimation;