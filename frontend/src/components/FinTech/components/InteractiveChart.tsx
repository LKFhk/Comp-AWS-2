/**
 * Interactive Chart Component with drill-down capabilities
 * Supports Chart.js and Recharts with advanced interactivity
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  Chip,
  Stack,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  ZoomIn as ZoomInIcon,
  Download as DownloadIcon,
  Fullscreen as FullscreenIcon,
  FilterList as FilterListIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ChartOptions,
  ChartData,
  InteractionItem,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import {
  ResponsiveContainer,
  LineChart,
  BarChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend,
  Line as RechartsLine,
  Bar as RechartsBar,
  Cell,
  PieChart,
  Pie,
} from 'recharts';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend
);

export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  metadata?: Record<string, any>;
  drillDownData?: ChartDataPoint[];
}

export interface InteractiveChartProps {
  title: string;
  data: ChartDataPoint[];
  chartType: 'line' | 'bar' | 'pie';
  library?: 'chartjs' | 'recharts';
  height?: number;
  enableDrillDown?: boolean;
  enableExport?: boolean;
  enableFullscreen?: boolean;
  enableFiltering?: boolean;
  onDataPointClick?: (dataPoint: ChartDataPoint, index: number) => void;
  onExport?: (format: 'png' | 'pdf' | 'csv' | 'excel') => void;
  customTooltip?: (dataPoint: ChartDataPoint) => React.ReactNode;
  colorScheme?: string[];
}

export const InteractiveChart: React.FC<InteractiveChartProps> = ({
  title,
  data,
  chartType,
  library = 'chartjs',
  height = 400,
  enableDrillDown = true,
  enableExport = true,
  enableFullscreen = true,
  enableFiltering = true,
  onDataPointClick,
  onExport,
  customTooltip,
  colorScheme = ['#1976d2', '#dc004e', '#9c27b0', '#673ab7', '#3f51b5'],
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [fullscreenOpen, setFullscreenOpen] = useState(false);
  const [drillDownData, setDrillDownData] = useState<ChartDataPoint[] | null>(null);
  const [drillDownTitle, setDrillDownTitle] = useState<string>('');
  const [filterValue, setFilterValue] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('30d');

  // Filter data based on current filters
  const filteredData = useMemo(() => {
    let filtered = [...data];
    
    if (filterValue !== 'all') {
      filtered = filtered.filter(point => 
        point.metadata?.category === filterValue
      );
    }
    
    // Apply time range filter if data has timestamps
    if (timeRange !== 'all') {
      const now = new Date();
      const daysBack = parseInt(timeRange.replace('d', ''));
      const cutoffDate = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
      
      filtered = filtered.filter(point => {
        if (point.metadata?.timestamp) {
          return new Date(point.metadata.timestamp) >= cutoffDate;
        }
        return true;
      });
    }
    
    return filtered;
  }, [data, filterValue, timeRange]);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleExport = (format: 'png' | 'pdf' | 'csv' | 'excel') => {
    onExport?.(format);
    handleMenuClose();
  };

  const handleDataPointClick = useCallback((dataPoint: ChartDataPoint, index: number) => {
    if (enableDrillDown && dataPoint.drillDownData) {
      setDrillDownData(dataPoint.drillDownData);
      setDrillDownTitle(`${title} - ${dataPoint.label || dataPoint.x}`);
    }
    onDataPointClick?.(dataPoint, index);
  }, [enableDrillDown, onDataPointClick, title]);

  const handleFilterChange = (event: SelectChangeEvent) => {
    setFilterValue(event.target.value);
  };

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    setTimeRange(event.target.value);
  };

  // Chart.js configuration
  const chartJSOptions: ChartOptions<'line' | 'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false, // We handle title separately
      },
      tooltip: {
        callbacks: {
          afterBody: (context) => {
            const dataPoint = filteredData[context[0].dataIndex];
            if (dataPoint.metadata) {
              return Object.entries(dataPoint.metadata)
                .map(([key, value]) => `${key}: ${value}`)
                .join('\n');
            }
            return '';
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const index = elements[0].index;
        const dataPoint = filteredData[index];
        handleDataPointClick(dataPoint, index);
      }
    },
  };

  const chartJSData = {
    labels: filteredData.map(point => point.x?.toString() || 'N/A'),
    datasets: [
      {
        label: title,
        data: filteredData.map(point => point.y),
        backgroundColor: colorScheme[0] + '80', // Add transparency
        borderColor: colorScheme[0],
        borderWidth: 2,
        tension: chartType === 'line' ? 0.4 : 0,
      },
    ],
  } as ChartData<typeof chartType>;

  // Recharts data format
  const rechartsData = filteredData.map(point => ({
    name: point.x?.toString() || 'N/A',
    value: point.y,
    label: point.label,
    ...point.metadata,
  }));

  const renderChart = () => {
    if (library === 'recharts') {
      return (
        <ResponsiveContainer width="100%" height={height}>
          {chartType === 'line' ? (
            <LineChart data={rechartsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip 
                content={({ active, payload, label }: any) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <Box sx={{ 
                        bgcolor: 'background.paper', 
                        p: 1, 
                        border: 1, 
                        borderColor: 'divider',
                        borderRadius: 1,
                        boxShadow: 2,
                      }}>
                        <Typography variant="body2" fontWeight="bold">
                          {label}
                        </Typography>
                        <Typography variant="body2">
                          Value: {payload[0].value}
                        </Typography>
                        {data.metadata && Object.entries(data.metadata).map(([key, value]: [string, any]) => (
                          <Typography key={key} variant="caption" display="block">
                            {key}: {String(value)}
                          </Typography>
                        ))}
                      </Box>
                    );
                  }
                  return null;
                }}
              />
              <RechartsLegend />
              <RechartsLine 
                type="monotone" 
                dataKey="value" 
                stroke={colorScheme[0]} 
                strokeWidth={2}
                dot={{ fill: colorScheme[0], strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: colorScheme[0], strokeWidth: 2 }}
                onClick={(data: any) => {
                  if (data && typeof data.index === 'number') {
                    const dataPoint = filteredData[data.index];
                    handleDataPointClick(dataPoint, data.index);
                  }
                }}
              />
            </LineChart>
          ) : chartType === 'bar' ? (
            <BarChart data={rechartsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip />
              <RechartsLegend />
              <RechartsBar 
                dataKey="value" 
                fill={colorScheme[0]}
                onClick={(data, index) => {
                  const dataPoint = filteredData[index];
                  handleDataPointClick(dataPoint, index);
                }}
              />
            </BarChart>
          ) : (
            <PieChart>
              <Pie
                data={rechartsData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                onClick={(data, index) => {
                  const dataPoint = filteredData[index];
                  handleDataPointClick(dataPoint, index);
                }}
              >
                {rechartsData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colorScheme[index % colorScheme.length]} />
                ))}
              </Pie>
              <RechartsTooltip />
              <RechartsLegend />
            </PieChart>
          )}
        </ResponsiveContainer>
      );
    } else {
      // Chart.js
      return (
        <Box sx={{ height }}>
          {chartType === 'line' ? (
            <Line data={chartJSData as any} options={chartJSOptions as any} />
          ) : (
            <Bar data={chartJSData as any} options={chartJSOptions as any} />
          )}
        </Box>
      );
    }
  };

  const availableCategories = useMemo(() => {
    const categories = new Set<string>();
    data.forEach(point => {
      if (point.metadata?.category) {
        categories.add(point.metadata.category);
      }
    });
    return Array.from(categories);
  }, [data]);

  return (
    <>
      <Card>
        <CardContent>
          {/* Chart Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" component="h3">
              {title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {/* Filters */}
              {enableFiltering && (
                <Stack direction="row" spacing={1}>
                  {availableCategories.length > 0 && (
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <InputLabel>Category</InputLabel>
                      <Select
                        value={filterValue}
                        label="Category"
                        onChange={handleFilterChange}
                      >
                        <MenuItem value="all">All</MenuItem>
                        {availableCategories.map(category => (
                          <MenuItem key={category} value={category}>
                            {category}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                  <FormControl size="small" sx={{ minWidth: 100 }}>
                    <InputLabel>Period</InputLabel>
                    <Select
                      value={timeRange}
                      label="Period"
                      onChange={handleTimeRangeChange}
                    >
                      <MenuItem value="all">All Time</MenuItem>
                      <MenuItem value="7d">7 Days</MenuItem>
                      <MenuItem value="30d">30 Days</MenuItem>
                      <MenuItem value="90d">90 Days</MenuItem>
                      <MenuItem value="365d">1 Year</MenuItem>
                    </Select>
                  </FormControl>
                </Stack>
              )}
              
              {/* Action Buttons */}
              {enableFullscreen && (
                <Tooltip title="Fullscreen">
                  <IconButton onClick={() => setFullscreenOpen(true)}>
                    <FullscreenIcon />
                  </IconButton>
                </Tooltip>
              )}
              
              {enableExport && (
                <>
                  <Tooltip title="More options">
                    <IconButton onClick={handleMenuClick}>
                      <MoreVertIcon />
                    </IconButton>
                  </Tooltip>
                  <Menu
                    anchorEl={anchorEl}
                    open={Boolean(anchorEl)}
                    onClose={handleMenuClose}
                  >
                    <MenuItem onClick={() => handleExport('png')}>
                      Export as PNG
                    </MenuItem>
                    <MenuItem onClick={() => handleExport('pdf')}>
                      Export as PDF
                    </MenuItem>
                    <MenuItem onClick={() => handleExport('csv')}>
                      Export as CSV
                    </MenuItem>
                    <MenuItem onClick={() => handleExport('excel')}>
                      Export as Excel
                    </MenuItem>
                  </Menu>
                </>
              )}
            </Box>
          </Box>

          {/* Active Filters Display */}
          {(filterValue !== 'all' || timeRange !== 'all') && (
            <Box sx={{ mb: 2 }}>
              <Stack direction="row" spacing={1}>
                {filterValue !== 'all' && (
                  <Chip
                    label={`Category: ${filterValue}`}
                    onDelete={() => setFilterValue('all')}
                    size="small"
                  />
                )}
                {timeRange !== 'all' && (
                  <Chip
                    label={`Period: ${timeRange}`}
                    onDelete={() => setTimeRange('all')}
                    size="small"
                  />
                )}
              </Stack>
            </Box>
          )}

          {/* Chart */}
          {renderChart()}

          {/* Data Summary */}
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="textSecondary">
              Showing {filteredData.length} of {data.length} data points
            </Typography>
            {enableDrillDown && (
              <Typography variant="body2" color="textSecondary">
                Click on data points for detailed view
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Fullscreen Dialog */}
      <Dialog
        open={fullscreenOpen}
        onClose={() => setFullscreenOpen(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          {title}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ height: '70vh' }}>
            {renderChart()}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFullscreenOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Drill-down Dialog */}
      <Dialog
        open={Boolean(drillDownData)}
        onClose={() => setDrillDownData(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {drillDownTitle}
        </DialogTitle>
        <DialogContent>
          {drillDownData && (
            <InteractiveChart
              title={drillDownTitle}
              data={drillDownData}
              chartType={chartType}
              library={library}
              height={300}
              enableDrillDown={false}
              enableFullscreen={false}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDrillDownData(null)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default InteractiveChart;