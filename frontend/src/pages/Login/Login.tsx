import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  Paper,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email,
  Lock,
  BusinessCenter,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../../components/Common/LoadingSpinner';

const Login: React.FC = () => {
  const [email, setEmail] = useState('demo@riskintel360.com');
  const [password, setPassword] = useState('demo123');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        bgcolor="background.default"
      >
        <LoadingSpinner size={60} message="Signing you in..." />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={24}
          sx={{
            borderRadius: 3,
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              p: 4,
              textAlign: 'center',
            }}
          >
            <BusinessCenter sx={{ fontSize: 48, mb: 2 }} />
            <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
              RiskIntel360
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              AI-Powered Financial Risk Intelligence Platform
            </Typography>
          </Box>

          {/* Login Form */}
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" component="h2" textAlign="center" mb={3}>
              Sign In to Your Account
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} noValidate data-testid="login-form">
              <TextField
                fullWidth
                id="email"
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                margin="normal"
                required
                autoComplete="email"
                autoFocus
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email color="action" />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 2 }}
                data-testid="login-email-input"
              />

              <TextField
                fullWidth
                id="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                margin="normal"
                required
                autoComplete="current-password"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility for secure financial platform access"
                        onClick={handleTogglePasswordVisibility}
                        edge="end"
                        data-testid="login-password-visibility-toggle"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 3 }}
                data-testid="login-password-input"
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={isLoading || !email || !password}
                sx={{
                  mt: 2,
                  mb: 2,
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 'bold',
                }}
                data-testid="login-submit-button"
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </Button>
            </Box>

            {/* Demo Credentials */}
            <Card sx={{ mt: 3, bgcolor: 'grey.50' }}>
              <CardContent>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Demo Credentials (Recommended)
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  <strong>Email:</strong> demo@riskintel360.com<br />
                  <strong>Password:</strong> demo123<br />
                  <em>Full features with AWS integration</em>
                </Typography>
                
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Test Credentials
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Email:</strong> test<br />
                  <strong>Password:</strong> test<br />
                  <em>Basic functionality testing</em>
                </Typography>
              </CardContent>
            </Card>

            {/* Features */}
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                AI-powered fraud prevention, compliance automation, and risk assessment
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2, flexWrap: 'wrap' }}>
                <Typography variant="caption" color="text.secondary">
                  ✓ Fraud Prevention
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ✓ Compliance Automation
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ✓ Risk Assessment
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1, flexWrap: 'wrap' }}>
                <Typography variant="caption" color="text.secondary">
                  ✓ 90% Fraud Detection Accuracy
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ✓ Real-time Regulatory Monitoring
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ✓ Automated KYC Verification
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Paper>
      </Container>
    </Box>
  );
};

export default Login;