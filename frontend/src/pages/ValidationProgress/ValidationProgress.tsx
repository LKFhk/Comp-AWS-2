import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,

} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as PendingIcon,
  PlayCircle as RunningIcon,
  Error as ErrorIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
// import { useAuth } from '../../contexts/AuthContext'; // Currently unused
import { useNotification } from '../../contexts/NotificationContext';
import { apiService, ValidationResponse, ProgressUpdate } from '../../services/api';
import { websocketService } from '../../services/websocket';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import ProgressBar from '../../components/Common/ProgressBar';

interface AgentStatus {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  startTime?: Date;
  endTime?: Date;
  result?: any;
}

const ValidationProgress: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([
    { name: 'Regulatory Compliance', status: 'pending', progress: 0 },
    { name: 'Risk Assessment', status: 'pending', progress: 0 },
    { name: 'Market Analysis', status: 'pending', progress: 0 },
    { name: 'Customer Behavior Intelligence', status: 'pending', progress: 0 },
    { name: 'Fraud Detection', status: 'pending', progress: 0 },
    { name: 'KYC Verification', status: 'pending', progress: 0 },
  ]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [startTime] = useState(new Date());
  
  const navigate = useNavigate();
  // const { user } = useAuth(); // Currently unused
  const { showNotification } = useNotification();

  const loadValidationData = useCallback(async () => {
    try {
      setError('');
      const validationData = await apiService.getValidation(id!);
      setValidation(validationData);
      
      // Try to get current progress
      try {
        const progressData = await apiService.getValidationProgress(id!);
        setProgress(progressData);
        updateAgentStatuses(progressData);
      } catch (progressError) {
        // Progress endpoint might not be available yet
        console.log('Progress data not available yet');
      }
      
    } catch (err: any) {
      console.error('Failed to load risk analysis data:', err);
      setError('Failed to load financial risk analysis progress data. Please try again.');
      showNotification('Failed to load financial risk analysis progress', 'error');
    } finally {
      setLoading(false);
    }
  }, [id, showNotification]);

  const connectToProgressUpdates = useCallback(() => {
    // WebSocket disabled in development - use polling instead
    // TODO: Enable WebSocket when backend WebSocket server is ready
    
    // const token = localStorage.getItem('auth_token');
    // if (token && id) {
    //   websocketService.connectToValidationProgress(id, token, (update) => {
    //     setProgress(update);
    //     updateAgentStatuses(update);
    //     
    //     if (update.status === 'completed') {
    //       showNotification('Financial risk analysis complete! View your comprehensive intelligence report.', 'success');
    //       setTimeout(() => {
    //         navigate(`/validation/${id}/results`);
    //       }, 2000);
    //     } else if (update.status === 'failed') {
    //       showNotification('Financial risk analysis failed. Please try again.', 'error');
    //     }
    //   });
    // }
  }, [id, navigate, showNotification]);

  useEffect(() => {
    if (id) {
      loadValidationData();
      // connectToProgressUpdates(); // Disabled - using polling instead
    }

    return () => {
      websocketService.disconnect();
    };
  }, [id, loadValidationData, connectToProgressUpdates]);

  const updateAgentStatuses = (progressUpdate: ProgressUpdate) => {
    setAgentStatuses(prevStatuses => {
      const newStatuses = [...prevStatuses];
      
      // Update based on current agent and overall progress
      const currentAgentIndex = newStatuses.findIndex(
        agent => agent.name.toLowerCase().replace(/\s+/g, '_') === progressUpdate.current_agent
      );
      
      // Mark previous agents as completed
      for (let i = 0; i < currentAgentIndex; i++) {
        if (newStatuses[i].status !== 'completed') {
          newStatuses[i].status = 'completed';
          newStatuses[i].progress = 100;
          newStatuses[i].endTime = new Date();
        }
      }
      
      // Update current agent
      if (currentAgentIndex >= 0) {
        newStatuses[currentAgentIndex].status = 'running';
        newStatuses[currentAgentIndex].progress = Math.min(
          (progressUpdate.progress_percentage / newStatuses.length) * 100,
          100
        );
        newStatuses[currentAgentIndex].message = progressUpdate.message;
        if (!newStatuses[currentAgentIndex].startTime) {
          newStatuses[currentAgentIndex].startTime = new Date();
        }
      }
      
      // If validation is completed, mark all as completed
      if (progressUpdate.status === 'completed') {
        newStatuses.forEach(agent => {
          agent.status = 'completed';
          agent.progress = 100;
          if (!agent.endTime) {
            agent.endTime = new Date();
          }
        });
      }
      
      return newStatuses;
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'running':
        return <RunningIcon color="primary" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <PendingIcon color="disabled" />;
    }
  };

  const getOverallProgress = () => {
    const completedAgents = agentStatuses.filter(agent => agent.status === 'completed').length;
    const runningAgents = agentStatuses.filter(agent => agent.status === 'running');
    
    let totalProgress = (completedAgents / agentStatuses.length) * 100;
    
    if (runningAgents.length > 0) {
      const runningProgress = runningAgents.reduce((sum, agent) => sum + agent.progress, 0);
      totalProgress += (runningProgress / 100) * (1 / agentStatuses.length) * 100;
    }
    
    return Math.min(totalProgress, 100);
  };

  const getEstimatedTimeRemaining = () => {
    const elapsed = (new Date().getTime() - startTime.getTime()) / 1000 / 60; // minutes
    const overallProgress = getOverallProgress();
    
    if (overallProgress === 0) return 'Initializing financial risk analysis...';
    if (overallProgress === 100) return 'Financial risk analysis completed';
    
    const estimatedTotal = (elapsed / overallProgress) * 100;
    const remaining = estimatedTotal - elapsed;
    
    if (remaining < 1) return 'Less than 1 minute';
    if (remaining < 60) return `${Math.round(remaining)} minutes`;
    
    const hours = Math.floor(remaining / 60);
    const minutes = Math.round(remaining % 60);
    return `${hours}h ${minutes}m`;
  };

  if (loading) {
    return <LoadingSpinner size={60} message="Loading risk analysis progress..." />;
  }

  if (!validation) {
    return (
      <Alert severity="error">
        Risk analysis not found or you don't have permission to view it.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          Risk Analysis Progress
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Real-time monitoring of your financial risk intelligence analysis
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Overall Progress */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={8}>
          <ProgressBar
            value={getOverallProgress()}
            label="Overall Progress"
            status={validation.status}
            currentAgent={progress?.current_agent}
            message={progress?.message}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <TimelineIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Time Remaining</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {getEstimatedTimeRemaining()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Started {format(new Date(validation.created_at), 'HH:mm')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Validation Details */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Financial Institution
              </Typography>
              <Typography variant="body2" paragraph>
                {validation.business_concept}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Regulatory Jurisdiction
              </Typography>
              <Typography variant="body2">
                {validation.target_market}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Configuration
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                {validation.analysis_scope.map((scope) => (
                  <Chip
                    key={scope}
                    label={scope.charAt(0).toUpperCase() + scope.slice(1)}
                    color="primary"
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box display="flex" alignItems="center" gap={1}>
                <SpeedIcon color="action" />
                <Typography variant="body2">
                  Priority: <strong>{validation.priority.charAt(0).toUpperCase() + validation.priority.slice(1)}</strong>
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Agent Status */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            AI Agent Progress
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Our specialized AI agents are working on different aspects of your risk analysis
          </Typography>
          
          <List>
            {agentStatuses.map((agent, index) => (
              <React.Fragment key={agent.name}>
                <ListItem>
                  <ListItemIcon>
                    {getStatusIcon(agent.status)}
                  </ListItemIcon>
                  <ListItemText
                    primaryTypographyProps={{ component: 'div' }}
                    secondaryTypographyProps={{ component: 'div' }}
                    primary={
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle1">
                          {agent.name}
                        </Typography>
                        <Chip
                          label={agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                          color={
                            agent.status === 'completed' ? 'success' :
                            agent.status === 'running' ? 'primary' :
                            agent.status === 'failed' ? 'error' : 'default'
                          }
                          size="small"
                        />
                      </Box>
                    }
                    secondary={
                      <React.Fragment>
                        {agent.message && (
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 1 }}>
                            {agent.message}
                          </Typography>
                        )}
                        {agent.status === 'running' && (
                          <Box sx={{ mt: 1 }}>
                            <ProgressBar
                              value={agent.progress}
                              showPercentage={false}
                              color="primary"
                            />
                          </Box>
                        )}
                        {agent.startTime && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            {agent.status === 'completed' && agent.endTime
                              ? `Completed in ${Math.round((agent.endTime.getTime() - agent.startTime.getTime()) / 1000 / 60)} minutes`
                              : `Started ${format(agent.startTime, 'HH:mm')}`
                            }
                          </Typography>
                        )}
                      </React.Fragment>
                    }
                  />
                </ListItem>
                {index < agentStatuses.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <Box mt={4} display="flex" justifyContent="space-between">
        <Button
          variant="outlined"
          onClick={() => navigate('/dashboard')}
        >
          Back to Dashboard
        </Button>
        {validation.status === 'completed' && (
          <Button
            variant="contained"
            startIcon={<AssessmentIcon />}
            onClick={() => navigate(`/validation/${id}/results`)}
          >
            View Results
          </Button>
        )}
      </Box>
    </Box>
  );
};

export default ValidationProgress;