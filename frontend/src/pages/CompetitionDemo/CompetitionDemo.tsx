import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  PlayArrow,
  Assessment,
  TrendingUp,
  Speed,
  AttachMoney,
  Psychology,
  ExpandMore,
  CheckCircle,

  CloudQueue,
  Memory
} from '@mui/icons-material';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { apiService } from '../../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  target_market: string;
  industry: string;
  estimated_duration: string;
  complexity: string;
}

interface ImpactMetrics {
  time_reduction_percentage: number;
  cost_savings_percentage: number;
  traditional_time_weeks: number;
  ai_time_hours: number;
  traditional_cost_usd: number;
  ai_cost_usd: number;
  confidence_score: number;
  data_quality_score: number;
  automation_level: number;
}

interface CompetitionMetrics {
  bedrock_nova_usage: Record<string, number>;
  agentcore_primitives_used: string[];
  external_api_integrations: number;
  autonomous_decisions_made: number;
  reasoning_steps_completed: number;
  inter_agent_communications: number;
}

interface DemoExecution {
  execution_id: string;
  scenario: string;
  status: 'running' | 'completed' | 'failed' | 'not_found' | 'timeout';
  impact_metrics?: ImpactMetrics;
  competition_metrics?: CompetitionMetrics;
  execution_timeline?: Array<{
    timestamp: string;
    event: string;
    details: string;
  }>;
  agent_decision_log?: Array<{
    timestamp: string;
    agent: string;
    decision: string;
    reasoning: string;
    confidence: number;
  }>;
  before_after_comparison?: any;
}

