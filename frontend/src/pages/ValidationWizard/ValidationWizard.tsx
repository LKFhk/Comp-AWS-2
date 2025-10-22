import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  FormControlLabel,
  Checkbox,
  Alert,
  Paper,
  Grid,
  Divider,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  Send as SendIcon,
  BusinessCenter as BusinessIcon,
  Public as PublicIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
// import { useAuth } from '../../contexts/AuthContext'; // Currently unused
import { useNotification } from '../../contexts/NotificationContext';
import { apiService, ValidationRequest } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';

const steps = [
  'Financial Entity',
  'Market & Jurisdiction',
  'Risk Dimensions',
  'Configuration',
  'Review & Submit'
];

const analysisOptions = [
  { id: 'market_risk', label: 'Market Risk Analysis', description: 'Market volatility, price movements, and economic indicator impacts' },
  { id: 'fraud_detection', label: 'Fraud Detection & Prevention', description: 'ML-powered transaction anomaly detection and fraud pattern recognition' },
  { id: 'credit_risk', label: 'Credit Risk Assessment', description: 'Credit exposure, default probability, and counterparty risk evaluation' },
  { id: 'compliance_monitoring', label: 'Regulatory Compliance Monitoring', description: 'SEC, FINRA, CFPB compliance tracking and regulatory change alerts' },
  { id: 'kyc_verification', label: 'KYC Verification & Customer Risk', description: 'Customer identity verification, sanctions screening, and behavioral risk scoring' },
];

