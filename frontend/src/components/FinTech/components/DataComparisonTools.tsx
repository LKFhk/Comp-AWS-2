/**
 * Data Comparison Tools Component
 * Provides time period, scenario, and benchmark comparison capabilities
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Grid,
  Alert,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  Stack,
} from '@mui/material';
import {
  Compare as CompareIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
  Add as AddIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { InteractiveChart, ChartDataPoint } from './InteractiveChart';
import { ExportFunctionality } from './ExportFunctionality';

export interface ComparisonDataSet {
  id: string;
  name: string;
  data: any[];
  color: string;
  type: 'current' | 'historical' | 'benchmark' | 'scenario';
  metadata?: {
    period?: string;
    description?: string;
    source?: string;
    lastUpdated?: string;
  };
}

export interface ComparisonMetric {
  field: string;
  label: string;
  format: 'number' | 'currency' | 'percentage' | 'date';
  aggregation: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'last';
  showTrend?: boolean;
  showPercentChange?: boolean;
}

export interface BenchmarkData {
  id: string;
  name: string;
  value: number;
  description?: string;
  source?: string;
  category: 'industry' | 'competitor' | 'internal' | 'regulatory';
}

export interface DataComparisonToolsProps {
  primaryDataSet: ComparisonDataSet;
  availableDataSets: ComparisonDataSet[];
  comparisonMetrics: ComparisonMetric[];
  benchmarks?: BenchmarkData[];
  onComparisonChange?: (selectedDataSets: ComparisonDataSet[], metrics: ComparisonMetric[]) => void;
  onSaveComparison?: (name: string, comparison: any) => void;
  enableScenarioModeling?: boolean;
  enableBenchmarking?: boolean;
  maxComparisons?: number;
}

export const DataComparisonTools: React.FC<DataComparisonToolsProps> = ({
  primaryDataSet,
  availableDataSets,
  comparisonMetrics,
  benchmarks = [],
  onComparisonChange,
  onSaveComparison,
  enableScenarioModeling = true,
  enableBenchmarking = true,
  maxComparisons = 5,
}) => {
  const [selectedDataSets, setSelectedDataSets] = useState<ComparisonDataSet[]>([primaryDataSet]);
  const [activeTab, setActiveTab] = useState(0);
  const [comparisonView, setComparisonView] = useState<'chart' | 'table' | 'metrics'>('chart');
  const [selectedMetrics, setSelectedMetrics] = useState<ComparisonMetric[]>(comparisonMetrics.slice(0, 3));
  const [selectedBenchmarks, setSelectedBenchmarks] = useState<BenchmarkData[]>([]);
  const [scenarioDialogOpen, setScenarioDialogOpen] = useState(false);
  const [scenarioName, setScenarioName] = useState('');
  const [scenarioModifier, setScenarioModifier] = useState(1.0);
  const [showPercentageChange, setShowPercentageChange] = useState(true);
  const [showTrendIndicators, setShowTrendIndicators] = useState(true);

  // Calculate comparison metrics
  const comparisonResults = useMemo(() => {
    return selectedMetrics.map(metric => {
      const results = selectedDataSets.map(dataSet => {
        const values = dataSet.data.map(item => Number(item[metric.field]) || 0);
        
        let aggregatedValue: number;
        switch (metric.aggregation) {
          case 'sum':
            aggregatedValue = values.reduce((sum, val) => sum + val, 0);
            break;
          case 'avg':
            aggregatedValue = values.length > 0 ? values.reduce((sum, val) => sum + val, 0) / values.length : 0;
            break;
          case 'min':
            aggregatedValue = Math.min(...values);
            break;
          case 'max':
            aggregatedValue = Math.max(...values);
            break;
          case 'count':
            aggregatedValue = values.length;
            break;
          case 'last':
            aggregatedValue = values[values.length - 1] || 0;
            break;
          default:
            aggregatedValue = 0;
        }

        return {
          dataSetId: dataSet.id,
          dataSetName: dataSet.name,
          value: aggregatedValue,
          rawValues: values,
        };
      });

      // Calculate percentage changes relative to primary dataset
      const primaryValue = results.find(r => r.dataSetId === primaryDataSet.id)?.value || 0;
      const resultsWithChange = results.map(result => ({
        ...result,
        percentChange: primaryValue !== 0 ? ((result.value - primaryValue) / primaryValue) * 100 : 0,
        trend: (result.value > primaryValue ? 'up' : result.value < primaryValue ? 'down' : 'neutral') as 'up' | 'down' | 'neutral',
      }));

      return {
        metric,
        results: resultsWithChange,
      };
    });
  }, [selectedDataSets, selectedMetrics, primaryDataSet.id]);

  // Prepare chart data for comparison
  const chartData = useMemo(() => {
    if (selectedDataSets.length === 0) return [];

    // Combine all data points with timestamps
    const allDataPoints: ChartDataPoint[] = [];
    
    selectedDataSets.forEach((dataSet, dataSetIndex) => {
      dataSet.data.forEach((item, itemIndex) => {
        selectedMetrics.forEach(metric => {
          allDataPoints.push({
            x: item.timestamp || item.date || itemIndex,
            y: Number(item[metric.field]) || 0,
            label: `${dataSet.name} - ${metric.label}`,
            metadata: {
              dataSetId: dataSet.id,
              dataSetName: dataSet.name,
              metric: metric.field,
              metricLabel: metric.label,
              color: dataSet.color,
              ...item,
            },
          });
        });
      });
    });

    return allDataPoints;
  }, [selectedDataSets, selectedMetrics]);

  const handleAddDataSet = (dataSet: ComparisonDataSet) => {
    if (selectedDataSets.length < maxComparisons && !selectedDataSets.find(ds => ds.id === dataSet.id)) {
      const newSelectedDataSets = [...selectedDataSets, dataSet];
      setSelectedDataSets(newSelectedDataSets);
      onComparisonChange?.(newSelectedDataSets, selectedMetrics);
    }
  };

  const handleRemoveDataSet = (dataSetId: string) => {
    if (dataSetId !== primaryDataSet.id) { // Don't allow removing primary dataset
      const newSelectedDataSets = selectedDataSets.filter(ds => ds.id !== dataSetId);
      setSelectedDataSets(newSelectedDataSets);
      onComparisonChange?.(newSelectedDataSets, selectedMetrics);
    }
  };

  const handleMetricToggle = (metric: ComparisonMetric) => {
    const isSelected = selectedMetrics.find(m => m.field === metric.field);
    let newSelectedMetrics: ComparisonMetric[];
    
    if (isSelected) {
      newSelectedMetrics = selectedMetrics.filter(m => m.field !== metric.field);
    } else {
      newSelectedMetrics = [...selectedMetrics, metric];
    }
    
    setSelectedMetrics(newSelectedMetrics);
    onComparisonChange?.(selectedDataSets, newSelectedMetrics);
  };

  const handleBenchmarkToggle = (benchmark: BenchmarkData) => {
    const isSelected = selectedBenchmarks.find(b => b.id === benchmark.id);
    
    if (isSelected) {
      setSelectedBenchmarks(prev => prev.filter(b => b.id !== benchmark.id));
    } else {
      setSelectedBenchmarks(prev => [...prev, benchmark]);
    }
  };

  const handleCreateScenario = () => {
    if (scenarioName.trim()) {
      // Create a modified version of the primary dataset
      const scenarioData = primaryDataSet.data.map(item => {
        const modifiedItem = { ...item };
        selectedMetrics.forEach(metric => {
          if (modifiedItem[metric.field] !== undefined) {
            modifiedItem[metric.field] = Number(modifiedItem[metric.field]) * scenarioModifier;
          }
        });
        return modifiedItem;
      });

      const scenarioDataSet: ComparisonDataSet = {
        id: `scenario-${Date.now()}`,
        name: scenarioName,
        data: scenarioData,
        color: '#ff9800',
        type: 'scenario',
        metadata: {
          description: `Scenario with ${((scenarioModifier - 1) * 100).toFixed(1)}% modifier`,
          source: 'User-generated scenario',
          lastUpdated: new Date().toISOString(),
        },
      };

      handleAddDataSet(scenarioDataSet);
      setScenarioDialogOpen(false);
      setScenarioName('');
      setScenarioModifier(1.0);
    }
  };

  const formatValue = (value: number, format: ComparisonMetric['format']) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'percentage':
        return `${value.toFixed(2)}%`;
      case 'number':
        return new Intl.NumberFormat('en-US').format(value);
      case 'date':
        return new Date(value).toLocaleDateString();
      default:
        return value.toString();
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon color="success" />;
      case 'down':
        return <TrendingDownIcon color="error" />;
      default:
        return <RemoveIcon color="disabled" />;
    }
  };

  const renderComparisonChart = () => (
    <InteractiveChart
      title="Data Comparison"
      data={chartData}
      chartType="line"
      library="recharts"
      height={400}
      enableDrillDown={true}
      enableExport={true}
      enableFullscreen={true}
      enableFiltering={true}
      colorScheme={selectedDataSets.map(ds => ds.color)}
    />
  );

  const renderComparisonTable = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Metric</TableCell>
            {selectedDataSets.map(dataSet => (
              <TableCell key={dataSet.id} align="right">
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: dataSet.color,
                    }}
                  />
                  {dataSet.name}
                </Box>
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {comparisonResults.map(({ metric, results }) => (
            <TableRow key={metric.field}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" fontWeight="medium">
                  {metric.label}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {metric.aggregation}
                </Typography>
              </TableCell>
              {results.map(result => (
                <TableCell key={result.dataSetId} align="right">
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                    <Box>
                      <Typography variant="body2">
                        {formatValue(result.value, metric.format)}
                      </Typography>
                      {showPercentageChange && result.dataSetId !== primaryDataSet.id && (
                        <Typography
                          variant="caption"
                          color={result.percentChange > 0 ? 'success.main' : result.percentChange < 0 ? 'error.main' : 'textSecondary'}
                        >
                          {result.percentChange > 0 ? '+' : ''}{result.percentChange.toFixed(1)}%
                        </Typography>
                      )}
                    </Box>
                    {showTrendIndicators && result.dataSetId !== primaryDataSet.id && (
                      <Box sx={{ minWidth: 24 }}>
                        {getTrendIcon(result.trend)}
                      </Box>
                    )}
                  </Box>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderMetricsView = () => (
    <Grid container spacing={3}>
      {comparisonResults.map(({ metric, results }) => (
        <Grid item xs={12} md={6} lg={4} key={metric.field}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {metric.label}
              </Typography>
              <Stack spacing={2}>
                {results.map(result => (
                  <Box key={result.dataSetId} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: selectedDataSets.find(ds => ds.id === result.dataSetId)?.color,
                        }}
                      />
                      <Typography variant="body2">
                        {result.dataSetName}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" fontWeight="medium">
                        {formatValue(result.value, metric.format)}
                      </Typography>
                      {showPercentageChange && result.dataSetId !== primaryDataSet.id && (
                        <Typography
                          variant="caption"
                          color={result.percentChange > 0 ? 'success.main' : result.percentChange < 0 ? 'error.main' : 'textSecondary'}
                        >
                          {result.percentChange > 0 ? '+' : ''}{result.percentChange.toFixed(1)}%
                        </Typography>
                      )}
                    </Box>
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">
            Data Comparison Tools
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <ExportFunctionality
              data={{
                title: 'Data Comparison Results',
                data: comparisonResults.flatMap(cr => cr.results),
                metadata: {
                  generatedBy: 'RiskIntel360 Platform',
                  generatedAt: new Date().toISOString(),
                  description: 'Comparison analysis results',
                  filters: {
                    dataSets: selectedDataSets.map(ds => ds.name).join(', '),
                  },
                },
              }}
              buttonSize="small"
            />
            {onSaveComparison && (
              <Button
                startIcon={<SaveIcon />}
                onClick={() => onSaveComparison('comparison', { selectedDataSets, selectedMetrics })}
                size="small"
                variant="outlined"
              >
                Save
              </Button>
            )}
          </Box>
        </Box>

        {/* Data Set Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Selected Data Sets ({selectedDataSets.length}/{maxComparisons})
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
            {selectedDataSets.map(dataSet => (
              <Chip
                key={dataSet.id}
                label={dataSet.name}
                onDelete={dataSet.id !== primaryDataSet.id ? () => handleRemoveDataSet(dataSet.id) : undefined}
                sx={{
                  backgroundColor: dataSet.color + '20',
                  borderColor: dataSet.color,
                  color: dataSet.color,
                }}
                variant="outlined"
              />
            ))}
          </Stack>
          
          <FormControl size="small" sx={{ minWidth: 200, mr: 2 }}>
            <InputLabel>Add Data Set</InputLabel>
            <Select
              value=""
              label="Add Data Set"
              onChange={(e) => {
                const dataSet = availableDataSets.find(ds => ds.id === e.target.value);
                if (dataSet) handleAddDataSet(dataSet);
              }}
            >
              {availableDataSets
                .filter(ds => !selectedDataSets.find(sds => sds.id === ds.id))
                .map(dataSet => (
                  <MenuItem key={dataSet.id} value={dataSet.id}>
                    {dataSet.name} ({dataSet.type})
                  </MenuItem>
                ))}
            </Select>
          </FormControl>

          {enableScenarioModeling && (
            <Button
              startIcon={<AddIcon />}
              onClick={() => setScenarioDialogOpen(true)}
              size="small"
              variant="outlined"
            >
              Create Scenario
            </Button>
          )}
        </Box>

        {/* Metric Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Comparison Metrics
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {comparisonMetrics.map(metric => (
              <Chip
                key={metric.field}
                label={metric.label}
                onClick={() => handleMetricToggle(metric)}
                color={selectedMetrics.find(m => m.field === metric.field) ? 'primary' : 'default'}
                variant={selectedMetrics.find(m => m.field === metric.field) ? 'filled' : 'outlined'}
              />
            ))}
          </Stack>
        </Box>

        {/* Benchmarks */}
        {enableBenchmarking && benchmarks.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Benchmarks
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {benchmarks.map(benchmark => (
                <Chip
                  key={benchmark.id}
                  label={`${benchmark.name}: ${formatValue(benchmark.value, 'number')}`}
                  onClick={() => handleBenchmarkToggle(benchmark)}
                  color={selectedBenchmarks.find(b => b.id === benchmark.id) ? 'secondary' : 'default'}
                  variant={selectedBenchmarks.find(b => b.id === benchmark.id) ? 'filled' : 'outlined'}
                  size="small"
                />
              ))}
            </Stack>
          </Box>
        )}

        {/* View Options */}
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab label="Chart View" />
            <Tab label="Table View" />
            <Tab label="Metrics View" />
          </Tabs>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={showPercentageChange}
                  onChange={(e) => setShowPercentageChange(e.target.checked)}
                  size="small"
                />
              }
              label="% Change"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={showTrendIndicators}
                  onChange={(e) => setShowTrendIndicators(e.target.checked)}
                  size="small"
                />
              }
              label="Trends"
            />
          </Box>
        </Box>

        {/* Comparison Results */}
        {selectedDataSets.length > 1 ? (
          <Box>
            {activeTab === 0 && renderComparisonChart()}
            {activeTab === 1 && renderComparisonTable()}
            {activeTab === 2 && renderMetricsView()}
          </Box>
        ) : (
          <Alert severity="info">
            Select additional data sets to begin comparison analysis.
          </Alert>
        )}
      </CardContent>

      {/* Scenario Creation Dialog */}
      <Dialog
        open={scenarioDialogOpen}
        onClose={() => setScenarioDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create Scenario</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Scenario Name"
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              fullWidth
              placeholder="e.g., Optimistic Growth, Market Downturn"
            />
            
            <Box>
              <Typography gutterBottom>
                Modifier: {((scenarioModifier - 1) * 100).toFixed(1)}%
              </Typography>
              <Box sx={{ px: 2 }}>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={scenarioModifier}
                  onChange={(e) => setScenarioModifier(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography variant="caption">-50%</Typography>
                <Typography variant="caption">+100%</Typography>
              </Box>
            </Box>

            <Alert severity="info">
              This will create a modified version of your primary dataset with the specified modifier applied to all selected metrics.
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScenarioDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleCreateScenario}
            variant="contained"
            disabled={!scenarioName.trim()}
          >
            Create Scenario
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default DataComparisonTools;