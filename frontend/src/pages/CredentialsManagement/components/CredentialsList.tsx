import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Tooltip,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Visibility as VisibilityIcon,
  CloudQueue as CloudIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { credentialsService, ConfiguredServices } from '../../../services/credentialsService';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../../components/Common/LoadingSpinner';

interface CredentialsListProps {
  configuredServices: ConfiguredServices;
  onCredentialsUpdated: () => void;
}

const CredentialsList: React.FC<CredentialsListProps> = ({
  configuredServices,
  onCredentialsUpdated,
}) => {
  const [validatingService, setValidatingService] = useState<string | null>(null);
  const [deletingService, setDeletingService] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [serviceToDelete, setServiceToDelete] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<Record<string, any>>({});
  const [error, setError] = useState('');

  const { showNotification } = useNotification();

  const handleValidateCredentials = async (serviceName: string) => {
    try {
      setValidatingService(serviceName);
      setError('');

      const result = await credentialsService.validateServiceCredentials(serviceName);
      setValidationResults({
        ...validationResults,
        [serviceName]: result,
      });

      if (result.valid) {
        showNotification(`${credentialsService.getServiceDisplayName(serviceName)} credentials are valid`, 'success');
      } else {
        showNotification(`${credentialsService.getServiceDisplayName(serviceName)} validation failed`, 'error');
      }
    } catch (err: any) {
      console.error(`Failed to validate ${serviceName}:`, err);
      setError(`Failed to validate ${serviceName}: ${err.message}`);
    } finally {
      setValidatingService(null);
    }
  };

  const handleDeleteCredentials = async (serviceName: string) => {
    try {
      setDeletingService(serviceName);
      setError('');

      await credentialsService.deleteServiceCredentials(serviceName);
      showNotification(`${credentialsService.getServiceDisplayName(serviceName)} credentials deleted`, 'success');
      onCredentialsUpdated();

      // Remove from validation results
      const newResults = { ...validationResults };
      delete newResults[serviceName];
      setValidationResults(newResults);
    } catch (err: any) {
      console.error(`Failed to delete ${serviceName}:`, err);
      setError(`Failed to delete ${serviceName}: ${err.message}`);
    } finally {
      setDeletingService(null);
      setDeleteDialogOpen(false);
      setServiceToDelete(null);
    }
  };

  const openDeleteDialog = (serviceName: string) => {
    setServiceToDelete(serviceName);
    setDeleteDialogOpen(true);
  };

  const closeDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setServiceToDelete(null);
  };

  const getServiceIcon = (serviceName: string) => {
    if (['aws', 'bedrock'].includes(serviceName)) {
      return <CloudIcon color="primary" />;
    }
    return <SecurityIcon color="primary" />;
  };

  const getValidationStatus = (serviceName: string) => {
    const result = validationResults[serviceName];
    if (!result) return null;

    return result.valid ? (
      <Chip
        icon={<CheckIcon />}
        label="Valid"
        color="success"
        size="small"
      />
    ) : (
      <Chip
        icon={<ErrorIcon />}
        label="Invalid"
        color="error"
        size="small"
      />
    );
  };

  const allServices = [
    ...configuredServices.aws_services,
    ...configuredServices.external_services,
  ];

  if (allServices.length === 0) {
    return (
      <Box>
        <Typography variant="h5" gutterBottom>
          Configured Services
        </Typography>
        
        <Card>
          <CardContent>
            <Box
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              minHeight={200}
              color="text.secondary"
            >
              <SecurityIcon fontSize="large" sx={{ mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Services Configured
              </Typography>
              <Typography variant="body2" textAlign="center">
                You haven't configured any services yet. Use the AWS Setup or External APIs tabs
                to add your credentials and start using the RiskIntel360 platform.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Configured Services
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage your configured credentials and validate their status.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* AWS Services */}
        {configuredServices.aws_services.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AWS Services ({configuredServices.aws_services.length})
                </Typography>
                
                <List>
                  {configuredServices.aws_services.map((serviceName, index) => (
                    <React.Fragment key={serviceName}>
                      <ListItem>
                        <ListItemIcon>
                          {getServiceIcon(serviceName)}
                        </ListItemIcon>
                        <ListItemText
                          primary={credentialsService.getServiceDisplayName(serviceName)}
                          secondary={
                            <Box display="flex" alignItems="center" gap={1} sx={{ mt: 0.5 }}>
                              {getValidationStatus(serviceName)}
                              {validationResults[serviceName]?.region && (
                                <Chip
                                  label={validationResults[serviceName].region}
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <Tooltip title="Validate AWS credentials for financial data access">
                            <IconButton
                              edge="end"
                              onClick={() => handleValidateCredentials(serviceName)}
                              disabled={validatingService === serviceName}
                              sx={{ mr: 1 }}
                            >
                              {validatingService === serviceName ? (
                                <LoadingSpinner size={20} />
                              ) : (
                                <RefreshIcon />
                              )}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete AWS credentials">
                            <IconButton
                              edge="end"
                              onClick={() => openDeleteDialog(serviceName)}
                              disabled={deletingService === serviceName}
                              color="error"
                            >
                              {deletingService === serviceName ? (
                                <LoadingSpinner size={20} />
                              ) : (
                                <DeleteIcon />
                              )}
                            </IconButton>
                          </Tooltip>
                        </ListItemSecondaryAction>
                      </ListItem>
                      {index < configuredServices.aws_services.length - 1 && <Box sx={{ borderBottom: 1, borderColor: 'divider', mx: 2 }} />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* External Services */}
        {configuredServices.external_services.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  External APIs ({configuredServices.external_services.length})
                </Typography>
                
                <List>
                  {configuredServices.external_services.map((serviceName, index) => (
                    <React.Fragment key={serviceName}>
                      <ListItem>
                        <ListItemIcon>
                          <Typography fontSize="1.5rem">
                            {credentialsService.getServiceIcon(serviceName)}
                          </Typography>
                        </ListItemIcon>
                        <ListItemText
                          primary={credentialsService.getServiceDisplayName(serviceName)}
                          secondary={
                            <Box display="flex" alignItems="center" gap={1} sx={{ mt: 0.5 }}>
                              {getValidationStatus(serviceName)}
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <Tooltip title="Validate financial data API key">
                            <IconButton
                              edge="end"
                              onClick={() => handleValidateCredentials(serviceName)}
                              disabled={validatingService === serviceName}
                              sx={{ mr: 1 }}
                            >
                              {validatingService === serviceName ? (
                                <LoadingSpinner size={20} />
                              ) : (
                                <RefreshIcon />
                              )}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete financial data API key">
                            <IconButton
                              edge="end"
                              onClick={() => openDeleteDialog(serviceName)}
                              disabled={deletingService === serviceName}
                              color="error"
                            >
                              {deletingService === serviceName ? (
                                <LoadingSpinner size={20} />
                              ) : (
                                <DeleteIcon />
                              )}
                            </IconButton>
                          </Tooltip>
                        </ListItemSecondaryAction>
                      </ListItem>
                      {index < configuredServices.external_services.length - 1 && <Box sx={{ borderBottom: 1, borderColor: 'divider', mx: 2 }} />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Validation Results Details */}
        {Object.keys(validationResults).length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Validation Details
                </Typography>
                
                {Object.entries(validationResults).map(([serviceName, result]) => (
                  <Box key={serviceName} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      {credentialsService.getServiceDisplayName(serviceName)}
                    </Typography>
                    
                    {result.valid ? (
                      <Alert severity="success" sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          ✅ Credentials are valid and working
                        </Typography>
                        {result.permissions && result.permissions.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              Permissions:
                            </Typography>
                            <Box display="flex" flexWrap="wrap" gap={0.5} sx={{ mt: 0.5 }}>
                              {result.permissions.map((permission: string) => (
                                <Chip
                                  key={permission}
                                  label={permission}
                                  size="small"
                                  variant="outlined"
                                />
                              ))}
                            </Box>
                          </Box>
                        )}
                      </Alert>
                    ) : (
                      <Alert severity="error" sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          ❌ {result.error_message || 'Credential validation failed'}
                        </Typography>
                      </Alert>
                    )}
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={closeDeleteDialog}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Delete Credentials
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete the credentials for{' '}
            <strong>
              {serviceToDelete ? credentialsService.getServiceDisplayName(serviceToDelete) : ''}
            </strong>?
            This action cannot be undone and you'll need to reconfigure the service to use it again.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteDialog}>Cancel</Button>
          <Button
            onClick={() => serviceToDelete && handleDeleteCredentials(serviceToDelete)}
            color="error"
            variant="contained"
            disabled={deletingService !== null}
          >
            {deletingService ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Information */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <strong>Security:</strong> All credentials are encrypted at rest and never logged.
          Validation checks verify that your credentials are working without exposing sensitive information.
          You can safely delete and reconfigure credentials at any time.
        </Typography>
      </Alert>
    </Box>
  );
};

export default CredentialsList;