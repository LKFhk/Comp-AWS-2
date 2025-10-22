/**
 * Onboarding Flow Component
 * Guided tour for new users to understand the platform
 */

import React, { useState } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Person as PersonIcon,
  AttachMoney as MoneyIcon,
  CheckCircle as CheckCircleIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface OnboardingStep {
  label: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  features: string[];
  action?: {
    label: string;
    path: string;
  };
}

const onboardingSteps: OnboardingStep[] = [
  {
    label: 'Welcome to RiskIntel360',
    title: 'AI-Powered Financial Risk Intelligence',
    description: 'Transform manual financial risk analysis into intelligent, automated insights in under 2 hours with 95% time reduction and 80% cost savings.',
    icon: <DashboardIcon sx={{ fontSize: 60 }} />,
    features: [
      'Multi-agent AI architecture with 5 specialized agents',
      'Real-time financial risk monitoring',
      'Automated compliance and fraud detection',
      'Comprehensive market intelligence',
    ],
  },
  {
    label: 'Compliance Monitoring',
    title: 'Automated Regulatory Compliance',
    description: 'Monitor regulatory changes from SEC, FINRA, CFPB and assess compliance requirements automatically.',
    icon: <AssessmentIcon sx={{ fontSize: 60 }} />,
    features: [
      'Real-time regulatory change tracking',
      'Automated compliance gap analysis',
      'Remediation plan generation',
      '$5M+ annual compliance cost savings',
    ],
    action: {
      label: 'View Compliance Dashboard',
      path: '/fintech/compliance',
    },
  },
  {
    label: 'Fraud Detection',
    title: 'Advanced ML-Powered Fraud Detection',
    description: 'Detect fraud patterns in real-time with 90% reduction in false positives using unsupervised machine learning.',
    icon: <SecurityIcon sx={{ fontSize: 60 }} />,
    features: [
      'Real-time transaction analysis',
      'Unsupervised ML anomaly detection',
      '90% false positive reduction',
      '$10M+ annual fraud prevention',
    ],
    action: {
      label: 'View Fraud Dashboard',
      path: '/fintech/fraud',
    },
  },
  {
    label: 'Market Intelligence',
    title: 'Financial Market Analysis',
    description: 'AI-powered market intelligence using public data sources for comprehensive financial insights.',
    icon: <TrendingUpIcon sx={{ fontSize: 60 }} />,
    features: [
      'Real-time market data analysis',
      'Economic indicator tracking',
      'Sentiment analysis from financial news',
      '85% insights from free public sources',
    ],
    action: {
      label: 'View Market Dashboard',
      path: '/fintech/market',
    },
  },
  {
    label: 'KYC Verification',
    title: 'Automated Customer Verification',
    description: 'Streamline KYC processes with automated verification and risk scoring.',
    icon: <PersonIcon sx={{ fontSize: 60 }} />,
    features: [
      'Automated document verification',
      'Risk-based customer scoring',
      'Sanctions list checking',
      'Compliance workflow automation',
    ],
    action: {
      label: 'View KYC Dashboard',
      path: '/fintech/kyc',
    },
  },
  {
    label: 'Business Value',
    title: 'Measurable ROI and Impact',
    description: 'Track and demonstrate the business value generated through fraud prevention, compliance automation, and risk reduction.',
    icon: <MoneyIcon sx={{ fontSize: 60 }} />,
    features: [
      '$20M+ annual value generation',
      '1010% ROI for large institutions',
      'Scalable for companies of all sizes',
      'Real-time value tracking',
    ],
    action: {
      label: 'View Business Value Dashboard',
      path: '/fintech/business-value',
    },
  },
];

