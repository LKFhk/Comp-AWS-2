import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import { useNotification } from '../../contexts/NotificationContext';
import { apiService } from '../../services/api';

interface ValidationSummary {
  id: string;
  created_at: string;
  status: string;
  agent_type?: string;
  confidence_score?: number;
  processing_time?: number;
  time_reduction?: number;
  cost_savings?: number;
}

const Results: React.FC = () => {
  const [validations, setValidations] = useState<ValidationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const { showNotification } = useNotification();

  useEffect(() => {
    loadValidations();
  }, []);

  const loadValidations = async () => {
    try {
      // Load regular validations
      const data = await apiService.getValidations();
      const regularValidations = Array.isArray(data) ? data : (data.validations || []);
      
      // Also load demo executions with real execution IDs
      let demoValidations: ValidationSummary[] = [];
      try {
        const demoResponse = await fetch('http://localhost:8000/api/v1/demo/executions');
        if (demoResponse.ok) {
          const demoData = await demoResponse.json();
          if (demoData.executions && demoData.executions.length > 0) {
            // Map real demo executions to validation format
            demoValidations = demoData.executions.map((execution: any) => ({
              id: execution.execution_id, // Use real execution ID
              created_at: execution.created_at,
              status: execution.status,
              agent_type: `Demo: ${execution.scenario.replace(/_/g, ' ')}`,
              confidence_score: execution.confidence_score,
              processing_time: execution.processing_time_seconds,
              time_reduction: execution.time_reduction_percentage,
              cost_savings: execution.cost_savings_percentage
            }));
          }
        }
      } catch (demoError) {
        console.log('Demo executions not available:', demoError);
      }
      
      // Combine regular validations and demo executions
      setValidations([...regularValidations, ...demoValidations]);
    } catch (error) {
      console.error('Error loading validations:', error);
      showNotification('Error loading validations', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'in_progress':
      case 'processing':
        return 'info';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredValidations = validations.filter(v =>
    v.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.agent_type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <LoadingSpinner message="Loading results..." />;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Analysis Results
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            color="secondary"
            onClick={() => navigate('/competition-demo')}
          >
            Competition Demo
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/validation/new')}
          >
            New Analysis
          </Button>
        </Box>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            placeholder="Search financial risk analyses by ID, institution, or agent type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </CardContent>
      </Card>

      {filteredValidations.length === 0 ? (
        <Card>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No Results Found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {searchTerm ? 'Try adjusting your search criteria' : 'Start a new analysis to see results here'}
              </Typography>
              <Button
                variant="contained"
                color="primary"
                onClick={() => navigate('/validation/new')}
              >
                Start New Analysis
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Agent Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredValidations.map((validation) => (
                <TableRow key={validation.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {validation.id.substring(0, 8)}...
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={validation.agent_type || 'Unknown'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={validation.status}
                      color={getStatusColor(validation.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {validation.confidence_score ? 
                      `${(validation.confidence_score * 100).toFixed(1)}%` : 
                      'N/A'
                    }
                  </TableCell>
                  <TableCell>
                    {format(new Date(validation.created_at), 'MMM dd, yyyy HH:mm')}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => navigate(`/validation/${validation.id}/results`)}
                      title="View Results"
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default Results;
