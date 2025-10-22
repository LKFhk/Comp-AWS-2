/**
 * User Preferences Component
 * Dashboard personalization and user settings
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  FormGroup,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Divider,
  Alert,
  Snackbar,
  Grid,
  Chip,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

interface UserPreferencesProps {
  onSave?: (preferences: any) => void;
}

export const UserPreferences: React.FC<UserPreferencesProps> = ({ onSave }) => {
  const { user, updateUser } = useAuth();
  const [preferences, setPreferences] = useState(user?.preferences || {});
  const [showSuccess, setShowSuccess] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handlePreferenceChange = (key: string, value: any) => {
    setPreferences((prev: any) => ({
      ...prev,
      [key]: value,
    }));
    setHasChanges(true);
  };

  const handleNotificationChange = (key: string, value: boolean) => {
    setPreferences((prev: any) => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: value,
      },
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      // Update user preferences
      updateUser({ preferences });
      
      // Call optional callback
      if (onSave) {
        onSave(preferences);
      }

      setShowSuccess(true);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };

  const handleReset = () => {
    setPreferences(user?.preferences || {});
    setHasChanges(false);
  };

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            User Preferences
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Customize your dashboard experience and notification settings
          </Typography>

          <Divider sx={{ my: 3 }} />

          {/* Theme Preferences */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Appearance
            </Typography>
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Theme</InputLabel>
              <Select
                value={preferences.theme || 'light'}
                label="Theme"
                onChange={(e) => handlePreferenceChange('theme', e.target.value)}
              >
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="auto">Auto (System)</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Notification Preferences */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Notifications
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notifications?.email || false}
                    onChange={(e) => handleNotificationChange('email', e.target.checked)}
                  />
                }
                label="Email Notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notifications?.push || false}
                    onChange={(e) => handleNotificationChange('push', e.target.checked)}
                  />
                }
                label="Push Notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notifications?.validationComplete || true}
                    onChange={(e) => handleNotificationChange('validationComplete', e.target.checked)}
                  />
                }
                label="Analysis Complete Notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notifications?.weeklyReport || false}
                    onChange={(e) => handleNotificationChange('weeklyReport', e.target.checked)}
                  />
                }
                label="Weekly Summary Report"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notifications?.fraudAlerts || true}
                    onChange={(e) => handleNotificationChange('fraudAlerts', e.target.checked)}
                  />
                }
                label="Fraud Detection Alerts"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.notifications?.complianceAlerts || true}
                    onChange={(e) => handleNotificationChange('complianceAlerts', e.target.checked)}
                  />
                }
                label="Compliance Alerts"
              />
            </FormGroup>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Dashboard Preferences */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Dashboard Settings
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Default Dashboard</InputLabel>
                  <Select
                    value={preferences.defaultDashboard || 'risk-intel'}
                    label="Default Dashboard"
                    onChange={(e) => handlePreferenceChange('defaultDashboard', e.target.value)}
                  >
                    <MenuItem value="risk-intel">Risk Intelligence</MenuItem>
                    <MenuItem value="compliance">Compliance Monitoring</MenuItem>
                    <MenuItem value="fraud">Fraud Detection</MenuItem>
                    <MenuItem value="market">Market Intelligence</MenuItem>
                    <MenuItem value="kyc">KYC Verification</MenuItem>
                    <MenuItem value="business-value">Business Value</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Refresh Interval</InputLabel>
                  <Select
                    value={preferences.refreshInterval || 30}
                    label="Refresh Interval"
                    onChange={(e) => handlePreferenceChange('refreshInterval', e.target.value)}
                  >
                    <MenuItem value={10}>10 seconds</MenuItem>
                    <MenuItem value={30}>30 seconds</MenuItem>
                    <MenuItem value={60}>1 minute</MenuItem>
                    <MenuItem value={300}>5 minutes</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <FormGroup sx={{ mt: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.compactMode || false}
                    onChange={(e) => handlePreferenceChange('compactMode', e.target.checked)}
                  />
                }
                label="Compact Mode (Show more data in less space)"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.showTutorials || true}
                    onChange={(e) => handlePreferenceChange('showTutorials', e.target.checked)}
                  />
                }
                label="Show Tutorials and Tooltips"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences.enableAnimations || true}
                    onChange={(e) => handlePreferenceChange('enableAnimations', e.target.checked)}
                  />
                }
                label="Enable Animations"
              />
            </FormGroup>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Analysis Preferences */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Analysis Settings
            </Typography>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Default Priority</InputLabel>
              <Select
                value={preferences.defaultPriority || 'medium'}
                label="Default Priority"
                onChange={(e) => handlePreferenceChange('defaultPriority', e.target.value)}
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
              </Select>
            </FormControl>

            <Typography variant="body2" gutterBottom>
              Default Analysis Scope:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
              {['regulatory', 'fraud', 'market', 'kyc', 'risk'].map((scope) => (
                <Chip
                  key={scope}
                  label={scope.charAt(0).toUpperCase() + scope.slice(1)}
                  onClick={() => {
                    const currentScope = preferences.defaultAnalysisScope || [];
                    const newScope = currentScope.includes(scope)
                      ? currentScope.filter((s: string) => s !== scope)
                      : [...currentScope, scope];
                    handlePreferenceChange('defaultAnalysisScope', newScope);
                  }}
                  color={preferences.defaultAnalysisScope?.includes(scope) ? 'primary' : 'default'}
                  variant={preferences.defaultAnalysisScope?.includes(scope) ? 'filled' : 'outlined'}
                />
              ))}
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Regional Settings */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Regional Settings
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={preferences.language || 'en'}
                    label="Language"
                    onChange={(e) => handlePreferenceChange('language', e.target.value)}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Español</MenuItem>
                    <MenuItem value="fr">Français</MenuItem>
                    <MenuItem value="de">Deutsch</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={preferences.timezone || 'UTC'}
                    label="Timezone"
                    onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                  >
                    <MenuItem value="UTC">UTC</MenuItem>
                    <MenuItem value="America/New_York">Eastern Time</MenuItem>
                    <MenuItem value="America/Chicago">Central Time</MenuItem>
                    <MenuItem value="America/Denver">Mountain Time</MenuItem>
                    <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                    <MenuItem value="Europe/London">London</MenuItem>
                    <MenuItem value="Europe/Paris">Paris</MenuItem>
                    <MenuItem value="Asia/Tokyo">Tokyo</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 4 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleReset}
              disabled={!hasChanges}
            >
              Reset
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={!hasChanges}
            >
              Save Preferences
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Snackbar
        open={showSuccess}
        autoHideDuration={3000}
        onClose={() => setShowSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setShowSuccess(false)}>
          Preferences saved successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
};
