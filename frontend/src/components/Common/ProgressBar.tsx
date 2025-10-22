import React from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Card,
  CardContent,
  Chip,
} from '@mui/material';

interface ProgressBarProps {
  value: number;
  label?: string;
  status?: string;
  currentAgent?: string;
  message?: string;
  showPercentage?: boolean;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  status,
  currentAgent,
  message,
  showPercentage = true,
  color = 'primary',
}) => {
  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'failed':
      case 'error':
        return 'error';
      case 'running':
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatAgentName = (agentName?: string) => {
    if (!agentName) return '';
    return agentName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <Card elevation={1}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          {label && (
            <Typography variant="subtitle2" color="text.primary">
              {label}
            </Typography>
          )}
          {status && (
            <Chip
              label={status.charAt(0).toUpperCase() + status.slice(1)}
              color={getStatusColor(status) as any}
              size="small"
            />
          )}
        </Box>

        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Box width="100%" mr={1}>
            <LinearProgress
              variant="determinate"
              value={Math.min(Math.max(value, 0), 100)}
              color={color}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                },
              }}
            />
          </Box>
          {showPercentage && (
            <Box minWidth={35}>
              <Typography variant="body2" color="text.secondary">
                {Math.round(value)}%
              </Typography>
            </Box>
          )}
        </Box>

        {currentAgent && (
          <Box mb={1}>
            <Typography variant="caption" color="text.secondary">
              Current Agent: <strong>{formatAgentName(currentAgent)}</strong>
            </Typography>
          </Box>
        )}

        {message && (
          <Typography variant="body2" color="text.secondary">
            {message}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default ProgressBar;