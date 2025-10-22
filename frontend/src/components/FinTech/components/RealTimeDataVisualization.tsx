/**
 * Real-time Data Visualization Component
 * Integrates with WebSocket for live updates and streaming data
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  Badge,
  Stack,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  SignalWifi4Bar as ConnectedIcon,
  SignalWifiOff as DisconnectedIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { InteractiveChart, ChartDataPoint } from './InteractiveChart';
import { useWebSocketUpdates } from '../hooks/useWebSocketUpdates';

export interface RealTimeDataPoint extends ChartDataPoint {
  timestamp: string;
  source: string;
  confidence?: number;
  alertLevel?: 'low' | 'medium' | 'high' | 'critical';
}

export interface RealTimeVisualizationProps {
  title: string;
  dataSource: string;
  chartType: 'line' | 'bar' | 'pie';
  maxDataPoints?: number;
  updateInterval?: number;
  enableAlerts?: boolean;
  alertThresholds?: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  onAlert?: (dataPoint: RealTimeDataPoint) => void;
  onDataUpdate?: (data: RealTimeDataPoint[]) => void;
}

export const RealTimeDataVisualization: React.FC<RealTimeVisualizationProps> = ({
  title,
  dataSource,
  chartType,
  maxDataPoints = 100,
  updateInterval = 5000,
  enableAlerts = true,
  alertThresholds = {
    low: 50,
    medium: 70,
    high: 85,
    critical: 95,
  },
  onAlert,
  onDataUpdate,
}) => {
  const theme = useTheme();
  const [data, setData] = useState<RealTimeDataPoint[]>([]);
  const [isStreaming, setIsStreaming] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [alertCount, setAlertCount] = useState(0);
  const [dataRate, setDataRate] = useState(0);
  const dataRateRef = useRef(0);
  const lastDataCountRef = useRef(0);

  // WebSocket integration
  const {
    isConnected,
    lastMessage,
    error: connectionError,
    connect,
    disconnect,
  } = useWebSocketUpdates(dataSource, {
    enabled: true,
    reconnectInterval: 5000,
  });

  // Update connection status based on WebSocket state
  useEffect(() => {
    if (isConnected) {
      setConnectionStatus('connected');
    } else if (connectionError) {
      setConnectionStatus('disconnected');
    } else {
      setConnectionStatus('connecting');
    }
  }, [isConnected, connectionError]);

  // Process incoming WebSocket messages
  useEffect(() => {
    if (lastMessage && isStreaming) {
      try {
        const newDataPoint: RealTimeDataPoint = lastMessage.data as RealTimeDataPoint;
        
        setData(prevData => {
          const updatedData = [...prevData, newDataPoint];
          
          // Keep only the most recent data points
          if (updatedData.length > maxDataPoints) {
            updatedData.splice(0, updatedData.length - maxDataPoints);
          }
          
          // Check for alerts
          if (enableAlerts && newDataPoint.y) {
            const alertLevel = getAlertLevel(newDataPoint.y);
            if (alertLevel !== 'low') {
              const alertDataPoint = { ...newDataPoint, alertLevel };
              onAlert?.(alertDataPoint);
              setAlertCount(prev => prev + 1);
            }
          }
          
          setLastUpdate(new Date());
          onDataUpdate?.(updatedData);
          
          return updatedData;
        });
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage, isStreaming, maxDataPoints, enableAlerts, onAlert, onDataUpdate]);

  // Calculate data rate
  useEffect(() => {
    const interval = setInterval(() => {
      const currentCount = data.length;
      const rate = currentCount - lastDataCountRef.current;
      setDataRate(rate);
      dataRateRef.current = rate;
      lastDataCountRef.current = currentCount;
    }, 1000);

    return () => clearInterval(interval);
  }, [data.length]);

  // Generate mock real-time data for demonstration
  useEffect(() => {
    if (!isConnected && isStreaming) {
      const interval = setInterval(() => {
        const mockDataPoint: RealTimeDataPoint = {
          x: new Date().toISOString(),
          y: Math.random() * 100,
          timestamp: new Date().toISOString(),
          source: dataSource,
          confidence: 0.8 + Math.random() * 0.2,
          metadata: {
            category: ['fraud', 'compliance', 'market', 'risk'][Math.floor(Math.random() * 4)],
            region: ['US', 'EU', 'APAC'][Math.floor(Math.random() * 3)],
          },
        };

        setData(prevData => {
          const updatedData = [...prevData, mockDataPoint];
          
          if (updatedData.length > maxDataPoints) {
            updatedData.splice(0, updatedData.length - maxDataPoints);
          }
          
          // Check for alerts
          if (enableAlerts) {
            const alertLevel = getAlertLevel(mockDataPoint.y);
            if (alertLevel !== 'low') {
              const alertDataPoint = { ...mockDataPoint, alertLevel };
              onAlert?.(alertDataPoint);
              setAlertCount(prev => prev + 1);
            }
          }
          
          setLastUpdate(new Date());
          onDataUpdate?.(updatedData);
          
          return updatedData;
        });
      }, updateInterval);

      return () => clearInterval(interval);
    }
  }, [isConnected, isStreaming, dataSource, maxDataPoints, updateInterval, enableAlerts, onAlert, onDataUpdate]);

  const getAlertLevel = (value: number): 'low' | 'medium' | 'high' | 'critical' => {
    if (value >= alertThresholds.critical) return 'critical';
    if (value >= alertThresholds.high) return 'high';
    if (value >= alertThresholds.medium) return 'medium';
    return 'low';
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical':
        return theme.palette.error.main;
      case 'high':
        return theme.palette.warning.main;
      case 'medium':
        return theme.palette.info.main;
      default:
        return theme.palette.success.main;
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return theme.palette.success.main;
      case 'disconnected':
        return theme.palette.error.main;
      default:
        return theme.palette.warning.main;
    }
  };

  const handleToggleStreaming = () => {
    setIsStreaming(!isStreaming);
    if (!isStreaming && connectionStatus === 'disconnected') {
      connect();
    }
  };

  const handleRefresh = () => {
    setData([]);
    setAlertCount(0);
    setLastUpdate(null);
    if (connectionStatus === 'disconnected') {
      connect();
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Convert data for chart display
  const chartData: ChartDataPoint[] = data.map((point, index) => ({
    x: formatTimestamp(point.timestamp),
    y: point.y,
    label: point.source,
    metadata: {
      ...point.metadata,
      confidence: point.confidence,
      alertLevel: point.alertLevel,
      fullTimestamp: point.timestamp,
    },
    drillDownData: data.slice(Math.max(0, index - 10), index + 1).map(p => ({
      x: formatTimestamp(p.timestamp),
      y: p.y,
      metadata: p.metadata,
    })),
  }));

  return (
    <Card>
      <CardContent>
        {/* Header with Controls */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="h3">
              {title}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
              <Chip
                icon={connectionStatus === 'connected' ? <ConnectedIcon /> : <DisconnectedIcon />}
                label={connectionStatus}
                size="small"
                sx={{ 
                  backgroundColor: getConnectionStatusColor(),
                  color: 'white',
                }}
              />
              <Chip
                icon={<SpeedIcon />}
                label={`${dataRate}/sec`}
                size="small"
                variant="outlined"
              />
              {lastUpdate && (
                <Typography variant="caption" color="textSecondary">
                  Last update: {lastUpdate.toLocaleTimeString()}
                </Typography>
              )}
            </Stack>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={isStreaming}
                  onChange={handleToggleStreaming}
                  color="primary"
                />
              }
              label="Live Updates"
            />
            
            <Tooltip title="Refresh Data">
              <IconButton onClick={handleRefresh}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            
            {enableAlerts && alertCount > 0 && (
              <Badge badgeContent={alertCount} color="error">
                <Chip
                  label="Alerts"
                  size="small"
                  color="error"
                  variant="outlined"
                />
              </Badge>
            )}
          </Box>
        </Box>

        {/* Connection Error Alert */}
        {connectionError && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            WebSocket connection error: {connectionError}. Using mock data for demonstration.
          </Alert>
        )}

        {/* Loading Indicator */}
        {connectionStatus === 'connecting' && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Connecting to real-time data stream...
            </Typography>
          </Box>
        )}

        {/* Real-time Chart */}
        {data.length > 0 ? (
          <InteractiveChart
            title=""
            data={chartData}
            chartType={chartType}
            library="recharts"
            height={400}
            enableDrillDown={true}
            enableExport={true}
            enableFullscreen={true}
            enableFiltering={true}
            colorScheme={[
              theme.palette.primary.main,
              theme.palette.secondary.main,
              theme.palette.success.main,
              theme.palette.warning.main,
              theme.palette.error.main,
            ]}
            onDataPointClick={(dataPoint, index) => {
              console.log('Real-time data point clicked:', dataPoint, index);
            }}
            onExport={(format) => {
              console.log('Exporting real-time data as:', format);
            }}
          />
        ) : (
          <Box sx={{ 
            height: 400, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            bgcolor: 'grey.50',
            borderRadius: 1,
          }}>
            <Typography variant="body1" color="textSecondary">
              {isStreaming ? 'Waiting for real-time data...' : 'Real-time updates paused'}
            </Typography>
          </Box>
        )}

        {/* Data Statistics */}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            {data.length} data points • {dataRate} updates/sec
          </Typography>
          <Stack direction="row" spacing={1}>
            {enableAlerts && Object.entries(alertThresholds).map(([level, threshold]) => (
              <Chip
                key={level}
                label={`${level}: >${threshold}`}
                size="small"
                variant="outlined"
                sx={{ 
                  borderColor: getAlertColor(level),
                  color: getAlertColor(level),
                }}
              />
            ))}
          </Stack>
        </Box>
      </CardContent>
    </Card>
  );
};

export default RealTimeDataVisualization;