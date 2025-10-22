/**
 * Alert Management System Component
 * Handles notification preferences, alert rules, and alert history
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Badge,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  Divider,
  Stack,
  Avatar,
  Menu,
  Tooltip,
  Collapse,
  LinearProgress,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  NotificationsActive as NotificationsActiveIcon,
  NotificationsOff as NotificationsOffIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Person as PersonIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Web as WebIcon,
  PhoneAndroid as MobileIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  category: 'fraud' | 'compliance' | 'risk' | 'market' | 'kyc' | 'system';
  condition: {
    field: string;
    operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq' | 'contains' | 'between';
    value: any;
    threshold?: number;
  };
  severity: 'low' | 'medium' | 'high' | 'critical';
  isActive: boolean;
  notifications: {
    email: boolean;
    sms: boolean;
    push: boolean;
    webhook: boolean;
  };
  cooldownMinutes: number;
  createdAt: string;
  lastTriggered?: string;
  triggerCount: number;
}

export interface AlertInstance {
  id: string;
  ruleId: string;
  ruleName: string;
  category: AlertRule['category'];
  severity: AlertRule['severity'];
  title: string;
  message: string;
  data: any;
  status: 'active' | 'acknowledged' | 'resolved' | 'dismissed';
  createdAt: string;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
  resolvedAt?: string;
  resolvedBy?: string;
  actions?: {
    label: string;
    action: string;
    url?: string;
  }[];
}

export interface NotificationPreferences {
  email: {
    enabled: boolean;
    address: string;
    frequency: 'immediate' | 'hourly' | 'daily';
    categories: AlertRule['category'][];
    minSeverity: AlertRule['severity'];
  };
  sms: {
    enabled: boolean;
    phoneNumber: string;
    categories: AlertRule['category'][];
    minSeverity: AlertRule['severity'];
  };
  push: {
    enabled: boolean;
    categories: AlertRule['category'][];
    minSeverity: AlertRule['severity'];
  };
  webhook: {
    enabled: boolean;
    url: string;
    categories: AlertRule['category'][];
    minSeverity: AlertRule['severity'];
  };
}

export interface AlertManagementSystemProps {
  initialRules?: AlertRule[];
  initialAlerts?: AlertInstance[];
  initialPreferences?: NotificationPreferences;
  onRuleCreate?: (rule: Omit<AlertRule, 'id' | 'createdAt' | 'triggerCount'>) => void;
  onRuleUpdate?: (ruleId: string, updates: Partial<AlertRule>) => void;
  onRuleDelete?: (ruleId: string) => void;
  onAlertAction?: (alertId: string, action: string) => void;
  onPreferencesUpdate?: (preferences: NotificationPreferences) => void;
  enableRealTimeUpdates?: boolean;
}

export const AlertManagementSystem: React.FC<AlertManagementSystemProps> = ({
  initialRules = [],
  initialAlerts = [],
  initialPreferences,
  onRuleCreate,
  onRuleUpdate,
  onRuleDelete,
  onAlertAction,
  onPreferencesUpdate,
  enableRealTimeUpdates = true,
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [rules, setRules] = useState<AlertRule[]>(initialRules);
  const [alerts, setAlerts] = useState<AlertInstance[]>(initialAlerts);
  const [preferences, setPreferences] = useState<NotificationPreferences>(
    initialPreferences || {
      email: {
        enabled: true,
        address: '',
        frequency: 'immediate',
        categories: ['fraud', 'compliance', 'risk'],
        minSeverity: 'medium',
      },
      sms: {
        enabled: false,
        phoneNumber: '',
        categories: ['fraud', 'compliance'],
        minSeverity: 'high',
      },
      push: {
        enabled: true,
        categories: ['fraud', 'compliance', 'risk', 'market'],
        minSeverity: 'medium',
      },
      webhook: {
        enabled: false,
        url: '',
        categories: ['fraud', 'compliance'],
        minSeverity: 'high',
      },
    }
  );

  const [ruleDialogOpen, setRuleDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [preferencesDialogOpen, setPreferencesDialogOpen] = useState(false);
  const [alertMenuAnchor, setAlertMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedAlert, setSelectedAlert] = useState<AlertInstance | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());

  // Mock real-time updates
  useEffect(() => {
    if (enableRealTimeUpdates) {
      const interval = setInterval(() => {
        // Simulate new alerts
        if (Math.random() < 0.1) { // 10% chance every 5 seconds
          const categories: AlertRule['category'][] = ['fraud', 'compliance', 'risk', 'market', 'kyc'];
          const severities: AlertRule['severity'][] = ['low', 'medium', 'high', 'critical'];
          
          const newAlert: AlertInstance = {
            id: `alert-${Date.now()}`,
            ruleId: `rule-${Math.floor(Math.random() * 5)}`,
            ruleName: 'Real-time Detection Rule',
            category: categories[Math.floor(Math.random() * categories.length)],
            severity: severities[Math.floor(Math.random() * severities.length)],
            title: 'Anomaly Detected',
            message: 'Real-time monitoring has detected an anomaly requiring attention.',
            data: { value: Math.random() * 100, threshold: 75 },
            status: 'active',
            createdAt: new Date().toISOString(),
            actions: [
              { label: 'Investigate', action: 'investigate' },
              { label: 'Dismiss', action: 'dismiss' },
            ],
          };

          setAlerts(prev => [newAlert, ...prev.slice(0, 49)]); // Keep last 50 alerts
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [enableRealTimeUpdates]);

  const handleCreateRule = (ruleData: Omit<AlertRule, 'id' | 'createdAt' | 'triggerCount'>) => {
    const newRule: AlertRule = {
      ...ruleData,
      id: `rule-${Date.now()}`,
      createdAt: new Date().toISOString(),
      triggerCount: 0,
    };

    setRules(prev => [...prev, newRule]);
    onRuleCreate?.(ruleData);
    setRuleDialogOpen(false);
    setEditingRule(null);
    setSnackbarMessage('Alert rule created successfully');
    setSnackbarOpen(true);
  };

  const handleUpdateRule = (ruleId: string, updates: Partial<AlertRule>) => {
    setRules(prev => prev.map(rule => 
      rule.id === ruleId ? { ...rule, ...updates } : rule
    ));
    onRuleUpdate?.(ruleId, updates);
    setRuleDialogOpen(false);
    setEditingRule(null);
    setSnackbarMessage('Alert rule updated successfully');
    setSnackbarOpen(true);
  };

  const handleDeleteRule = (ruleId: string) => {
    setRules(prev => prev.filter(rule => rule.id !== ruleId));
    onRuleDelete?.(ruleId);
    setSnackbarMessage('Alert rule deleted successfully');
    setSnackbarOpen(true);
  };

  const handleAlertAction = (alertId: string, action: string) => {
    setAlerts(prev => prev.map(alert => {
      if (alert.id === alertId) {
        const now = new Date().toISOString();
        switch (action) {
          case 'acknowledge':
            return { ...alert, status: 'acknowledged', acknowledgedAt: now, acknowledgedBy: 'Current User' };
          case 'resolve':
            return { ...alert, status: 'resolved', resolvedAt: now, resolvedBy: 'Current User' };
          case 'dismiss':
            return { ...alert, status: 'dismissed' };
          default:
            return alert;
        }
      }
      return alert;
    }));
    
    onAlertAction?.(alertId, action);
    setAlertMenuAnchor(null);
    setSelectedAlert(null);
    setSnackbarMessage(`Alert ${action}d successfully`);
    setSnackbarOpen(true);
  };

  const handleToggleAlertExpansion = (alertId: string) => {
    setExpandedAlerts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(alertId)) {
        newSet.delete(alertId);
      } else {
        newSet.add(alertId);
      }
      return newSet;
    });
  };

  const getSeverityColor = (severity: AlertRule['severity']) => {
    switch (severity) {
      case 'critical':
        return theme.palette.error.main;
      case 'high':
        return theme.palette.warning.main;
      case 'medium':
        return theme.palette.info.main;
      case 'low':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getCategoryIcon = (category: AlertRule['category']) => {
    switch (category) {
      case 'fraud':
        return <SecurityIcon />;
      case 'compliance':
        return <AssessmentIcon />;
      case 'risk':
        return <WarningIcon />;
      case 'market':
        return <TrendingUpIcon />;
      case 'kyc':
        return <PersonIcon />;
      case 'system':
        return <InfoIcon />;
      default:
        return <NotificationsIcon />;
    }
  };

  const getStatusIcon = (status: AlertInstance['status']) => {
    switch (status) {
      case 'active':
        return <ErrorIcon color="error" />;
      case 'acknowledged':
        return <InfoIcon color="info" />;
      case 'resolved':
        return <CheckCircleIcon color="success" />;
      case 'dismissed':
        return <NotificationsOffIcon color="disabled" />;
      default:
        return <NotificationsIcon />;
    }
  };

  const activeAlerts = alerts.filter(alert => alert.status === 'active');
  const acknowledgedAlerts = alerts.filter(alert => alert.status === 'acknowledged');
  const resolvedAlerts = alerts.filter(alert => alert.status === 'resolved');

  const renderRuleDialog = () => (
    <Dialog
      open={ruleDialogOpen}
      onClose={() => {
        setRuleDialogOpen(false);
        setEditingRule(null);
      }}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        {editingRule ? 'Edit Alert Rule' : 'Create Alert Rule'}
      </DialogTitle>
      <DialogContent>
        <RuleForm
          initialRule={editingRule}
          onSubmit={editingRule ? 
            (updates) => handleUpdateRule(editingRule.id, updates) :
            handleCreateRule
          }
        />
      </DialogContent>
    </Dialog>
  );

  const renderAlertsList = (alertsList: AlertInstance[], title: string) => (
    <Box>
      <Typography variant="h6" gutterBottom>
        {title} ({alertsList.length})
      </Typography>
      <List>
        {alertsList.map(alert => (
          <React.Fragment key={alert.id}>
            <ListItem>
              <ListItemIcon>
                <Avatar sx={{ bgcolor: getSeverityColor(alert.severity), width: 32, height: 32 }}>
                  {getCategoryIcon(alert.category)}
                </Avatar>
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1" fontWeight="medium">
                      {alert.title}
                    </Typography>
                    <Chip
                      label={alert.severity}
                      size="small"
                      sx={{
                        backgroundColor: getSeverityColor(alert.severity),
                        color: 'white',
                      }}
                    />
                    <Chip
                      label={alert.category}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      {alert.message}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {new Date(alert.createdAt).toLocaleString()}
                    </Typography>
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <IconButton
                    onClick={() => handleToggleAlertExpansion(alert.id)}
                    size="small"
                  >
                    {expandedAlerts.has(alert.id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                  <IconButton
                    onClick={(e) => {
                      setAlertMenuAnchor(e.currentTarget);
                      setSelectedAlert(alert);
                    }}
                    size="small"
                  >
                    <MoreVertIcon />
                  </IconButton>
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
            
            <Collapse in={expandedAlerts.has(alert.id)}>
              <Box sx={{ pl: 8, pr: 2, pb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  <strong>Rule:</strong> {alert.ruleName}
                </Typography>
                {alert.data && (
                  <Typography variant="body2" gutterBottom>
                    <strong>Data:</strong> {JSON.stringify(alert.data, null, 2)}
                  </Typography>
                )}
                {alert.acknowledgedAt && (
                  <Typography variant="body2" gutterBottom>
                    <strong>Acknowledged:</strong> {new Date(alert.acknowledgedAt).toLocaleString()} by {alert.acknowledgedBy}
                  </Typography>
                )}
                {alert.resolvedAt && (
                  <Typography variant="body2" gutterBottom>
                    <strong>Resolved:</strong> {new Date(alert.resolvedAt).toLocaleString()} by {alert.resolvedBy}
                  </Typography>
                )}
                {alert.actions && (
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    {alert.actions.map(action => (
                      <Button
                        key={action.action}
                        size="small"
                        variant="outlined"
                        onClick={() => handleAlertAction(alert.id, action.action)}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </Stack>
                )}
              </Box>
            </Collapse>
            <Divider />
          </React.Fragment>
        ))}
      </List>
    </Box>
  );

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6">
              Alert Management
            </Typography>
            <Badge badgeContent={activeAlerts.length} color="error">
              <NotificationsActiveIcon />
            </Badge>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              startIcon={<AddIcon />}
              onClick={() => setRuleDialogOpen(true)}
              variant="outlined"
              size="small"
            >
              New Rule
            </Button>
            <Button
              startIcon={<NotificationsIcon />}
              onClick={() => setPreferencesDialogOpen(true)}
              variant="outlined"
              size="small"
            >
              Preferences
            </Button>
          </Box>
        </Box>

        {/* Summary Cards */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 3 }}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main">
                {activeAlerts.length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Active Alerts
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {acknowledgedAlerts.length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Acknowledged
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {resolvedAlerts.length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Resolved
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary.main">
                {rules.filter(r => r.isActive).length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Active Rules
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Tabs */}
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab label={`Active Alerts (${activeAlerts.length})`} />
          <Tab label={`Alert Rules (${rules.length})`} />
          <Tab label="Alert History" />
        </Tabs>

        {/* Tab Content */}
        {activeTab === 0 && (
          <Box>
            {activeAlerts.length > 0 ? (
              renderAlertsList(activeAlerts, 'Active Alerts')
            ) : (
              <Alert severity="success">
                No active alerts. Your system is running smoothly!
              </Alert>
            )}
          </Box>
        )}

        {activeTab === 1 && (
          <Box>
            <List>
              {rules.map(rule => (
                <React.Fragment key={rule.id}>
                  <ListItem>
                    <ListItemIcon>
                      {getCategoryIcon(rule.category)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body1" fontWeight="medium">
                            {rule.name}
                          </Typography>
                          <Chip
                            label={rule.isActive ? 'Active' : 'Inactive'}
                            size="small"
                            color={rule.isActive ? 'success' : 'default'}
                          />
                          <Chip
                            label={rule.severity}
                            size="small"
                            sx={{
                              backgroundColor: getSeverityColor(rule.severity),
                              color: 'white',
                            }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            {rule.description}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            Triggered {rule.triggerCount} times • Created {new Date(rule.createdAt).toLocaleDateString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        onClick={() => {
                          setEditingRule(rule);
                          setRuleDialogOpen(true);
                        }}
                        size="small"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        onClick={() => handleDeleteRule(rule.id)}
                        size="small"
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </Box>
        )}

        {activeTab === 2 && (
          <Box>
            {renderAlertsList([...acknowledgedAlerts, ...resolvedAlerts], 'Alert History')}
          </Box>
        )}
      </CardContent>

      {/* Alert Action Menu */}
      <Menu
        anchorEl={alertMenuAnchor}
        open={Boolean(alertMenuAnchor)}
        onClose={() => {
          setAlertMenuAnchor(null);
          setSelectedAlert(null);
        }}
      >
        {selectedAlert?.status === 'active' && (
          <MenuItem onClick={() => selectedAlert && handleAlertAction(selectedAlert.id, 'acknowledge')}>
            Acknowledge
          </MenuItem>
        )}
        {(selectedAlert?.status === 'active' || selectedAlert?.status === 'acknowledged') && (
          <MenuItem onClick={() => selectedAlert && handleAlertAction(selectedAlert.id, 'resolve')}>
            Resolve
          </MenuItem>
        )}
        <MenuItem onClick={() => selectedAlert && handleAlertAction(selectedAlert.id, 'dismiss')}>
          Dismiss
        </MenuItem>
      </Menu>

      {/* Rule Dialog */}
      {renderRuleDialog()}

      {/* Notification Preferences Dialog */}
      <NotificationPreferencesDialog
        open={preferencesDialogOpen}
        preferences={preferences}
        onClose={() => setPreferencesDialogOpen(false)}
        onSave={(newPreferences) => {
          setPreferences(newPreferences);
          onPreferencesUpdate?.(newPreferences);
          setPreferencesDialogOpen(false);
          setSnackbarMessage('Notification preferences updated');
          setSnackbarOpen(true);
        }}
      />

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Card>
  );
};

// Rule Form Component
const RuleForm: React.FC<{
  initialRule?: AlertRule | null;
  onSubmit: (rule: Omit<AlertRule, 'id' | 'createdAt' | 'triggerCount'>) => void;
}> = ({ initialRule, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: initialRule?.name || '',
    description: initialRule?.description || '',
    category: initialRule?.category || 'fraud' as AlertRule['category'],
    condition: initialRule?.condition || {
      field: '',
      operator: 'gt' as const,
      value: '',
    },
    severity: initialRule?.severity || 'medium' as AlertRule['severity'],
    isActive: initialRule?.isActive ?? true,
    notifications: initialRule?.notifications || {
      email: true,
      sms: false,
      push: true,
      webhook: false,
    },
    cooldownMinutes: initialRule?.cooldownMinutes || 60,
  });

  const handleSubmit = () => {
    onSubmit(formData);
  };

  return (
    <Stack spacing={3} sx={{ mt: 1 }}>
      <TextField
        label="Rule Name"
        value={formData.name}
        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
        fullWidth
        required
      />
      
      <TextField
        label="Description"
        value={formData.description}
        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
        fullWidth
        multiline
        rows={2}
      />

      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Category</InputLabel>
          <Select
            value={formData.category}
            label="Category"
            onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as AlertRule['category'] }))}
          >
            <MenuItem value="fraud">Fraud Detection</MenuItem>
            <MenuItem value="compliance">Compliance</MenuItem>
            <MenuItem value="risk">Risk Assessment</MenuItem>
            <MenuItem value="market">Market Analysis</MenuItem>
            <MenuItem value="kyc">KYC Verification</MenuItem>
            <MenuItem value="system">System</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Severity</InputLabel>
          <Select
            value={formData.severity}
            label="Severity"
            onChange={(e) => setFormData(prev => ({ ...prev, severity: e.target.value as AlertRule['severity'] }))}
          >
            <MenuItem value="low">Low</MenuItem>
            <MenuItem value="medium">Medium</MenuItem>
            <MenuItem value="high">High</MenuItem>
            <MenuItem value="critical">Critical</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Typography variant="subtitle2">Condition</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 2 }}>
        <TextField
          label="Field"
          value={formData.condition.field}
          onChange={(e) => setFormData(prev => ({
            ...prev,
            condition: { ...prev.condition, field: e.target.value }
          }))}
          placeholder="e.g., fraud_score"
        />
        
        <FormControl>
          <InputLabel>Operator</InputLabel>
          <Select
            value={formData.condition.operator}
            label="Operator"
            onChange={(e) => setFormData(prev => ({
              ...prev,
              condition: { ...prev.condition, operator: e.target.value as any }
            }))}
          >
            <MenuItem value="gt">Greater Than</MenuItem>
            <MenuItem value="gte">Greater Than or Equal</MenuItem>
            <MenuItem value="lt">Less Than</MenuItem>
            <MenuItem value="lte">Less Than or Equal</MenuItem>
            <MenuItem value="eq">Equals</MenuItem>
            <MenuItem value="neq">Not Equals</MenuItem>
            <MenuItem value="contains">Contains</MenuItem>
            <MenuItem value="between">Between</MenuItem>
          </Select>
        </FormControl>

        <TextField
          label="Value"
          value={formData.condition.value}
          onChange={(e) => setFormData(prev => ({
            ...prev,
            condition: { ...prev.condition, value: e.target.value }
          }))}
          placeholder="e.g., 0.8"
        />
      </Box>

      <Typography variant="subtitle2">Notifications</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
        <FormControlLabel
          control={
            <Switch
              checked={formData.notifications.email}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                notifications: { ...prev.notifications, email: e.target.checked }
              }))}
            />
          }
          label="Email"
        />
        <FormControlLabel
          control={
            <Switch
              checked={formData.notifications.sms}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                notifications: { ...prev.notifications, sms: e.target.checked }
              }))}
            />
          }
          label="SMS"
        />
        <FormControlLabel
          control={
            <Switch
              checked={formData.notifications.push}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                notifications: { ...prev.notifications, push: e.target.checked }
              }))}
            />
          }
          label="Push Notification"
        />
        <FormControlLabel
          control={
            <Switch
              checked={formData.notifications.webhook}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                notifications: { ...prev.notifications, webhook: e.target.checked }
              }))}
            />
          }
          label="Webhook"
        />
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
        <TextField
          label="Cooldown (minutes)"
          type="number"
          value={formData.cooldownMinutes}
          onChange={(e) => setFormData(prev => ({ ...prev, cooldownMinutes: Number(e.target.value) }))}
          inputProps={{ min: 1 }}
        />
        
        <FormControlLabel
          control={
            <Switch
              checked={formData.isActive}
              onChange={(e) => setFormData(prev => ({ ...prev, isActive: e.target.checked }))}
            />
          }
          label="Active"
        />
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button variant="contained" onClick={handleSubmit}>
          {initialRule ? 'Update Rule' : 'Create Rule'}
        </Button>
      </Box>
    </Stack>
  );
};

