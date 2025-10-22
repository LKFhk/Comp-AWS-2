import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  Divider,
  Avatar,
  IconButton,
} from '@mui/material';
import {
  Save as SaveIcon,
  Edit as EditIcon,
  Notifications as NotificationsIcon,
  Palette as PaletteIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNotification } from '../../contexts/NotificationContext';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';

interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    email: boolean;
    push: boolean;
    validationComplete: boolean;
    weeklyReport: boolean;
  };
  defaultAnalysisScope: string[];
  defaultPriority: 'low' | 'medium' | 'high';
  language: string;
  timezone: string;
}

const Settings: React.FC = () => {
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: 'light',
    notifications: {
      email: true,
      push: true,
      validationComplete: true,
      weeklyReport: false,
    },
    defaultAnalysisScope: ['market', 'competitive', 'financial', 'risk', 'customer'],
    defaultPriority: 'medium',
    language: 'en',
    timezone: 'UTC',
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const { user, updateUser } = useAuth();
  const { showNotification } = useNotification();

  const analysisOptions = [
    { id: 'market', label: 'Market Research' },
    { id: 'competitive', label: 'Competitive Intelligence' },
    { id: 'financial', label: 'Financial Validation' },
    { id: 'risk', label: 'Risk Assessment' },
    { id: 'customer', label: 'Customer Intelligence' },
  ];

  const loadUserPreferences = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      // Load user preferences from API
      const userPrefs = await apiService.getUserPreferences();
      setPreferences(prevPrefs => ({ ...prevPrefs, ...userPrefs }));
      
    } catch (err: any) {
      console.error('Failed to load user preferences:', err);
      // Use default preferences if loading fails
      setError('Failed to load preferences. Using defaults.');
    } finally {
      setLoading(false);
    }
  }, []); // Remove preferences dependency to prevent infinite loop

  useEffect(() => {
    loadUserPreferences();
  }, []); // Only load once on mount

  const handleSavePreferences = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');
      
      // Save preferences to API
      await apiService.updateUserPreferences(preferences);
      
      // Update user context with new preferences
      updateUser({ preferences });
      
      setSuccess('Financial risk intelligence platform preferences saved successfully!');
      showNotification('Platform settings saved successfully', 'success');
      
    } catch (err: any) {
      console.error('Failed to save preferences:', err);
      setError('Failed to save platform preferences. Please try again.');
      showNotification('Failed to save platform settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleAnalysisScopeChange = (optionId: string, checked: boolean) => {
    if (checked) {
      setPreferences({
        ...preferences,
        defaultAnalysisScope: [...preferences.defaultAnalysisScope, optionId],
      });
    } else {
      setPreferences({
        ...preferences,
        defaultAnalysisScope: preferences.defaultAnalysisScope.filter(id => id !== optionId),
      });
    }
  };

  const handleNotificationChange = (key: keyof UserPreferences['notifications'], value: boolean) => {
    setPreferences({
      ...preferences,
      notifications: {
        ...preferences.notifications,
        [key]: value,
      },
    });
  };

  if (loading) {
    return <LoadingSpinner size={60} message="Loading platform settings..." />;
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" mb={4}>
        Customize your RiskIntel360 experience and preferences
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
        {/* Profile Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={3}>
                <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </Avatar>
                <Box>
                  <Typography variant="h6">{user?.name || 'User'}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {user?.email || 'user@example.com'}
                  </Typography>
                </Box>
                <IconButton sx={{ ml: 'auto' }}>
                  <EditIcon />
                </IconButton>
              </Box>
              
              <Divider sx={{ mb: 3 }} />
              
              <Typography variant="h6" gutterBottom>
                <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Account Information
              </Typography>
              
              <TextField
                fullWidth
                label="Full Name"
                value={user?.name || ''}
                margin="normal"
                disabled
                helperText="Contact RiskIntel360 support to update your account name"
              />
              
              <TextField
                fullWidth
                label="Email Address"
                value={user?.email || ''}
                margin="normal"
                disabled
                helperText="Contact RiskIntel360 support to update your email address"
              />
              
              <TextField
                fullWidth
                label="Role"
                value={user?.role || 'analyst'}
                margin="normal"
                disabled
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Appearance Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <PaletteIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Appearance & Language
              </Typography>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Theme</InputLabel>
                <Select
                  value={preferences.theme}
                  label="Theme"
                  onChange={(e) => setPreferences({ ...preferences, theme: e.target.value as any })}
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="auto">Auto (System)</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Language</InputLabel>
                <Select
                  value={preferences.language}
                  label="Language"
                  onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="de">German</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={preferences.timezone}
                  label="Timezone"
                  onChange={(e) => setPreferences({ ...preferences, timezone: e.target.value })}
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
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <NotificationsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Notification Preferences
              </Typography>
              
              <Box display="flex" flexDirection="column" gap={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.email}
                      onChange={(e) => handleNotificationChange('email', e.target.checked)}
                    />
                  }
                  label="Email Notifications"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.push}
                      onChange={(e) => handleNotificationChange('push', e.target.checked)}
                    />
                  }
                  label="Push Notifications"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.validationComplete}
                      onChange={(e) => handleNotificationChange('validationComplete', e.target.checked)}
                    />
                  }
                  label="Validation Completion Alerts"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.weeklyReport}
                      onChange={(e) => handleNotificationChange('weeklyReport', e.target.checked)}
                    />
                  }
                  label="Weekly Summary Reports"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Default Validation Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Default Validation Settings
              </Typography>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Default Priority</InputLabel>
                <Select
                  value={preferences.defaultPriority}
                  label="Default Priority"
                  onChange={(e) => setPreferences({ ...preferences, defaultPriority: e.target.value as any })}
                >
                  <MenuItem value="low">Low Priority</MenuItem>
                  <MenuItem value="medium">Medium Priority</MenuItem>
                  <MenuItem value="high">High Priority</MenuItem>
                </Select>
              </FormControl>
              
              <Typography variant="subtitle2" sx={{ mt: 3, mb: 2 }}>
                Default Analysis Scope
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Select which analysis areas to include by default in new validations
              </Typography>
              
              <Box display="flex" flexWrap="wrap" gap={1}>
                {analysisOptions.map((option) => (
                  <Chip
                    key={option.id}
                    label={option.label}
                    color={preferences.defaultAnalysisScope.includes(option.id) ? 'primary' : 'default'}
                    variant={preferences.defaultAnalysisScope.includes(option.id) ? 'filled' : 'outlined'}
                    onClick={() => handleAnalysisScopeChange(
                      option.id,
                      !preferences.defaultAnalysisScope.includes(option.id)
                    )}
                    clickable
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Data & Privacy */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data & Privacy
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Data Retention
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Your validation data is stored securely and retained according to our data policy.
                  </Typography>
                  <Button variant="outlined" size="small">
                    View Data Policy
                  </Button>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Export Data
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Download all your validation data and results in a portable format.
                  </Typography>
                  <Button variant="outlined" size="small">
                    Export Data
                  </Button>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" gutterBottom>
                    Delete Account
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Permanently delete your account and all associated data.
                  </Typography>
                  <Button variant="outlined" color="error" size="small">
                    Delete Account
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Save Button */}
      <Box mt={4} display="flex" justifyContent="flex-end">
        <Button
          variant="contained"
          size="large"
          startIcon={<SaveIcon />}
          onClick={handleSavePreferences}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </Box>
    </Box>
  );
};

export default Settings;