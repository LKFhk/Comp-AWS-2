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
  ListItemIcon,
  ListItemText,
  Divider,
  Link,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  Launch as LaunchIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { credentialsService, ExternalAPIKey } from '../../../services/credentialsService';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../../components/Common/LoadingSpinner';

interface ExternalAPIKeysSetupProps {
  onCredentialsUpdated: () => void;
  configuredServices: string[];
}

const ExternalAPIKeysSetup: React.FC<ExternalAPIKeysSetupProps> = ({
  onCredentialsUpdated,
  configuredServices,
}) => {
  const [selectedService, setSelectedService] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [endpointUrl, setEndpointUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const { showNotification } = useNotification();

  const availableServices = [
    {
      id: 'alpha_vantage',
      name: 'Alpha Vantage',
      description: 'Financial market data and stock prices',
      website: 'https://www.alphavantage.co/',
      icon: '📈',
      required: false,
      category: 'Financial Data',
    },
    {
      id: 'news_api',
      name: 'News API',
      description: 'Global news articles and headlines',
      website: 'https://newsapi.org/',
      icon: '📰',
      required: false,
      category: 'News & Media',
    },
    {
      id: 'twitter_api',
      name: 'Twitter API',
      description: 'Social media sentiment and trends',
      website: 'https://developer.twitter.com/',
      icon: '🐦',
      required: false,
      category: 'Social Media',
    },
    {
      id: 'reddit_api',
      name: 'Reddit API',
      description: 'Community discussions and sentiment',
      website: 'https://www.reddit.com/dev/api/',
      icon: '🔴',
      required: false,
      category: 'Social Media',
    },
    {
      id: 'crunchbase',
      name: 'Crunchbase',
      description: 'Company and startup information',
      website: 'https://data.crunchbase.com/',
      icon: '🏢',
      required: false,
      category: 'Business Intelligence',
    },
    {
      id: 'pitchbook',
      name: 'PitchBook',
      description: 'Private market intelligence',
      website: 'https://pitchbook.com/',
      icon: '💼',
      required: false,
      category: 'Business Intelligence',
    },
  ];

  const handleServiceChange = (event: any) => {
    setSelectedService(event.target.value);
    setApiKey('');
    setEndpointUrl('');
    setError('');
    setSuccess('');
  };

  const handleSetupAPIKey = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      if (!selectedService || !apiKey) {
        setError('Please select a service and enter an API key');
        return;
      }

      const apiKeyData: ExternalAPIKey = {
        service_name: selectedService,
        api_key: apiKey,
        endpoint_url: endpointUrl || undefined,
      };

      // Client-side validation
      const validationErrors = credentialsService.validateExternalAPIKey(apiKeyData);
      if (validationErrors.length > 0) {
        setError(validationErrors.join(', '));
        return;
      }

      // Setup API key
      const result = await credentialsService.setupExternalAPIKey(apiKeyData);

      if (result.valid) {
        setSuccess(`${credentialsService.getServiceDisplayName(selectedService)} API key configured successfully!`);
        showNotification('API key configured successfully', 'success');
        onCredentialsUpdated();
        
        // Reset form
        setSelectedService('');
        setApiKey('');
        setEndpointUrl('');
      } else {
        setError(result.error_message || 'API key validation failed');
      }
    } catch (err: any) {
      console.error('Failed to setup API key:', err);
      setError(err.message || 'Failed to setup API key');
    } finally {
      setLoading(false);
    }
  };

  const getServicesByCategory = () => {
    const categories: Record<string, typeof availableServices> = {};
    availableServices.forEach(service => {
      if (!categories[service.category]) {
        categories[service.category] = [];
      }
      categories[service.category].push(service);
    });
    return categories;
  };

  const getSelectedServiceInfo = () => {
    return availableServices.find(service => service.id === selectedService);
  };

  const isServiceConfigured = (serviceId: string) => {
    return configuredServices.includes(serviceId);
  };

  const unconfiguredServices = availableServices.filter(
    service => !isServiceConfigured(service.id)
  );

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        External API Keys Setup
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure external API keys to enhance the RiskIntel360 platform with additional data sources.
        These APIs are optional but provide richer analysis capabilities.
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

      {/* Configured Services Summary */}
      {configuredServices.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configured Services ({configuredServices.length})
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {configuredServices.map((serviceId) => {
                const service = availableServices.find(s => s.id === serviceId);
                return (
                  <Chip
                    key={serviceId}
                    icon={<CheckIcon />}
                    label={service ? service.name : serviceId}
                    color="success"
                    variant="outlined"
                  />
                );
              })}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Add New API Key */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Add New API Key
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Select Service</InputLabel>
                <Select
                  value={selectedService}
                  label="Select Service"
                  onChange={handleServiceChange}
                >
                  {unconfiguredServices.map((service) => (
                    <MenuItem key={service.id} value={service.id}>
                      <Box display="flex" alignItems="center" component="div">
                        <Box component="span" sx={{ mr: 1, fontSize: '1rem' }}>{service.icon}</Box>
                        <Box component="div">
                          <Box component="div" sx={{ fontSize: '1rem', fontWeight: 400 }}>{service.name}</Box>
                          <Box component="div" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                            {service.description}
                          </Box>
                        </Box>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {selectedService && (
              <>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="API Key"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your API key"
                    helperText="Your API key will be encrypted and stored securely for financial data access"
                    required
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Custom Endpoint URL (Optional)"
                    value={endpointUrl}
                    onChange={(e) => setEndpointUrl(e.target.value)}
                    placeholder="https://api.example.com"
                    helperText="Leave empty to use the default financial data endpoint"
                  />
                </Grid>

                {getSelectedServiceInfo() && (
                  <Grid item xs={12}>
                    <Alert severity="info">
                      <Typography variant="body2">
                        <strong>{getSelectedServiceInfo()!.name}:</strong> {getSelectedServiceInfo()!.description}
                      </Typography>
                      <Link
                        href={getSelectedServiceInfo()!.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ display: 'inline-flex', alignItems: 'center', mt: 1 }}
                      >
                        Get API Key <LaunchIcon fontSize="small" sx={{ ml: 0.5 }} />
                      </Link>
                    </Alert>
                  </Grid>
                )}
              </>
            )}
          </Grid>

          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              startIcon={loading ? <LoadingSpinner size={20} /> : <AddIcon />}
              onClick={handleSetupAPIKey}
              disabled={loading || !selectedService || !apiKey}
            >
              {loading ? 'Setting up...' : 'Setup API Key'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Available Services Information */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Available External Services
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            These external APIs enhance the RiskIntel360 platform with additional data sources.
            All services are optional and the platform will work with fallback data if APIs are not configured.
          </Typography>

          {Object.entries(getServicesByCategory()).map(([category, services]) => (
            <Accordion key={category} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">{category}</Typography>
                <Chip
                  label={`${services.filter(s => isServiceConfigured(s.id)).length}/${services.length} configured`}
                  size="small"
                  sx={{ ml: 2 }}
                />
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {services.map((service, index) => (
                    <React.Fragment key={service.id}>
                      <ListItem>
                        <ListItemIcon>
                          <Typography fontSize="1.5rem">{service.icon}</Typography>
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box display="flex" alignItems="center">
                              <Typography variant="body1">{service.name}</Typography>
                              {isServiceConfigured(service.id) && (
                                <Chip
                                  icon={<CheckIcon />}
                                  label="Configured"
                                  color="success"
                                  size="small"
                                  sx={{ ml: 1 }}
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {service.description}
                              </Typography>
                              <Link
                                href={service.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{ display: 'inline-flex', alignItems: 'center', mt: 0.5 }}
                              >
                                Learn more <LaunchIcon fontSize="small" sx={{ ml: 0.5 }} />
                              </Link>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < services.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          ))}
        </CardContent>
      </Card>

      {/* Information Box */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>Note:</strong> External APIs are optional. The RiskIntel360 platform uses AI-generated
          fallback data when external APIs are not available, ensuring the system always works.
          However, real API data provides more accurate and up-to-date analysis results.
        </Typography>
      </Alert>
    </Box>
  );
};

export default ExternalAPIKeysSetup;