export const OnboardingFlow: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [showDialog, setShowDialog] = useState(true);
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleSkip = () => {
    // Mark onboarding as completed
    if (user) {
      updateUser({
        preferences: {
          ...user.preferences,
          onboardingCompleted: true,
        },
      });
    }
    navigate('/dashboard');
  };

  const handleComplete = () => {
    // Mark onboarding as completed
    if (user) {
      updateUser({
        preferences: {
          ...user.preferences,
          onboardingCompleted: true,
        },
      });
    }
    navigate('/fintech/risk-intel');
  };

  const handleActionClick = (path: string) => {
    navigate(path);
  };

  return (
    <>
      <Dialog
        open={showDialog}
        onClose={() => setShowDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PlayArrowIcon color="primary" />
            <Typography variant="h6">Welcome to RiskIntel360!</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Would you like a quick tour of the platform's key features?
          </Typography>
          <Typography variant="body2" color="textSecondary">
            This will take about 2 minutes and help you get started quickly.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleSkip}>
            Skip Tour
          </Button>
          <Button variant="contained" onClick={() => setShowDialog(false)}>
            Start Tour
          </Button>
        </DialogActions>
      </Dialog>

      <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h3" gutterBottom>
            Welcome to RiskIntel360
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Let's get you started with our AI-powered financial risk intelligence platform
          </Typography>
        </Box>

        <Grid container spacing={4}>
          <Grid item xs={12} md={4}>
            <Stepper activeStep={activeStep} orientation="vertical">
              {onboardingSteps.map((step, index) => (
                <Step key={step.label}>
                  <StepLabel
                    optional={
                      index === onboardingSteps.length - 1 ? (
                        <Typography variant="caption">Last step</Typography>
                      ) : null
                    }
                  >
                    {step.label}
                  </StepLabel>
                  <StepContent>
                    <Box sx={{ mb: 2 }}>
                      <Button
                        variant="contained"
                        onClick={handleNext}
                        sx={{ mt: 1, mr: 1 }}
                        disabled={index === onboardingSteps.length - 1}
                      >
                        {index === onboardingSteps.length - 1 ? 'Finish' : 'Continue'}
                      </Button>
                      <Button
                        disabled={index === 0}
                        onClick={handleBack}
                        sx={{ mt: 1, mr: 1 }}
                      >
                        Back
                      </Button>
                    </Box>
                  </StepContent>
                </Step>
              ))}
            </Stepper>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card elevation={3}>
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      bgcolor: 'primary.light',
                      color: 'primary.contrastText',
                    }}
                  >
                    {onboardingSteps[activeStep].icon}
                  </Box>
                </Box>

                <Typography variant="h4" gutterBottom align="center">
                  {onboardingSteps[activeStep].title}
                </Typography>

                <Typography variant="body1" paragraph align="center" color="textSecondary">
                  {onboardingSteps[activeStep].description}
                </Typography>

                <Box sx={{ my: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Key Features:
                  </Typography>
                  <List>
                    {onboardingSteps[activeStep].features.map((feature, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircleIcon color="success" />
                        </ListItemIcon>
                        <ListItemText primary={feature} />
                      </ListItem>
                    ))}
                  </List>
                </Box>

                {onboardingSteps[activeStep].action && (
                  <Box sx={{ textAlign: 'center', mt: 3 }}>
                    <Button
                      variant="outlined"
                      size="large"
                      onClick={() => handleActionClick(onboardingSteps[activeStep].action!.path)}
                    >
                      {onboardingSteps[activeStep].action?.label}
                    </Button>
                  </Box>
                )}

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                  <Button
                    onClick={handleSkip}
                    color="inherit"
                  >
                    Skip Tour
                  </Button>
                  <Box>
                    <Chip
                      label={`${activeStep + 1} of ${onboardingSteps.length}`}
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                  {activeStep === onboardingSteps.length - 1 ? (
                    <Button
                      variant="contained"
                      onClick={handleComplete}
                      endIcon={<CheckCircleIcon />}
                    >
                      Get Started
                    </Button>
                  ) : (
                    <Button
                      variant="contained"
                      onClick={handleNext}
                    >
                      Next
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </>
  );
};