const ValidationWizard: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Form data
  const [formData, setFormData] = useState<ValidationRequest>({
    financial_institution_profile: '',
    regulatory_jurisdiction: '',
    analysis_scope: ['market_risk', 'fraud_detection', 'credit_risk', 'compliance_monitoring', 'kyc_verification'],
    priority: 'medium',
    custom_parameters: {},
  });

  const navigate = useNavigate();
  // const { user } = useAuth(); // Currently unused
  const { showNotification } = useNotification();

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
      setError('');
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
    setError('');
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        if (!formData.financial_institution_profile.trim()) {
          setError('Please describe your financial institution profile');
          return false;
        }
        if (formData.financial_institution_profile.length < 10) {
          setError('Financial institution profile must be at least 10 characters');
          return false;
        }
        break;
      case 1:
        if (!formData.regulatory_jurisdiction.trim()) {
          setError('Please describe your regulatory jurisdiction and market segment');
          return false;
        }
        if (formData.regulatory_jurisdiction.length < 5) {
          setError('Regulatory jurisdiction description must be at least 5 characters');
          return false;
        }
        break;
      case 2:
        if (formData.analysis_scope.length === 0) {
          setError('Please select at least one risk dimension');
          return false;
        }
        break;
      default:
        break;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validateStep(activeStep)) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await apiService.createValidation(formData);
      showNotification('Financial risk analysis initiated successfully!', 'success');
      navigate(`/validation/${response.id}/progress`);
    } catch (err: any) {
      console.error('Failed to create validation:', err);
      setError(err.response?.data?.detail || 'Failed to initiate financial risk analysis');
      showNotification('Failed to initiate financial risk analysis', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalysisScopeChange = (optionId: string, checked: boolean) => {
    if (checked) {
      setFormData({
        ...formData,
        analysis_scope: [...formData.analysis_scope, optionId],
      });
    } else {
      setFormData({
        ...formData,
        analysis_scope: formData.analysis_scope.filter(id => id !== optionId),
      });
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Box display="flex" alignItems="center" mb={3}>
              <BusinessIcon color="primary" sx={{ mr: 2, fontSize: 32 }} />
              <Typography variant="h5">Describe Your Financial Entity</Typography>
            </Box>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Financial Institution Profile"
              placeholder="Describe your financial institution (e.g., FinTech startup processing $50M annual transactions, Regional bank with 500K customers, Payment gateway handling cross-border transfers, Cryptocurrency exchange with 100K users)..."
              value={formData.financial_institution_profile}
              onChange={(e) => setFormData({ ...formData, financial_institution_profile: e.target.value })}
              helperText={`${formData.financial_institution_profile.length}/1000 characters`}
              inputProps={{ maxLength: 1000 }}
              data-testid="wizard-institution-input"
            />
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Tip:</strong> Include your business model, transaction volume, regulatory jurisdiction, and key risk factors. 
                More detail enables more accurate fraud detection, compliance analysis, and risk assessment.
              </Typography>
            </Alert>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Box display="flex" alignItems="center" mb={3}>
              <PublicIcon color="primary" sx={{ mr: 2, fontSize: 32 }} />
              <Typography variant="h5">Define Market Segment & Jurisdiction</Typography>
            </Box>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Regulatory Jurisdiction & Market Segment"
              placeholder="Describe the financial market segment, customer demographics, geographic regions, and regulatory jurisdictions (e.g., US SEC/FINRA regulated broker-dealer, EU MiFID II compliant investment firm, APAC digital banking platform)..."
              value={formData.regulatory_jurisdiction}
              onChange={(e) => setFormData({ ...formData, regulatory_jurisdiction: e.target.value })}
              helperText={`${formData.regulatory_jurisdiction.length}/500 characters`}
              inputProps={{ maxLength: 500 }}
              data-testid="wizard-jurisdiction-input"
            />
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Examples:</strong> "US SEC/FINRA regulated broker-dealer serving institutional clients", 
                "EU MiFID II compliant investment firm with retail focus", "APAC digital banking platform for SME lending"
              </Typography>
            </Alert>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Box display="flex" alignItems="center" mb={3}>
              <AssessmentIcon color="primary" sx={{ mr: 2, fontSize: 32 }} />
              <Typography variant="h5">Select Risk Analysis Dimensions</Typography>
            </Box>
            <Typography variant="body1" color="text.secondary" mb={3}>
              Choose which risk dimensions to analyze. Each specialized AI agent provides deep financial intelligence:
            </Typography>
            <Grid container spacing={2}>
              {analysisOptions.map((option) => (
                <Grid item xs={12} md={6} key={option.id}>
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      cursor: 'pointer',
                      border: formData.analysis_scope.includes(option.id) ? 2 : 1,
                      borderColor: formData.analysis_scope.includes(option.id) ? 'primary.main' : 'divider',
                      '&:hover': {
                        borderColor: 'primary.main',
                      },
                    }}
                    onClick={() => handleAnalysisScopeChange(option.id, !formData.analysis_scope.includes(option.id))}
                  >
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={formData.analysis_scope.includes(option.id)}
                          onChange={(e) => handleAnalysisScopeChange(option.id, e.target.checked)}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="subtitle1" fontWeight="medium">
                            {option.label}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {option.description}
                          </Typography>
                        </Box>
                      }
                    />
                  </Paper>
                </Grid>
              ))}
            </Grid>
            <Alert severity="success" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Recommended:</strong> Select all dimensions for comprehensive risk analysis. 
                Each specialized AI agent provides unique financial intelligence that complements the others.
              </Typography>
            </Alert>
          </Box>
        );

      case 3:
        return (
          <Box>
            <Box display="flex" alignItems="center" mb={3}>
              <SettingsIcon color="primary" sx={{ mr: 2, fontSize: 32 }} />
              <Typography variant="h5">Configuration Settings</Typography>
            </Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Priority Level</InputLabel>
                  <Select
                    value={formData.priority}
                    label="Priority Level"
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                  >
                    <MenuItem value="low">
                      <Box>
                        <Typography>Low Priority</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Standard processing (~2 hours)
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="medium">
                      <Box>
                        <Typography>Medium Priority</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Balanced processing (~1.5 hours)
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="high">
                      <Box>
                        <Typography>High Priority</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Fast processing (~1 hour)
                        </Typography>
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Priority affects processing speed:</strong> Higher priority risk analyses are processed faster 
                but may consume more resources. Medium priority is recommended for most use cases.
              </Typography>
            </Alert>
          </Box>
        );

      case 4:
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Review Your Risk Analysis Request
            </Typography>
            <Typography variant="body1" color="text.secondary" mb={3}>
              Review your request before submitting. Our 5 specialized fintech AI agents will begin comprehensive risk analysis immediately.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Financial Institution
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {formData.financial_institution_profile}
                    </Typography>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="h6" gutterBottom>
                      Regulatory Jurisdiction
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {formData.regulatory_jurisdiction}
                    </Typography>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="h6" gutterBottom>
                      Risk Analysis Dimensions
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                      {formData.analysis_scope.map((scope) => {
                        const option = analysisOptions.find(opt => opt.id === scope);
                        return (
                          <Chip
                            key={scope}
                            label={option?.label}
                            color="primary"
                            variant="outlined"
                          />
                        );
                      })}
                    </Box>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="h6" gutterBottom>
                      Priority Level
                    </Typography>
                    <Chip
                      label={`${formData.priority.charAt(0).toUpperCase() + formData.priority.slice(1)} Priority`}
                      color={formData.priority === 'high' ? 'error' : formData.priority === 'medium' ? 'warning' : 'default'}
                    />
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Estimated completion time:</strong> {
                  formData.priority === 'high' ? '~1 hour' :
                  formData.priority === 'medium' ? '~1.5 hours' : '~2 hours'
                } for {formData.analysis_scope.length} risk dimensions.
              </Typography>
            </Alert>
          </Box>
        );

      default:
        return 'Unknown step';
    }
  };

  if (loading) {
    return <LoadingSpinner size={60} message="Creating your validation request..." />;
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        New Financial Risk Analysis
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" mb={4}>
        Comprehensive financial intelligence powered by 5 specialized AI agents
      </Typography>

      <Card>
        <CardContent>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ minHeight: 400 }}>
            {getStepContent(activeStep)}
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
            <Button
              color="inherit"
              disabled={activeStep === 0}
              onClick={handleBack}
              startIcon={<ArrowBackIcon />}
              sx={{ mr: 1 }}
              data-testid="wizard-back-button"
            >
              Back
            </Button>
            <Box sx={{ flex: '1 1 auto' }} />
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleSubmit}
                startIcon={<SendIcon />}
                disabled={loading}
                data-testid="wizard-submit-button"
              >
                Start Risk Analysis
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<ArrowForwardIcon />}
                data-testid="wizard-next-button"
              >
                Next
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ValidationWizard;