// Notification Preferences Dialog Component
const NotificationPreferencesDialog: React.FC<{
  open: boolean;
  preferences: NotificationPreferences;
  onClose: () => void;
  onSave: (preferences: NotificationPreferences) => void;
}> = ({ open, preferences, onClose, onSave }) => {
  const [formData, setFormData] = useState(preferences);

  useEffect(() => {
    setFormData(preferences);
  }, [preferences]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Notification Preferences</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Email Preferences */}
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <EmailIcon />
                <Typography variant="h6">Email Notifications</Typography>
                <Switch
                  checked={formData.email.enabled}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    email: { ...prev.email, enabled: e.target.checked }
                  }))}
                />
              </Box>
              {formData.email.enabled && (
                <Stack spacing={2}>
                  <TextField
                    label="Email Address"
                    value={formData.email.address}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      email: { ...prev.email, address: e.target.value }
                    }))}
                    fullWidth
                  />
                  <FormControl fullWidth>
                    <InputLabel>Frequency</InputLabel>
                    <Select
                      value={formData.email.frequency}
                      label="Frequency"
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        email: { ...prev.email, frequency: e.target.value as any }
                      }))}
                    >
                      <MenuItem value="immediate">Immediate</MenuItem>
                      <MenuItem value="hourly">Hourly Digest</MenuItem>
                      <MenuItem value="daily">Daily Digest</MenuItem>
                    </Select>
                  </FormControl>
                </Stack>
              )}
            </CardContent>
          </Card>

          {/* SMS Preferences */}
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <SmsIcon />
                <Typography variant="h6">SMS Notifications</Typography>
                <Switch
                  checked={formData.sms.enabled}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    sms: { ...prev.sms, enabled: e.target.checked }
                  }))}
                />
              </Box>
              {formData.sms.enabled && (
                <TextField
                  label="Phone Number"
                  value={formData.sms.phoneNumber}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    sms: { ...prev.sms, phoneNumber: e.target.value }
                  }))}
                  fullWidth
                />
              )}
            </CardContent>
          </Card>

          {/* Push Preferences */}
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <MobileIcon />
                <Typography variant="h6">Push Notifications</Typography>
                <Switch
                  checked={formData.push.enabled}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    push: { ...prev.push, enabled: e.target.checked }
                  }))}
                />
              </Box>
            </CardContent>
          </Card>

          {/* Webhook Preferences */}
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <WebIcon />
                <Typography variant="h6">Webhook Notifications</Typography>
                <Switch
                  checked={formData.webhook.enabled}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    webhook: { ...prev.webhook, enabled: e.target.checked }
                  }))}
                />
              </Box>
              {formData.webhook.enabled && (
                <TextField
                  label="Webhook URL"
                  value={formData.webhook.url}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    webhook: { ...prev.webhook, url: e.target.value }
                  }))}
                  fullWidth
                />
              )}
            </CardContent>
          </Card>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={() => onSave(formData)} variant="contained">
          Save Preferences
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AlertManagementSystem;