const CompetitionDemo: React.FC = () => {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [currentExecution, setCurrentExecution] = useState<DemoExecution | null>(null);
  const [showcaseData, setShowcaseData] = useState<any>(null);
  const [impactDashboard, setImpactDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [resultsDialog, setResultsDialog] = useState(false);
  const [executionResults, setExecutionResults] = useState<any>(null);
  const [awsStatus, setAwsStatus] = useState<{aws_configured: boolean; mode: string; message: string} | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Use ref to track polling interval for cleanup
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadDemoStatus();
    loadDemoScenarios();
    loadShowcaseData();
    loadImpactDashboard();
  }, []);

  const loadDemoStatus = async () => {
    try {
      // Direct backend call (bypassing proxy for now)
      let response;
      try {
        console.log('Making direct connection to: http://localhost:8000/api/v1/demo/status');
        response = await fetch('http://localhost:8000/api/v1/demo/status');
        console.log('Direct connection response:', response.status, response.statusText);
        if (!response.ok) {
          throw new Error(`Direct backend failed with HTTP ${response.status}`);
        }
        console.log('Direct connection successful!');
      } catch (backendError) {
        console.error('Direct backend connection failed:', backendError);
        console.error('Backend error details:', backendError.message, backendError.stack);
        // Set default mock status
        setAwsStatus({
          aws_configured: false,
          mode: 'mock',
          message: 'API connection failed - using mock mode for demonstration'
        });
        return;
      }
      
      const data = await response.json();
      setAwsStatus(data);
    } catch (error) {
      console.error('Failed to load demo status:', error);
      // Default to mock mode if status check fails
      setAwsStatus({
        aws_configured: false,
        mode: 'mock',
        message: 'AWS not configured - using sample output for demonstration'
      });
    }
  };

  const loadDemoScenarios = async () => {
    try {
      console.log('Loading demo scenarios...');
      const data = await apiService.getDemoScenarios();
      setScenarios(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load demo scenarios:', error);
      setScenarios([]);
    }
  };

  const loadShowcaseData = async () => {
    try {
      console.log('Loading showcase data...');
      const data = await apiService.getDemoShowcase();
      setShowcaseData(data);
    } catch (error) {
      console.error('Failed to load showcase data:', error);
      // Set default mock showcase data
      setShowcaseData({
        aws_services_used: ['Amazon Bedrock Nova', 'Amazon ECS', 'Amazon S3'],
        ai_capabilities: { reasoning_llms: 'Mock data - API connection failed' },
        measurable_impact: { time_reduction: 'Mock data' },
        technical_innovation: { public_data_first: 'Mock data' }
      });
    }
  };

  const loadImpactDashboard = async () => {
    try {
      console.log('Loading impact dashboard...');
      const data = await apiService.getDemoImpactDashboard();
      setImpactDashboard(data);
    } catch (error) {
      console.error('Failed to load impact dashboard:', error);
      // Set default mock impact dashboard
      setImpactDashboard({
        total_executions: 0,
        average_metrics: {
          time_reduction_percentage: 95.0,
          cost_savings_percentage: 80.0,
          confidence_score: 0.92,
          automation_level: 95.0
        },
        message: 'Mock data - API connection failed'
      });
    }
  };

  const executeDemo = async (scenarioId: string) => {
    setLoading(true);
    setSelectedScenario(scenarioId);
    setError(null); // Clear any previous errors
    
    try {
      console.log(`Executing demo scenario: ${scenarioId}`);
      const data = await apiService.executeDemoScenario(scenarioId, false); // Use real AWS when available
      console.log('Demo execution response:', data);
      
      setCurrentExecution({
        execution_id: data.execution_id,
        scenario: scenarioId,
        status: data.status || 'running'
      });
      
      // Check if demo completed instantly
      if (data.status === 'completed') {
        setLoading(false);
        loadExecutionResults(data.execution_id);
      } else {
        // Poll for status updates if not completed
        pollExecutionStatus(data.execution_id);
      }
    } catch (error: any) {
      console.error('Failed to execute demo:', error);
      setLoading(false);
      
      // Provide user-friendly error message
      if (error.code === 'ECONNABORTED') {
        setError('Demo execution timed out. The backend may be processing a complex scenario. Please try again.');
      } else if (error.response?.status === 500) {
        setError('Demo execution failed due to a server error. Please try again.');
      } else if (error.response?.status === 404) {
        setError('Demo scenario not found. Please refresh the page and try again.');
      } else {
        setError(`Demo execution failed: ${error.message || 'Unknown error'}. Please try again.`);
      }
    }
  };

  const pollExecutionStatus = async (executionId: string) => {
    // Clear any existing polling interval
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    
    let pollCount = 0;
    const maxPolls = 24; // 2 minutes max (24 * 5 seconds)
    
    pollIntervalRef.current = setInterval(async () => {
      try {
        pollCount++;
        console.log(`Polling execution status for: ${executionId} (${pollCount}/${maxPolls})`);
        
        if (pollCount > maxPolls) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          console.log('Polling timeout reached, stopping');
          setLoading(false);
          setCurrentExecution(prev => prev ? { ...prev, status: 'timeout' } : null);
          return;
        }
        
        const data = await apiService.getDemoExecutionStatus(executionId);
        console.log('Poll response:', data);
        
        if (data.status === 'completed') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setCurrentExecution(prev => prev ? { ...prev, status: 'completed', impact_metrics: data.impact_metrics } : null);
          setLoading(false);
          loadExecutionResults(executionId);
        } else if (data.status === 'failed') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setCurrentExecution(prev => prev ? { ...prev, status: 'failed' } : null);
          setLoading(false);
        } else if (data.status === 'not_found') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          console.log('Demo execution not found, stopping polling');
          setLoading(false);
          setCurrentExecution(prev => prev ? { ...prev, status: 'not_found' } : null);
        }
        // Continue polling for 'running' status
      } catch (error) {
        console.error('Failed to poll execution status:', error);
        pollCount++; // Count errors toward timeout
      }
    }, 5000);
  };
  
  // Cleanup polling interval on component unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);

  const loadExecutionResults = async (executionId: string) => {
    try {
      console.log(`Loading execution results for: ${executionId}`);
      const data = await apiService.getDemoExecutionResults(executionId);
      setExecutionResults(data);
      setResultsDialog(true);
      loadImpactDashboard(); // Refresh dashboard
    } catch (error) {
      console.error('Failed to load execution results:', error);
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'High': return 'error';
      case 'Medium': return 'warning';
      default: return 'success';
    }
  };

  const renderImpactMetricsChart = () => {
    if (!impactDashboard?.average_metrics) return null;

    const data = {
      labels: ['Time Reduction', 'Cost Savings', 'Confidence Score', 'Automation Level'],
      datasets: [{
        label: 'Performance Metrics (%)',
        data: [
          impactDashboard.average_metrics.time_reduction_percentage,
          impactDashboard.average_metrics.cost_savings_percentage,
          impactDashboard.average_metrics.confidence_score * 100,
          impactDashboard.average_metrics.automation_level * 100
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(153, 102, 255, 0.6)'
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(153, 102, 255, 1)'
        ],
        borderWidth: 1
      }]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: 'Competition Impact Metrics'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      }
    };

    return <Bar data={data} options={options} data-testid="bar-chart" />;
  };

  const renderBedrockUsageChart = () => {
    if (!executionResults?.competition_metrics?.bedrock_nova_usage) return null;

    const usage = executionResults.competition_metrics.bedrock_nova_usage;
    const data = {
      labels: Object.keys(usage),
      datasets: [{
        data: Object.values(usage),
        backgroundColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0'
        ]
      }]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'right' as const,
        },
        title: {
          display: true,
          text: 'Amazon Bedrock Nova Model Usage'
        }
      }
    };

    return <Doughnut data={data} options={options} data-testid="doughnut-chart" />;
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        AWS AI Agent Competition Demo
      </Typography>
      
      <Typography variant="h6" color="text.secondary" align="center" sx={{ mb: 4 }}>
        RiskIntel360 - Autonomous Multi-Agent Financial Risk Validation Platform
      </Typography>

      {/* AWS Configuration Status Banner */}
      {awsStatus && (
        <Alert 
          severity={awsStatus.aws_configured ? "success" : "info"} 
          icon={awsStatus.aws_configured ? <CheckCircle /> : <Memory />}
          sx={{ mb: 3 }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="subtitle1" fontWeight="bold">
                {awsStatus.aws_configured ? '🚀 Live AI Mode' : '📊 Demo Mode'}
              </Typography>
              <Typography variant="body2">
                {awsStatus.message}
              </Typography>
            </Box>
            <Chip 
              label={awsStatus.mode?.toUpperCase() || 'UNKNOWN'} 
              color={awsStatus.aws_configured ? "success" : "default"}
              sx={{ fontWeight: 'bold' }}
            />
          </Box>
        </Alert>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <Typography variant="subtitle1" fontWeight="bold">
            Demo Execution Error
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
        </Alert>
      )}

      {/* Competition Showcase Section */}
      {showcaseData && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              <CloudQueue sx={{ mr: 1, verticalAlign: 'middle' }} />
              AWS Services & Competition Requirements
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>AWS Services Used</Typography>
                <List dense>
                  {showcaseData.aws_services_used?.map((service: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText primary={service} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>AgentCore Primitives</Typography>
                <List dense>
                  {showcaseData.agentcore_primitives?.map((primitive: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <Memory color="primary" />
                      </ListItemIcon>
                      <ListItemText primary={primitive} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Impact Dashboard */}
      {impactDashboard && impactDashboard.total_executions > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              <Assessment sx={{ mr: 1, verticalAlign: 'middle' }} />
              Measurable Impact Dashboard
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                {renderImpactMetricsChart()}
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" color="success.main">
                    <TrendingUp sx={{ mr: 1, verticalAlign: 'middle' }} />
                    {impactDashboard.average_metrics?.time_reduction_percentage?.toFixed(1) || '0.0'}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Time Reduction
                  </Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" color="primary.main">
                    <AttachMoney sx={{ mr: 1, verticalAlign: 'middle' }} />
                    {impactDashboard.average_metrics?.cost_savings_percentage?.toFixed(1) || '0.0'}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Cost Savings
                  </Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" color="warning.main">
                    <Psychology sx={{ mr: 1, verticalAlign: 'middle' }} />
                    {((impactDashboard.average_metrics?.confidence_score || 0) * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Confidence Score
                  </Typography>
                </Box>
                
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Executions: {impactDashboard.total_executions}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Autonomous Decisions: {impactDashboard.competition_totals?.autonomous_decisions_made || 0}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Demo Scenarios */}
      <Typography variant="h5" gutterBottom>
        Competition Demo Scenarios
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {Array.isArray(scenarios) && scenarios.map((scenario) => (
          <Grid item xs={12} md={6} lg={4} key={scenario.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" gutterBottom>
                  {scenario.name}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {scenario.description}
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Chip 
                    label={scenario.industry} 
                    size="small" 
                    sx={{ mr: 1, mb: 1 }} 
                  />
                  <Chip 
                    label={scenario.complexity} 
                    size="small" 
                    color={getComplexityColor(scenario.complexity)}
                    sx={{ mr: 1, mb: 1 }} 
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <Speed sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                  Duration: {scenario.estimated_duration}
                </Typography>
                
                <Typography variant="body2" color="text.secondary">
                  Target: {scenario.target_market}
                </Typography>
              </CardContent>
              
              <Box sx={{ p: 2, pt: 0 }}>
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<PlayArrow />}
                  onClick={() => executeDemo(scenario.id)}
                  disabled={loading && selectedScenario === scenario.id}
                >
                  {loading && selectedScenario === scenario.id ? 'Executing...' : 'Execute Demo'}
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Current Execution Status */}
      {currentExecution && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Current Demo Execution
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body1">
                Scenario: {currentExecution.scenario.replace('_', ' ').toUpperCase()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Execution ID: {currentExecution.execution_id}
              </Typography>
            </Box>
            
            {currentExecution.status === 'running' && (
              <Box>
                <LinearProgress sx={{ mb: 2 }} />
                <Alert severity="info">
                  Demo execution in progress. This typically takes 90-120 minutes to complete.
                </Alert>
              </Box>
            )}
            
            {currentExecution.status === 'completed' && currentExecution.impact_metrics && (
              <Alert severity="success">
                Demo completed successfully! 
                Time reduction: {currentExecution.impact_metrics?.time_reduction_percentage?.toFixed(1) || '0.0'}%, 
                Cost savings: {currentExecution.impact_metrics?.cost_savings_percentage?.toFixed(1) || '0.0'}%
              </Alert>
            )}
            
            {currentExecution.status === 'failed' && (
              <Alert severity="error">
                Demo execution failed. Please try again.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Dialog */}
      <Dialog 
        open={resultsDialog} 
        onClose={() => setResultsDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Competition Demo Results
        </DialogTitle>
        
        <DialogContent>
          {executionResults && (
            <Box>
              {/* Impact Metrics */}
              <Typography variant="h6" gutterBottom>Impact Metrics</Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {executionResults.impact_metrics?.time_reduction_percentage?.toFixed(1) || '0.0'}%
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">Time Reduction</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                      {executionResults.before_after_comparison?.improvements?.time_saved?.explanation || 
                       `${executionResults.impact_metrics?.traditional_time_weeks || 0} weeks → ${executionResults.impact_metrics?.ai_time_hours?.toFixed(1) || 0} hours`}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary.main">
                      {executionResults.impact_metrics?.cost_savings_percentage?.toFixed(1) || '0.0'}%
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">Cost Savings</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                      {executionResults.before_after_comparison?.improvements?.cost_reduced?.explanation || 
                       `$${executionResults.impact_metrics?.traditional_cost_usd?.toLocaleString() || 0} → $${executionResults.impact_metrics?.ai_cost_usd?.toLocaleString() || 0}`}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {((executionResults.impact_metrics?.confidence_score || 0) * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">Confidence Score</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                      {executionResults.before_after_comparison?.improvements?.accuracy_improved?.explanation || 
                       'AI-powered analysis with cross-agent validation'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main">
                      {((executionResults.impact_metrics?.automation_level || 0) * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">Automation Level</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                      {executionResults.before_after_comparison?.improvements?.automation_level?.explanation || 
                       'Fully automated with human oversight'}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              {/* Bedrock Usage Chart */}
              <Box sx={{ mb: 4, height: 300 }}>
                {renderBedrockUsageChart()}
              </Box>

              {/* Competition Metrics */}
              <Accordion sx={{ mt: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">Competition Metrics</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>Autonomous Capabilities</Typography>
                      <Typography>Decisions Made: {executionResults.competition_metrics.autonomous_decisions_made}</Typography>
                      <Typography>Reasoning Steps: {executionResults.competition_metrics.reasoning_steps_completed}</Typography>
                      <Typography>Inter-Agent Communications: {executionResults.competition_metrics.inter_agent_communications}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>Integration Points</Typography>
                      <Typography>External APIs: {executionResults.competition_metrics.external_api_integrations}</Typography>
                      <Typography>AgentCore Primitives: {executionResults.competition_metrics.agentcore_primitives_used.length}</Typography>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* Agent Decision Log - Detailed View */}
              <Accordion sx={{ mt: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">Agent Decision Log - Detailed Analysis</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {executionResults.agent_decision_log?.map((decision: any, index: number) => (
                      <Card key={index} variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Box>
                              <Chip 
                                label={decision.agent.replace(/_/g, ' ').toUpperCase()} 
                                color="primary" 
                                size="small" 
                                sx={{ mb: 1 }}
                              />
                              <Typography variant="h6" gutterBottom>
                                {decision.decision}
                              </Typography>
                            </Box>
                            <Chip 
                              label={`${((decision.confidence || 0) * 100).toFixed(0)}% Confidence`}
                              color={decision.confidence >= 0.9 ? "success" : decision.confidence >= 0.8 ? "primary" : "warning"}
                              sx={{ fontWeight: 'bold' }}
                            />
                          </Box>
                          
                          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                            <strong>Reasoning:</strong> {decision.reasoning}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setResultsDialog(false)}>Close</Button>
          {currentExecution && (
            <Button 
              variant="contained" 
              onClick={() => {
                setResultsDialog(false);
                navigate(`/validation/${currentExecution.execution_id}/results`);
              }}
            >
              View Full Results
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CompetitionDemo;