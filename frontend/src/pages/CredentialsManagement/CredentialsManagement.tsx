import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Alert,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import {
  CloudQueue as CloudIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useNotification } from '../../contexts/NotificationContext';
import { credentialsService } from '../../services/credentialsService';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import AWSCredentialsSetup from './components/AWSCredentialsSetup';
import ExternalAPIKeysSetup from './components/ExternalAPIKeysSetup';
import CostEstimation from './components/CostEstimation';
import BudgetManagement from './components/BudgetManagement';
import CredentialsList from './components/CredentialsList';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`credentials-tabpanel-${index}`}
      aria-labelledby={`credentials-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const CredentialsManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [configuredServices, setConfiguredServices] = useState<{
    aws_services: string[];
    external_services: string[];
    total_count: number;
  }>({
    aws_services: [],
    external_services: [],
    total_count: 0,
  });

  const { showNotification } = useNotification();

  useEffect(() => {
    loadConfiguredServices();
  }, []);

  const loadConfiguredServices = async () => {
    try {
      setLoading(true);
      setError('');
      
      const services = await credentialsService.listConfiguredServices();
      setConfiguredServices(services);
      
    } catch (err: any) {
      console.error('Failed to load configured services:', err);
      setError('Failed to load configured services. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleCredentialsUpdated = () => {
    loadConfiguredServices();
    showNotification('Credentials updated successfully', 'success');
  };

  if (loading) {
    return <LoadingSpinner size={60} message="Loading credentials management..." />;
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        AWS API Key Management
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" mb={4}>
        Securely manage your AWS credentials and external API keys for the RiskIntel360 platform
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Overview Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CloudIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">
                    {configuredServices.aws_services.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    AWS Services
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <SecurityIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">
                    {configuredServices.external_services.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    External APIs
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AssessmentIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">
                    {configuredServices.total_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Services
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <SettingsIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">
                    {configuredServices.aws_services.includes('aws') ? 'Active' : 'Inactive'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    AWS Status
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="credentials management tabs">
            <Tab label="AWS Setup" />
            <Tab label="External APIs" />
            <Tab label="Cost Estimation" />
            <Tab label="Budget Management" />
            <Tab label="Configured Services" />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <AWSCredentialsSetup 
            onCredentialsUpdated={handleCredentialsUpdated}
            isConfigured={configuredServices.aws_services.includes('aws')}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <ExternalAPIKeysSetup 
            onCredentialsUpdated={handleCredentialsUpdated}
            configuredServices={configuredServices.external_services}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <CostEstimation />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <BudgetManagement />
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <CredentialsList 
            configuredServices={configuredServices}
            onCredentialsUpdated={handleCredentialsUpdated}
          />
        </TabPanel>
      </Card>

      {/* Quick Actions */}
      <Box mt={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<CloudIcon />}
                  onClick={() => setActiveTab(0)}
                  disabled={configuredServices.aws_services.includes('aws')}
                >
                  {configuredServices.aws_services.includes('aws') ? 'AWS Configured' : 'Setup AWS'}
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<AssessmentIcon />}
                  onClick={() => setActiveTab(2)}
                >
                  Estimate Costs
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<SettingsIcon />}
                  onClick={() => setActiveTab(3)}
                >
                  Manage Budget
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default CredentialsManagement;