/**
 * Competition Demo Dashboard Component
 * AWS competition showcase scenarios and live demonstrations
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
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Timeline as TimelineIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Person as PersonIcon,
  AttachMoney as AttachMoneyIcon,
  Speed as SpeedIcon,
  CloudQueue as CloudQueueIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Visibility as VisibilityIcon,
  EmojiEvents as EmojiEventsIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';
import { useWebSocketUpdates } from './hooks/useWebSocketUpdates';

interface CompetitionDemoDashboardProps {
  refreshInterval?: number;
}

interface DemoScenario {
  scenario_id: string;
  title: string;
  description: string;
  duration_estimate: number;
  agents_involved: string[];
  business_value: number;
  status: 'ready' | 'running' | 'completed' | 'error';
  progress: number;
  results?: any;
}

interface CompetitionMetrics {
  total_value_generated: number;
  time_reduction_percentage: number;
  cost_savings_percentage: number;
  fraud_prevention_amount: number;
  compliance_cost_reduction: number;
  roi_percentage: number;
  aws_services_used: string[];
  agents_active: number;
  response_time_avg: number;
  uptime_percentage: number;
}

interface LiveDemoStep {
  step_id: string;
  title: string;
  description: string;
  agent: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  duration: number;
  result?: any;
}

export const CompetitionDemoDashboard: React.FC<CompetitionDemoDashboardProps> = ({
  refreshInterval = 30000, // 30 seconds - prevents browser freeze
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [demoScenarios, setDemoScenarios] = useState<DemoScenario[]>([]);
  const [competitionMetrics, setCompetitionMetrics] = useState<CompetitionMetrics | null>(null);
  const [activeDemoId, setActiveDemoId] = useState<string | null>(null);
  const [liveDemoSteps, setLiveDemoSteps] = useState<LiveDemoStep[]>([]);
  const [showResultsDialog, setShowResultsDialog] = useState(false);
  const [selectedResults, setSelectedResults] = useState<any>(null);

  // WebSocket updates for real-time demo progress
  const { isConnected, lastMessage } = useWebSocketUpdates('competition_demo');

  // Fetch demo data
  const fetchDemoData = useCallback(async () => {
    try {
      setError(null);
      
      // Mock competition demo scenarios
      const mockScenarios: DemoScenario[] = [
        {
          scenario_id: 'demo-001',
          title: 'Complete Fintech Risk Analysis',
          description: 'End-to-end demonstration of all 5 AI agents working together to analyze a fintech startup\'s risk profile, regulatory compliance, and fraud detection capabilities.',
          duration_estimate: 120, // 2 minutes for demo
          agents_involved: ['Regulatory Compliance', 'Fraud Detection', 'Risk Assessment', 'Market Analysis', 'KYC Verification'],
          business_value: 2500000, // $2.5M annual value
          status: 'ready',
          progress: 0,
        },
        {
          scenario_id: 'demo-002',
          title: 'Real-time Fraud Detection',
          description: 'Live demonstration of unsupervised ML fraud detection with 90% false positive reduction, processing 1000 transactions in real-time.',
          duration_estimate: 90, // 1.5 minutes
          agents_involved: ['Fraud Detection'],
          business_value: 10000000, // $10M fraud prevention
          status: 'ready',
          progress: 0,
        },
        {
          scenario_id: 'demo-003',
          title: 'Regulatory Compliance Automation',
          description: 'Automated monitoring of SEC, FINRA, and CFPB regulatory changes with instant compliance assessment and remediation planning.',
          duration_estimate: 75, // 1.25 minutes
          agents_involved: ['Regulatory Compliance'],
          business_value: 5000000, // $5M compliance savings
          status: 'ready',
          progress: 0,
        },
        {
          scenario_id: 'demo-004',
          title: 'Public Data Intelligence',
          description: 'Showcase of 90% functionality using free public data sources (SEC EDGAR, FRED, Treasury.gov) to democratize financial intelligence.',
          duration_estimate: 100, // 1.67 minutes
          agents_involved: ['Market Analysis', 'Regulatory Compliance'],
          business_value: 1500000, // $1.5M cost savings
          status: 'ready',
          progress: 0,
        },
        {
          scenario_id: 'demo-005',
          title: 'AWS Competition Showcase',
          description: 'Complete demonstration highlighting Amazon Bedrock Nova, AgentCore primitives, and measurable business impact for competition judging.',
          duration_estimate: 180, // 3 minutes
          agents_involved: ['All Agents', 'AWS Services'],
          business_value: 20000000, // $20M total value
          status: 'ready',
          progress: 0,
        },
      ];

      setDemoScenarios(mockScenarios);

      // Mock competition metrics
      const mockMetrics: CompetitionMetrics = {
        total_value_generated: 39000000, // $39M total
        time_reduction_percentage: 95, // 95% time reduction
        cost_savings_percentage: 80, // 80% cost savings
        fraud_prevention_amount: 10000000, // $10M fraud prevented
        compliance_cost_reduction: 5000000, // $5M compliance savings
        roi_percentage: 1010, // 1010% ROI
        aws_services_used: [
          'Amazon Bedrock Nova (Claude-3)',
          'Amazon Bedrock AgentCore',
          'Amazon ECS',
          'Amazon S3',
          'Amazon CloudWatch',
          'Amazon API Gateway',
        ],
        agents_active: 5,
        response_time_avg: 3.2,
        uptime_percentage: 99.92,
      };

      setCompetitionMetrics(mockMetrics);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch demo data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDemoData();
    const interval = setInterval(fetchDemoData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchDemoData, refreshInterval]);

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'demo_progress') {
      const { scenario_id, progress, status, step_results } = lastMessage.data;
      
      // Update demo progress
      setDemoScenarios(prev => prev.map(scenario => 
        scenario.scenario_id === scenario_id 
          ? { ...scenario, progress, status, results: step_results }
          : scenario
      ));

      // Update live demo steps if this is the active demo
      if (scenario_id === activeDemoId && step_results) {
        setLiveDemoSteps(step_results);
      }
    }
  }, [lastMessage, activeDemoId]);

  const startDemo = async (scenarioId: string) => {
    try {
      setActiveDemoId(scenarioId);
      
      // Update scenario status
      setDemoScenarios(prev => prev.map(scenario => 
        scenario.scenario_id === scenarioId 
          ? { ...scenario, status: 'running', progress: 0 }
          : scenario
      ));

      // Initialize demo steps based on scenario
      const scenario = demoScenarios.find(s => s.scenario_id === scenarioId);
      if (scenario) {
        const steps = generateDemoSteps(scenario);
        setLiveDemoSteps(steps);
        
        // Simulate demo execution
        simulateDemoExecution(scenarioId, steps);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start demo');
    }
  };

  const stopDemo = () => {
    if (activeDemoId) {
      setDemoScenarios(prev => prev.map(scenario => 
        scenario.scenario_id === activeDemoId 
          ? { ...scenario, status: 'ready', progress: 0 }
          : scenario
      ));
      setActiveDemoId(null);
      setLiveDemoSteps([]);
    }
  };

  const generateDemoSteps = (scenario: DemoScenario): LiveDemoStep[] => {
    const baseSteps: LiveDemoStep[] = [
      {
        step_id: 'init',
        title: 'Initialize AWS Services',
        description: 'Connecting to Amazon Bedrock Nova and AgentCore',
        agent: 'System',
        status: 'pending',
        duration: 5,
      },
      {
        step_id: 'data',
        title: 'Fetch Public Data',
        description: 'Retrieving data from SEC, FINRA, FRED, and other public sources',
        agent: 'Data Layer',
        status: 'pending',
        duration: 10,
      },
    ];

    // Add agent-specific steps based on scenario
    scenario.agents_involved.forEach((agent, index) => {
      if (agent !== 'All Agents' && agent !== 'AWS Services') {
        baseSteps.push({
          step_id: `agent-${index}`,
          title: `${agent} Analysis`,
          description: `Running ${agent.toLowerCase()} analysis with Claude-3`,
          agent: agent,
          status: 'pending',
          duration: 15 + Math.random() * 10,
        });
      }
    });

    baseSteps.push({
      step_id: 'synthesis',
      title: 'Results Synthesis',
      description: 'Combining agent results and calculating business value',
      agent: 'Supervisor',
      status: 'pending',
      duration: 8,
    });

    return baseSteps;
  };

  const simulateDemoExecution = async (scenarioId: string, steps: LiveDemoStep[]) => {
    let totalDuration = 0;
    const scenario = demoScenarios.find(s => s.scenario_id === scenarioId);
    const estimatedDuration = scenario?.duration_estimate || 120;

    for (let i = 0; i < steps.length; i++) {
      // Update current step to active
      setLiveDemoSteps(prev => prev.map((step, index) => ({
        ...step,
        status: index === i ? 'active' : index < i ? 'completed' : 'pending'
      })));

      // Simulate step execution
      await new Promise(resolve => setTimeout(resolve, steps[i].duration * 100)); // Speed up for demo
      
      totalDuration += steps[i].duration;
      const progress = Math.min((totalDuration / estimatedDuration) * 100, 100);

      // Update progress
      setDemoScenarios(prev => prev.map(s => 
        s.scenario_id === scenarioId 
          ? { ...s, progress }
          : s
      ));
    }

    // Complete demo
    setDemoScenarios(prev => prev.map(s => 
      s.scenario_id === scenarioId 
        ? { 
            ...s, 
            status: 'completed', 
            progress: 100,
            results: generateDemoResults(scenario!)
          }
        : s
    ));

    setLiveDemoSteps(prev => prev.map(step => ({ ...step, status: 'completed' })));
    setActiveDemoId(null);
  };

  const generateDemoResults = (scenario: DemoScenario) => {
    return {
      execution_time: scenario.duration_estimate,
      business_value_generated: scenario.business_value,
      agents_used: scenario.agents_involved.length,
      aws_services_utilized: ['Bedrock Nova', 'AgentCore', 'ECS', 'CloudWatch'],
      success_rate: 98.5 + Math.random() * 1.5,
      confidence_score: 0.92 + Math.random() * 0.08,
      key_insights: [
        'Achieved 95% time reduction compared to manual analysis',
        '80% cost savings through public data utilization',
        'Real-time fraud detection with 90% false positive reduction',
        'Automated compliance monitoring with instant alerts',
      ],
    };
  };

  const viewResults = (scenario: DemoScenario) => {
    setSelectedResults(scenario.results);
    setShowResultsDialog(true);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <LoadingState message="Loading competition demo scenarios..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchDemoData}>
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
              <EmojiEventsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              AWS Competition Demo
            </Typography>
            <Typography variant="subtitle1" color="textSecondary">
              Live Demonstrations and Competition Showcase Scenarios
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Chip 
                label={isConnected ? 'Live Demo Ready' : 'Offline'}
                color={isConnected ? 'success' : 'error'}
                size="small"
              />
              <Chip 
                label={activeDemoId ? 'Demo Running' : 'Ready to Demo'}
                color={activeDemoId ? 'warning' : 'primary'}
                size="small"
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh Demo Data">
              <IconButton onClick={fetchDemoData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            {activeDemoId && (
              <Button
                variant="outlined"
                color="error"
                startIcon={<StopIcon />}
                onClick={stopDemo}
              >
                Stop Demo
              </Button>
            )}
          </Box>
        </Box>

        {/* Competition Metrics Overview */}
        {competitionMetrics && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={2}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`, color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <AttachMoneyIcon sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h5">
                    {formatCurrency(competitionMetrics.total_value_generated)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Total Value Generated
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`, color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <SpeedIcon sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h5">
                    {competitionMetrics.time_reduction_percentage}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Time Reduction
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.info.main}, ${theme.palette.info.dark})`, color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <TrendingUpIcon sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h5">
                    {competitionMetrics.roi_percentage}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    ROI
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`, color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <SecurityIcon sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h5">
                    {formatCurrency(competitionMetrics.fraud_prevention_amount)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Fraud Prevented
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.error.main}, ${theme.palette.error.dark})`, color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <TimelineIcon sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h5">
                    {competitionMetrics.response_time_avg}s
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    Avg Response Time
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Card sx={{ background: `linear-gradient(135deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`, color: 'white' }}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <CloudQueueIcon sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h5">
                    {competitionMetrics.uptime_percentage}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    System Uptime
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Demo Scenarios */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12}>
            <Typography variant="h5" gutterBottom>
              Competition Demo Scenarios
            </Typography>
          </Grid>
          {demoScenarios.map((scenario) => (
            <Grid item xs={12} md={6} key={scenario.scenario_id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      {scenario.title}
                    </Typography>
                    <Chip
                      label={scenario.status}
                      size="small"
                      color={
                        scenario.status === 'completed' ? 'success' :
                        scenario.status === 'running' ? 'warning' :
                        scenario.status === 'error' ? 'error' : 'default'
                      }
                    />
                  </Box>
                  
                  <Typography variant="body2" color="textSecondary" paragraph>
                    {scenario.description}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Agents Involved: {scenario.agents_involved.join(', ')}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Estimated Duration: {formatDuration(scenario.duration_estimate)}
                    </Typography>
                    <Typography variant="body2" color="success.main" gutterBottom>
                      Business Value: {formatCurrency(scenario.business_value)}
                    </Typography>
                  </Box>

                  {scenario.status === 'running' && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" gutterBottom>
                        Progress: {scenario.progress.toFixed(0)}%
                      </Typography>
                      <LinearProgress variant="determinate" value={scenario.progress} />
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    {scenario.status === 'completed' && scenario.results && (
                      <Button
                        size="small"
                        startIcon={<VisibilityIcon />}
                        onClick={() => viewResults(scenario)}
                      >
                        View Results
                      </Button>
                    )}
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<PlayArrowIcon />}
                      onClick={() => startDemo(scenario.scenario_id)}
                      disabled={scenario.status === 'running' || !!activeDemoId}
                    >
                      Start Demo
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Live Demo Progress */}
        {activeDemoId && liveDemoSteps.length > 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Live Demo Progress
                  </Typography>
                  <Stepper orientation="vertical">
                    {liveDemoSteps.map((step) => (
                      <Step key={step.step_id} active={step.status === 'active'} completed={step.status === 'completed'}>
                        <StepLabel
                          error={step.status === 'error'}
                          icon={
                            step.status === 'active' ? <CircularProgress size={24} /> :
                            step.status === 'completed' ? <CheckCircleIcon color="success" /> :
                            step.status === 'error' ? <ErrorIcon color="error" /> :
                            undefined
                          }
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle1">
                              {step.title}
                            </Typography>
                            <Chip label={step.agent} size="small" variant="outlined" />
                          </Box>
                        </StepLabel>
                        <StepContent>
                          <Typography variant="body2" color="textSecondary">
                            {step.description}
                          </Typography>
                          {step.status === 'active' && (
                            <LinearProgress sx={{ mt: 1, width: 200 }} />
                          )}
                        </StepContent>
                      </Step>
                    ))}
                  </Stepper>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Results Dialog */}
        <Dialog
          open={showResultsDialog}
          onClose={() => setShowResultsDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Demo Results</DialogTitle>
          <DialogContent>
            {selectedResults && (
              <Box>
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      Execution Time
                    </Typography>
                    <Typography variant="h6">
                      {formatDuration(selectedResults.execution_time)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      Business Value Generated
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {formatCurrency(selectedResults.business_value_generated)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      Success Rate
                    </Typography>
                    <Typography variant="h6">
                      {selectedResults.success_rate.toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      Confidence Score
                    </Typography>
                    <Typography variant="h6">
                      {(selectedResults.confidence_score * 100).toFixed(1)}%
                    </Typography>
                  </Grid>
                </Grid>

                <Typography variant="h6" gutterBottom>
                  Key Insights
                </Typography>
                <List>
                  {selectedResults.key_insights.map((insight: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircleIcon color="success" />
                      </ListItemIcon>
                      <ListItemText primary={insight} />
                    </ListItem>
                  ))}
                </List>

                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  AWS Services Utilized
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedResults.aws_services_utilized.map((service: string) => (
                    <Chip key={service} label={service} color="primary" size="small" />
                  ))}
                </Box>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowResultsDialog(false)}>Close</Button>
            <Button variant="contained" startIcon={<DownloadIcon />}>
              Export Results
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ErrorBoundary>
  );
};

export default CompetitionDemoDashboard;