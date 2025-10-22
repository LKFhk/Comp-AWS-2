import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  Grid,
  Switch,
  FormControlLabel,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Paper,
} from '@mui/material';
import {
  Save as SaveIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  MonetizationOn as MoneyIcon,
  Speed as SpeedIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { credentialsService, BudgetLimits, BudgetUsage } from '../../../services/credentialsService';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../../components/Common/LoadingSpinner';

const BudgetManagement: React.FC = () => {
  const [budgetLimits, setBudgetLimits] = useState<BudgetLimits>({
    max_daily_spend: 10.0,
    max_monthly_spend: 100.0,
    max_per_validation: 5.0,
    alert_threshold_percent: 80.0,
    auto_throttle_enabled: true,
  });
  const [budgetUsage, setBudgetUsage] = useState<BudgetUsage | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const { showNotification } = useNotification();

  useEffect(() => {
    loadBudgetUsage();
  }, []);

  const loadBudgetUsage = async () => {
    try {
      setLoading(true);
      setError('');
      
      const usage = await credentialsService.getCurrentBudgetUsage();
      setBudgetUsage(usage);
      
      // If limits exist, update the form
      if (usage.limits) {
        setBudgetLimits(usage.limits);
      }
      
    } catch (err: any) {
      console.error('Failed to load budget usage:', err);
      setError('Failed to load budget information');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof BudgetLimits) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'auto_throttle_enabled' 
      ? event.target.checked 
      : parseFloat(event.target.value) || 0;
    
    setBudgetLimits({
      ...budgetLimits,
      [field]: value,
    });
    setError('');
    setSuccess('');
  };

  const handleSaveBudgetLimits = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      // Client-side validation
      const validationErrors = credentialsService.validateBudgetLimits(budgetLimits);
      if (validationErrors.length > 0) {
        setError(validationErrors.join(', '));
        return;
      }

      await credentialsService.setBudgetLimits(budgetLimits);
      setSuccess('Budget limits saved successfully!');
      showNotification('Budget limits updated', 'success');
      
      // Reload usage data
      await loadBudgetUsage();
      
    } catch (err: any) {
      console.error('Failed to save budget limits:', err);
      setError(err.message || 'Failed to save budget limits');
    } finally {
      setSaving(false);
    }
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'error';
    if (percentage >= 75) return 'warning';
    return 'success';
  };

  const getAlertSeverity = (severity: string) => {
    switch (severity) {
      case 'error': return 'error' as const;
      case 'warning': return 'warning' as const;
      default: return 'info' as const;
    }
  };

  if (loading) {
    return <LoadingSpinner size={60} message="Loading budget information..." />;
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Budget Management
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Set spending limits and configure alerts to control your AWS costs.
        Budget guardrails help prevent unexpected charges and optimize spending.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Current Usage */}
        {budgetUsage && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Usage
                </Typography>

                <Grid container spacing={3}>
                  {/* Daily Usage */}
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2 }}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">Daily Usage</Typography>
                        <MoneyIcon color="primary" />
                      </Box>
                      <Typography variant="h5" color="primary">
                        {credentialsService.formatCurrency(budgetUsage.usage.daily)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        of {budgetUsage.limits ? credentialsService.formatCurrency(budgetUsage.limits.max_daily_spend) : 'N/A'} limit
                      </Typography>
                      {budgetUsage.limits && (
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(budgetUsage.usage_percentages.daily, 100)}
                          color={getUsageColor(budgetUsage.usage_percentages.daily)}
                          sx={{ mt: 1, height: 8, borderRadius: 4 }}
                        />
                      )}
                    </Paper>
                  </Grid>

                  {/* Monthly Usage */}
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2 }}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">Monthly Usage</Typography>
                        <TrendingUpIcon color="primary" />
                      </Box>
                      <Typography variant="h5" color="primary">
                        {credentialsService.formatCurrency(budgetUsage.usage.monthly)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        of {budgetUsage.limits ? credentialsService.formatCurrency(budgetUsage.limits.max_monthly_spend) : 'N/A'} limit
                      </Typography>
                      {budgetUsage.limits && (
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(budgetUsage.usage_percentages.monthly, 100)}
                          color={getUsageColor(budgetUsage.usage_percentages.monthly)}
                          sx={{ mt: 1, height: 8, borderRadius: 4 }}
                        />
                      )}
                    </Paper>
                  </Grid>

                  {/* Validations Count */}
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2 }}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">Validations</Typography>
                        <SpeedIcon color="primary" />
                      </Box>
                      <Typography variant="h5" color="primary">
                        {budgetUsage.usage.validations_today}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        today ({budgetUsage.usage.validations_this_month} this month)
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                {/* Alerts */}
                {budgetUsage.alerts && budgetUsage.alerts.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Active Alerts
                    </Typography>
                    {budgetUsage.alerts.map((alert, index) => (
                      <Alert
                        key={index}
                        severity={getAlertSeverity(alert.severity)}
                        sx={{ mb: 1 }}
                      >
                        {alert.message}
                      </Alert>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Budget Limits Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Budget Limits
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Maximum Daily Spend"
                    type="number"
                    value={budgetLimits.max_daily_spend}
                    onChange={handleInputChange('max_daily_spend')}
                    InputProps={{
                      startAdornment: '$',
                    }}
                    helperText="Maximum amount to spend per day on financial risk analysis"
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Maximum Monthly Spend"
                    type="number"
                    value={budgetLimits.max_monthly_spend}
                    onChange={handleInputChange('max_monthly_spend')}
                    InputProps={{
                      startAdornment: '$',
                    }}
                    helperText="Maximum amount to spend per month on financial risk analysis"
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Maximum Per Validation"
                    type="number"
                    value={budgetLimits.max_per_validation}
                    onChange={handleInputChange('max_per_validation')}
                    InputProps={{
                      startAdornment: '$',
                    }}
                    helperText="Maximum cost allowed for a single validation"
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Alert Threshold"
                    type="number"
                    value={budgetLimits.alert_threshold_percent}
                    onChange={handleInputChange('alert_threshold_percent')}
                    InputProps={{
                      endAdornment: '%',
                    }}
                    helperText="Send alerts when usage reaches this percentage"
                    inputProps={{ min: 0, max: 100, step: 1 }}
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={budgetLimits.auto_throttle_enabled}
                        onChange={handleInputChange('auto_throttle_enabled')}
                      />
                    }
                    label="Enable Auto-Throttling"
                  />
                  <Typography variant="body2" color="text.secondary">
                    Automatically reduce service usage when approaching limits
                  </Typography>
                </Grid>
              </Grid>

              <Box sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  startIcon={saving ? <LoadingSpinner size={20} /> : <SaveIcon />}
                  onClick={handleSaveBudgetLimits}
                  disabled={saving}
                  fullWidth
                >
                  {saving ? 'Saving...' : 'Save Budget Limits'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Budget Recommendations */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Budget Recommendations
              </Typography>

              <List>
                <ListItem>
                  <ListItemIcon>
                    <NotificationsIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Start with Conservative Limits"
                    secondary="Begin with lower limits and increase as you understand your usage patterns"
                  />
                </ListItem>

                <ListItem>
                  <ListItemIcon>
                    <TrendingUpIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Monitor Usage Trends"
                    secondary="Review your spending patterns weekly to optimize budget allocation"
                  />
                </ListItem>

                <ListItem>
                  <ListItemIcon>
                    <WarningIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Set Alert Thresholds"
                    secondary="Configure alerts at 75-80% to avoid hitting hard limits unexpectedly"
                  />
                </ListItem>

                <ListItem>
                  <ListItemIcon>
                    <SpeedIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Use Demo Profile for Testing"
                    secondary="Switch to demo profile for testing to minimize costs (60% savings)"
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Suggested Budget Ranges:
              </Typography>
              
              <Box display="flex" flexWrap="wrap" gap={1}>
                <Chip
                  label="Demo: $5-20/month"
                  color="success"
                  variant="outlined"
                  size="small"
                />
                <Chip
                  label="Development: $25-100/month"
                  color="primary"
                  variant="outlined"
                  size="small"
                />
                <Chip
                  label="Production: $100-500/month"
                  color="warning"
                  variant="outlined"
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Information */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>Budget Guardrails:</strong> These limits help prevent unexpected AWS charges.
          When limits are reached, new validation requests may be blocked or throttled.
          You can always adjust limits based on your needs and usage patterns.
        </Typography>
      </Alert>
    </Box>
  );
};

export default BudgetManagement;