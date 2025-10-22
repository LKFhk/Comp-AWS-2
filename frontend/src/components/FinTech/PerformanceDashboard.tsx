/**
 * Performance Dashboard Component
 * System metrics and agent performance monitoring
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkCheckIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Timeline as TimelineIcon,
  Computer as ComputerIcon,
  CloudQueue as CloudQueueIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';
import { useWebSocketUpdates } from './hooks/useWebSocketUpdates';

interface PerformanceDashboardProps {
  refreshInterval?: number;
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkLatency: number;
  uptime: number;
  activeConnections: number;
  requestsPerSecond: number;
  errorRate: number;
}

interface AgentPerformance {
  agent_id: string;
  agent_type: string;
  status: 'active' | 'idle' | 'error' | 'maintenance';
  response_time: number;
  success_rate: number;
  requests_processed: number;
  last_activity: string;
  confidence_score: number;
  error_count: number;
}

interface PerformanceAlert {
  alert_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  component: string;
  message: string;
  timestamp: string;
  resolved: boolean;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  refreshInterval = 30000, // 30 seconds - prevents browser freeze
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [agentPerformance, setAgentPerformance] = useState<AgentPerformance[]>([]);
  const [performanceAlerts, setPerformanceAlerts] = useState<PerformanceAlert[]>([]);
  const [historicalData, setHistoricalData] = useState<any[]>([]);

  // WebSocket updates for real-time performance data
  const { isConnected, lastMessage } = useWebSocketUpdates('performance');

  // Fetch performance data
  const fetchPerformanceData = useCallback(async () => {
    try {
      setError(null);
      
      // Mock system metrics
      const mockSystemMetrics: SystemMetrics = {
        cpuUsage: Math.random() * 30 + 20, // 20-50%
        memoryUsage: Math.random() * 20 + 60, // 60-80%
        diskUsage: Math.random() * 10 + 45, // 45-55%
        networkLatency: Math.random() * 20 + 10, // 10-30ms
        uptime: 99.92, // 99.92% uptime
        activeConnections: Math.floor(Math.random() * 30) + 20, // 20-50 connections
        requestsPerSecond: Math.random() * 50 + 100, // 100-150 RPS
        errorRate: Math.random() * 0.5 + 0.1, // 0.1-0.6% error rate
      };

      setSystemMetrics(mockSystemMetrics);

      // Mock agent performance data
      const mockAgentPerformance: AgentPerformance[] = [
        {
          agent_id: 'regulatory-001',
          agent_type: 'Regulatory Compliance',
          status: 'active',
          response_time: Math.random() * 2 + 2, // 2-4 seconds
          success_rate: 98.5 + Math.random() * 1.5, // 98.5-100%
          requests_processed: Math.floor(Math.random() * 50) + 150,
          last_activity: new Date(Date.now() - Math.random() * 300000).toISOString(),
          confidence_score: 0.92 + Math.random() * 0.08, // 0.92-1.0
          error_count: Math.floor(Math.random() * 3),
        },
        {
          agent_id: 'fraud-002',
          agent_type: 'Fraud Detection',
          status: 'active',
          response_time: Math.random() * 1.5 + 1.5, // 1.5-3 seconds
          success_rate: 95.2 + Math.random() * 4.8, // 95.2-100%
          requests_processed: Math.floor(Math.random() * 100) + 200,
          last_activity: new Date(Date.now() - Math.random() * 180000).toISOString(),
          confidence_score: 0.89 + Math.random() * 0.11, // 0.89-1.0
          error_count: Math.floor(Math.random() * 5),
        },
        {
          agent_id: 'market-003',
          agent_type: 'Market Analysis',
          status: 'active',
          response_time: Math.random() * 2.5 + 2.5, // 2.5-5 seconds
          success_rate: 97.1 + Math.random() * 2.9, // 97.1-100%
          requests_processed: Math.floor(Math.random() * 40) + 80,
          last_activity: new Date(Date.now() - Math.random() * 240000).toISOString(),
          confidence_score: 0.85 + Math.random() * 0.15, // 0.85-1.0
          error_count: Math.floor(Math.random() * 2),
        },
        {
          agent_id: 'kyc-004',
          agent_type: 'KYC Verification',
          status: 'idle',
          response_time: Math.random() * 1 + 3, // 3-4 seconds
          success_rate: 99.1 + Math.random() * 0.9, // 99.1-100%
          requests_processed: Math.floor(Math.random() * 30) + 60,
          last_activity: new Date(Date.now() - Math.random() * 600000).toISOString(),
          confidence_score: 0.94 + Math.random() * 0.06, // 0.94-1.0
          error_count: Math.floor(Math.random() * 1),
        },
        {
          agent_id: 'risk-005',
          agent_type: 'Risk Assessment',
          status: 'active',
          response_time: Math.random() * 2 + 3, // 3-5 seconds
          success_rate: 96.8 + Math.random() * 3.2, // 96.8-100%
          requests_processed: Math.floor(Math.random() * 60) + 120,
          last_activity: new Date(Date.now() - Math.random() * 120000).toISOString(),
          confidence_score: 0.88 + Math.random() * 0.12, // 0.88-1.0
          error_count: Math.floor(Math.random() * 4),
        },
      ];

      setAgentPerformance(mockAgentPerformance);

      // Mock performance alerts
      const mockAlerts: PerformanceAlert[] = [
        {
          alert_id: 'PERF-001',
          severity: 'medium',
          component: 'Fraud Detection Agent',
          message: 'Response time slightly elevated (4.2s avg)',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          resolved: false,
        },
        {
          alert_id: 'PERF-002',
          severity: 'low',
          component: 'System Memory',
          message: 'Memory usage at 78% - within normal range',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          resolved: true,
        },
        {
          alert_id: 'PERF-003',
          severity: 'high',
          component: 'Network Latency',
          message: 'Network latency spike detected (45ms)',
          timestamp: new Date(Date.now() - 900000).toISOString(),
          resolved: true,
        },
      ];

      setPerformanceAlerts(mockAlerts);

      // Mock historical performance data
      const now = Date.now();
      const historicalMetrics = [];
      for (let i = 23; i >= 0; i--) {
        historicalMetrics.push({
          timestamp: new Date(now - i * 3600000).toISOString(),
          response_time: Math.random() * 2 + 2.5,
          success_rate: 95 + Math.random() * 5,
          cpu_usage: Math.random() * 20 + 25,
          memory_usage: Math.random() * 15 + 65,
          requests_per_second: Math.random() * 40 + 110,
        });
      }
      setHistoricalData(historicalMetrics);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch performance data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPerformanceData();
    const interval = setInterval(fetchPerformanceData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchPerformanceData, refreshInterval]);

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'performance_update') {
      // Update performance data from WebSocket
      console.log('Received performance update:', lastMessage.data);
    }
  }, [lastMessage]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.palette.success.main;
      case 'idle':
        return theme.palette.warning.main;
      case 'error':
        return theme.palette.error.main;
      case 'maintenance':
        return theme.palette.info.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon />;
      case 'idle':
        return <WarningIcon />;
      case 'error':
        return <ErrorIcon />;
      case 'maintenance':
        return <ComputerIcon />;
      default:
        return <ComputerIcon />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return theme.palette.error.main;
      case 'high':
        return theme.palette.error.light;
      case 'medium':
        return theme.palette.warning.main;
      case 'low':
        return theme.palette.info.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  if (loading) {
    return <LoadingState message="Loading performance metrics..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchPerformanceData}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  return (
    <ErrorBoundary>
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h3" component="h1" gutterBottom>
              Performance Dashboard
            </Typography>
            <Typography variant="subtitle1" color="textSecondary">
              System Metrics and Agent Performance Monitoring
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Chip 
                label={isConnected ? 'Real-time Updates' : 'Offline'}
                color={isConnected ? 'success' : 'error'}
                size="small"
              />
              <Chip 
                label={`${agentPerformance.filter(a => a.status === 'active').length} Active Agents`}
                color="primary"
                size="small"
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh Metrics">
              <IconButton onClick={fetchPerformanceData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => console.log('Export performance report')}
            >
              Export Report
            </Button>
          </Box>
        </Box>

        {/* System Health Overview */}
        {systemMetrics && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <SpeedIcon color="primary" />
                    <Typography variant="h6">CPU Usage</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <CircularProgress
                      variant="determinate"
                      value={systemMetrics.cpuUsage}
                      size={60}
                      thickness={4}
                      sx={{ color: systemMetrics.cpuUsage > 80 ? theme.palette.error.main : theme.palette.primary.main }}
                    />
                    <Box>
                      <Typography variant="h5">
                        {systemMetrics.cpuUsage.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Normal range
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <MemoryIcon color="info" />
                    <Typography variant="h6">Memory Usage</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <CircularProgress
                      variant="determinate"
                      value={systemMetrics.memoryUsage}
                      size={60}
                      thickness={4}
                      sx={{ color: systemMetrics.memoryUsage > 90 ? theme.palette.error.main : theme.palette.info.main }}
                    />
                    <Box>
                      <Typography variant="h5">
                        {systemMetrics.memoryUsage.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Optimal
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <NetworkCheckIcon color="success" />
                    <Typography variant="h6">Network Latency</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {systemMetrics.networkLatency.toFixed(0)}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        ms
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        Excellent
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        &lt; 50ms target
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <CloudQueueIcon color="warning" />
                    <Typography variant="h6">System Uptime</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {systemMetrics.uptime.toFixed(2)}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        %
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        Excellent
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        99.9% target met
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Request Metrics */}
        {systemMetrics && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Request Metrics
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Requests per Second
                    </Typography>
                    <Typography variant="h4" color="primary.main">
                      {systemMetrics.requestsPerSecond.toFixed(0)}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Active Connections
                    </Typography>
                    <Typography variant="h5" color="info.main">
                      {systemMetrics.activeConnections}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Error Rate
                    </Typography>
                    <Typography variant="h5" color={systemMetrics.errorRate > 1 ? "error.main" : "success.main"}>
                      {systemMetrics.errorRate.toFixed(2)}%
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Agent Performance Overview
                  </Typography>
                  <Grid container spacing={2}>
                    {agentPerformance.slice(0, 4).map((agent) => (
                      <Grid item xs={12} sm={6} key={agent.agent_id}>
                        <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Avatar sx={{ 
                              bgcolor: getStatusColor(agent.status), 
                              width: 24, 
                              height: 24 
                            }}>
                              {getStatusIcon(agent.status)}
                            </Avatar>
                            <Typography variant="subtitle2">
                              {agent.agent_type}
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="textSecondary">
                            Response: {agent.response_time.toFixed(1)}s | Success: {agent.success_rate.toFixed(1)}%
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={agent.success_rate}
                            sx={{ mt: 1, height: 4, borderRadius: 2 }}
                          />
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Detailed Agent Performance */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Detailed Agent Performance
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Agent</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="right">Response Time</TableCell>
                        <TableCell align="right">Success Rate</TableCell>
                        <TableCell align="right">Requests</TableCell>
                        <TableCell align="right">Confidence</TableCell>
                        <TableCell align="right">Errors</TableCell>
                        <TableCell>Last Activity</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {agentPerformance.map((agent) => (
                        <TableRow key={agent.agent_id}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {agent.agent_type === 'Regulatory Compliance' && <AssessmentIcon color="primary" />}
                              {agent.agent_type === 'Fraud Detection' && <SecurityIcon color="error" />}
                              {agent.agent_type === 'Market Analysis' && <TrendingUpIcon color="success" />}
                              {agent.agent_type === 'KYC Verification' && <PersonIcon color="info" />}
                              {agent.agent_type === 'Risk Assessment' && <TimelineIcon color="warning" />}
                              <Box>
                                <Typography variant="body2" fontWeight="medium">
                                  {agent.agent_type}
                                </Typography>
                                <Typography variant="caption" color="textSecondary">
                                  {agent.agent_id}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={agent.status}
                              size="small"
                              sx={{
                                backgroundColor: getStatusColor(agent.status),
                                color: 'white',
                              }}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography 
                              variant="body2" 
                              color={agent.response_time > 5 ? "error.main" : "textPrimary"}
                            >
                              {agent.response_time.toFixed(1)}s
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography 
                              variant="body2" 
                              color={agent.success_rate < 95 ? "warning.main" : "success.main"}
                            >
                              {agent.success_rate.toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {agent.requests_processed.toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" color="primary.main">
                              {(agent.confidence_score * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography 
                              variant="body2" 
                              color={agent.error_count > 5 ? "error.main" : "textPrimary"}
                            >
                              {agent.error_count}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="textSecondary">
                              {new Date(agent.last_activity).toLocaleString()}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Performance Alerts */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Alerts
                </Typography>
                <List>
                  {performanceAlerts.map((alert, index) => (
                    <React.Fragment key={alert.alert_id}>
                      <ListItem>
                        <ListItemIcon>
                          <Avatar sx={{ 
                            bgcolor: getSeverityColor(alert.severity), 
                            width: 32, 
                            height: 32 
                          }}>
                            {alert.resolved ? <CheckCircleIcon /> : <WarningIcon />}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primaryTypographyProps={{ component: 'div' }}
                          secondaryTypographyProps={{ component: 'div' }}
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body1">
                                {alert.component}
                              </Typography>
                              <Chip
                                label={alert.severity}
                                size="small"
                                sx={{
                                  backgroundColor: getSeverityColor(alert.severity),
                                  color: 'white',
                                }}
                              />
                              {alert.resolved && (
                                <Chip
                                  label="Resolved"
                                  size="small"
                                  color="success"
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="textSecondary">
                                {alert.message}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {new Date(alert.timestamp).toLocaleString()}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < performanceAlerts.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </ErrorBoundary>
  );
};

export default PerformanceDashboard;