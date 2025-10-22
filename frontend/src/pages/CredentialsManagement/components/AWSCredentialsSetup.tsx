import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Link,
  Switch,
  FormControlLabel,
  Tooltip,
} from '@mui/material';
import {
  CloudQueue as CloudIcon,
  Security as SecurityIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Launch as LaunchIcon,
  Science as ScienceIcon,
  Rocket as RocketIcon,
} from '@mui/icons-material';
import { credentialsService, AWSCredentials } from '../../../services/credentialsService';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../../components/Common/LoadingSpinner';

interface AWSCredentialsSetupProps {
  onCredentialsUpdated: () => void;
  isConfigured: boolean;
}

const AWSCredentialsSetup: React.FC<AWSCredentialsSetupProps> = ({
  onCredentialsUpdated,
  isConfigured,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [credentials, setCredentials] = useState<AWSCredentials>({
    access_key_id: '',
    secret_access_key: '',
    region: 'us-east-1',
  });
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState('');
  const [validationResult, setValidationResult] = useState<any>(null);
  const [showCredentials, setShowCredentials] = useState(false);
  const [enableProductionMode, setEnableProductionMode] = useState(false);

  const { showNotification } = useNotification();

  const awsRegions = [
    { value: 'us-east-1', label: 'US East (N. Virginia)' },
    { value: 'us-east-2', label: 'US East (Ohio)' },
    { value: 'us-west-1', label: 'US West (N. California)' },
    { value: 'us-west-2', label: 'US West (Oregon)' },
    { value: 'eu-west-1', label: 'Europe (Ireland)' },
    { value: 'eu-west-2', label: 'Europe (London)' },
    { value: 'eu-central-1', label: 'Europe (Frankfurt)' },
    { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
    { value: 'ap-southeast-2', label: 'Asia Pacific (Sydney)' },
    { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)' },
  ];

  const steps = [
    'AWS Account Setup',
    'Create IAM User',
    'Configure Permissions',
    'Enter Credentials',
    'Validate & Complete',
  ];

  const handleInputChange = (field: keyof AWSCredentials) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setCredentials({
      ...credentials,
      [field]: event.target.value,
    });
    setError('');
    setValidationResult(null);
  };

  const handleRegionChange = (event: any) => {
    setCredentials({
      ...credentials,
      region: event.target.value,
    });
  };

  const validateAndSetupCredentials = async () => {
    try {
      setValidating(true);
      setError('');

      // Client-side validation
      const validationErrors = credentialsService.validateAWSCredentials(credentials);
      if (validationErrors.length > 0) {
        setError(validationErrors.join(', '));
        return;
      }

      // Server-side validation and setup
      const result = await credentialsService.setupAWSCredentials(credentials);
      setValidationResult(result);

      if (result.valid) {
        showNotification('AWS credentials configured successfully!', 'success');
        onCredentialsUpdated();
        setActiveStep(4); // Move to completion step
      } else {
        setError(result.error_message || 'Credential validation failed');
      }
    } catch (err: any) {
      console.error('Failed to setup AWS credentials:', err);
      setError(err.message || 'Failed to setup AWS credentials');
    } finally {
      setValidating(false);
    }
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setCredentials({
      access_key_id: '',
      secret_access_key: '',
      region: 'us-east-1',
    });
    setError('');
    setValidationResult(null);
  };

  if (isConfigured) {
    return (
      <Box>
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            AWS Credentials Already Configured
          </Typography>
          <Typography variant="body2">
            Your AWS credentials are already set up and validated. You can manage your budget limits
            and view cost estimates in the other tabs.
          </Typography>
        </Alert>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Configuration
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
                <Chip
                  icon={<CheckIcon />}
                  label="Active"
                  color="success"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">
                  Services
                </Typography>
                <Typography variant="body1">
                  AWS, Amazon Bedrock
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        AWS Credentials Setup Wizard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Follow these steps to securely configure your AWS credentials for the RiskIntel360 platform.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Stepper activeStep={activeStep} orientation="vertical">
        {/* Step 1: AWS Account Setup */}
        <Step>
          <StepLabel>AWS Account Setup</StepLabel>
          <StepContent>
            <Typography paragraph>
              You'll need an AWS account with access to Amazon Bedrock Nova and other required services.
            </Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Required AWS Services:</strong>
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CloudIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Amazon Bedrock (Claude-3 models)" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CloudIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Amazon ECS (for agent runtime)" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CloudIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Amazon Aurora Serverless (optional)" />
                </ListItem>
              </List>
            </Alert>

            <Box sx={{ mb: 2 }}>
              <Button
                variant="outlined"
                startIcon={<LaunchIcon />}
                href="https://aws.amazon.com/console/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Open AWS Console
              </Button>
            </Box>

            <Box sx={{ mb: 1 }}>
              <Button
                variant="contained"
                onClick={handleNext}
                sx={{ mt: 1, mr: 1 }}
              >
                Continue
              </Button>
            </Box>
          </StepContent>
        </Step>

        {/* Step 2: Create IAM User */}
        <Step>
          <StepLabel>Create IAM User</StepLabel>
          <StepContent>
            <Typography paragraph>
              Create a dedicated IAM user for the RiskIntel360 platform with programmatic access.
            </Typography>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Security Best Practice:</strong> Never use your root AWS account credentials.
                Always create a dedicated IAM user with minimal required permissions.
              </Typography>
            </Alert>

            <Typography variant="h6" gutterBottom>
              Steps to create IAM user:
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="1. Go to IAM Console → Users → Create User"
                  secondary="Choose a descriptive name like 'riskintel360-platform'"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="2. Select 'Programmatic access'"
                  secondary="This creates access keys for API calls"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="3. Don't attach policies yet"
                  secondary="We'll configure permissions in the next step"
                />
              </ListItem>
            </List>

            <Box sx={{ mb: 1 }}>
              <Button
                variant="contained"
                onClick={handleNext}
                sx={{ mt: 1, mr: 1 }}
              >
                Continue
              </Button>
              <Button onClick={handleBack} sx={{ mt: 1, mr: 1 }}>
                Back
              </Button>
            </Box>
          </StepContent>
        </Step>

        {/* Step 3: Configure Permissions */}
        <Step>
          <StepLabel>Configure Permissions</StepLabel>
          <StepContent>
            <Typography paragraph>
              Attach the necessary permissions to your IAM user for RiskIntel360 platform access.
            </Typography>

            <Typography variant="h6" gutterBottom>
              Required Permissions:
            </Typography>
            
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Minimum Required Policies:
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><SecurityIcon fontSize="small" /></ListItemIcon>
                    <ListItemText 
                      primary="AmazonBedrockFullAccess"
                      secondary="Access to Bedrock Nova (Claude-3) models"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><SecurityIcon fontSize="small" /></ListItemIcon>
                    <ListItemText 
                      primary="BedrockAgentCoreFullAccess"
                      secondary="For AgentCore multi-agent coordination primitives"
                    />
                  </ListItem>

                </List>
              </CardContent>
            </Card>

            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Optional (for full features):
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><SecurityIcon fontSize="small" /></ListItemIcon>
                    <ListItemText 
                      primary="AmazonRDSFullAccess"
                      secondary="For Aurora Serverless database"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><SecurityIcon fontSize="small" /></ListItemIcon>
                    <ListItemText 
                      primary="AmazonElastiCacheFullAccess"
                      secondary="For Redis caching"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>

            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                You can start with just Bedrock access and add other permissions later as needed.
              </Typography>
            </Alert>

            <Box sx={{ mb: 1 }}>
              <Button
                variant="contained"
                onClick={handleNext}
                sx={{ mt: 1, mr: 1 }}
              >
                Continue
              </Button>
              <Button onClick={handleBack} sx={{ mt: 1, mr: 1 }}>
                Back
              </Button>
            </Box>
          </StepContent>
        </Step>

        {/* Step 4: Enter Credentials */}
        <Step>
          <StepLabel>Enter Credentials</StepLabel>
          <StepContent>
            <Typography paragraph>
              Enter your AWS access keys. These will be encrypted and stored securely.
            </Typography>

            <Alert severity="warning" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Security Notice:</strong> Your credentials are encrypted at rest and never logged.
                Only you have access to your stored credentials.
              </Typography>
            </Alert>

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="AWS Access Key ID"
                  value={credentials.access_key_id}
                  onChange={handleInputChange('access_key_id')}
                  placeholder="AKIA..."
                  helperText="Starts with AKIA or ASIA"
                  required
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="AWS Secret Access Key"
                  type={showCredentials ? 'text' : 'password'}
                  value={credentials.secret_access_key}
                  onChange={handleInputChange('secret_access_key')}
                  placeholder="Enter your secret access key"
                  helperText="Keep this secret and secure"
                  required
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>AWS Region</InputLabel>
                  <Select
                    value={credentials.region}
                    label="AWS Region"
                    onChange={handleRegionChange}
                  >
                    {awsRegions.map((region) => (
                      <MenuItem key={region.value} value={region.value}>
                        {region.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Card variant="outlined" sx={{ bgcolor: 'background.default' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center">
                        {enableProductionMode ? (
                          <RocketIcon color="primary" sx={{ mr: 2 }} />
                        ) : (
                          <ScienceIcon color="action" sx={{ mr: 2 }} />
                        )}
                        <Box>
                          <Typography variant="subtitle1" fontWeight="bold">
                            AgentCore Production Mode
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {enableProductionMode 
                              ? 'Using real AWS Bedrock Agents API for multi-agent coordination'
                              : 'Using simulation mode for development (no Bedrock Agents setup required)'}
                          </Typography>
                        </Box>
                      </Box>
                      <Tooltip title={enableProductionMode 
                        ? 'Switch to simulation mode for development' 
                        : 'Enable real Bedrock Agents API (requires Bedrock Agents setup)'}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={enableProductionMode}
                              onChange={(e) => setEnableProductionMode(e.target.checked)}
                              color="primary"
                            />
                          }
                          label={enableProductionMode ? 'Production' : 'Development'}
                        />
                      </Tooltip>
                    </Box>

                    {enableProductionMode ? (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          Production Mode Requirements:
                        </Typography>
                        <List dense>
                          <ListItem sx={{ py: 0 }}>
                            <ListItemText 
                              primary="• Bedrock Agents must be created in AWS Console"
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                          <ListItem sx={{ py: 0 }}>
                            <ListItemText 
                              primary="• Agent IDs must be registered in the system"
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                          <ListItem sx={{ py: 0 }}>
                            <ListItemText 
                              primary="• IAM permissions for bedrock-agent and bedrock-agent-runtime"
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        </List>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          <Link 
                            href="https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html" 
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Learn more about AWS Bedrock Agents →
                          </Link>
                        </Typography>
                      </Alert>
                    ) : (
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          <strong>Development Mode (Recommended for testing):</strong> Uses local simulation 
                          for multi-agent coordination. No Bedrock Agents setup required. Perfect for 
                          development and testing without AWS costs.
                        </Typography>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Box sx={{ mt: 2, mb: 1 }}>
              <Button
                variant="contained"
                onClick={validateAndSetupCredentials}
                disabled={validating || !credentials.access_key_id || !credentials.secret_access_key}
                sx={{ mt: 1, mr: 1 }}
              >
                {validating ? 'Validating AWS credentials...' : 'Validate & Setup'}
              </Button>
              <Button onClick={handleBack} sx={{ mt: 1, mr: 1 }}>
                Back
              </Button>
            </Box>

            {validating && (
              <Box sx={{ mt: 2 }}>
                <LoadingSpinner size={24} message="Validating AWS credentials..." />
              </Box>
            )}
          </StepContent>
        </Step>

        {/* Step 5: Validation Results */}
        <Step>
          <StepLabel>Validate & Complete</StepLabel>
          <StepContent>
            {validationResult ? (
              <Box>
                {validationResult.valid ? (
                  <Alert severity="success" sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      ✅ AWS Credentials Successfully Configured!
                    </Typography>
                    <Typography variant="body2">
                      Your credentials have been validated and securely stored.
                    </Typography>
                  </Alert>
                ) : (
                  <Alert severity="error" sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      ❌ Credential Validation Failed
                    </Typography>
                    <Typography variant="body2">
                      {validationResult.error_message}
                    </Typography>
                  </Alert>
                )}

                {validationResult.valid && (
                  <Card sx={{ mb: 3 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Configuration Summary
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" color="text.secondary">
                            Region
                          </Typography>
                          <Typography variant="body1">
                            {validationResult.region}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" color="text.secondary">
                            Permissions
                          </Typography>
                          <Box>
                            {validationResult.permissions?.map((permission: string) => (
                              <Chip
                                key={permission}
                                label={permission}
                                size="small"
                                sx={{ mr: 1, mb: 1 }}
                              />
                            ))}
                          </Box>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                )}

                {validationResult.cost_estimate && (
                  <Card sx={{ mb: 3 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Cost Estimate (Sample Validation)
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        Estimated cost for a typical business validation:
                      </Typography>
                      <Typography variant="h4" color="primary">
                        ${validationResult.cost_estimate.total_cost_usd}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Duration: ~{validationResult.cost_estimate.estimated_duration_minutes} minutes
                      </Typography>
                    </CardContent>
                  </Card>
                )}

                <Box sx={{ mb: 1 }}>
                  {validationResult.valid ? (
                    <Button
                      variant="contained"
                      color="success"
                      onClick={() => {
                        showNotification('Setup completed successfully!', 'success');
                        onCredentialsUpdated();
                      }}
                    >
                      Complete Setup
                    </Button>
                  ) : (
                    <Button
                      variant="outlined"
                      onClick={() => setActiveStep(3)}
                      sx={{ mr: 1 }}
                    >
                      Try Again
                    </Button>
                  )}
                  <Button onClick={handleReset} sx={{ ml: 1 }}>
                    Start Over
                  </Button>
                </Box>
              </Box>
            ) : (
              <Typography>
                Click "Validate & Setup" in the previous step to continue.
              </Typography>
            )}
          </StepContent>
        </Step>
      </Stepper>
    </Box>
  );
};

export default AWSCredentialsSetup;