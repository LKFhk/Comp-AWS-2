import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Scatter, Doughnut, Bar } from 'react-chartjs-2';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface RiskAssessmentChartProps {
  data: any;
}

const RiskAssessmentChart = ({ data }: RiskAssessmentChartProps) => {
  // Risk Matrix (Probability vs Impact)
  const riskMatrixData = {
    datasets: [
      {
        label: 'Market Risk',
        data: [{ x: 6, y: 7 }],
        backgroundColor: 'rgba(255, 99, 132, 0.8)',
        borderColor: 'rgba(255, 99, 132, 1)',
        pointRadius: 8,
      },
      {
        label: 'Financial Risk',
        data: [{ x: 4, y: 8 }],
        backgroundColor: 'rgba(54, 162, 235, 0.8)',
        borderColor: 'rgba(54, 162, 235, 1)',
        pointRadius: 8,
      },
      {
        label: 'Operational Risk',
        data: [{ x: 5, y: 5 }],
        backgroundColor: 'rgba(255, 206, 86, 0.8)',
        borderColor: 'rgba(255, 206, 86, 1)',
        pointRadius: 8,
      },
      {
        label: 'Technology Risk',
        data: [{ x: 7, y: 6 }],
        backgroundColor: 'rgba(75, 192, 192, 0.8)',
        borderColor: 'rgba(75, 192, 192, 1)',
        pointRadius: 8,
      },
      {
        label: 'Regulatory Risk',
        data: [{ x: 3, y: 9 }],
        backgroundColor: 'rgba(153, 102, 255, 0.8)',
        borderColor: 'rgba(153, 102, 255, 1)',
        pointRadius: 8,
      },
    ],
  };

  // Risk Category Distribution
  const riskDistributionData = {
    labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'],
    datasets: [
      {
        data: [35, 40, 20, 5],
        backgroundColor: [
          '#4CAF50',
          '#FF9800',
          '#FF5722',
          '#F44336',
        ],
        borderWidth: 2,
      },
    ],
  };

  // Risk Mitigation Timeline
  const mitigationTimelineData = {
    labels: ['Immediate', '1-3 Months', '3-6 Months', '6-12 Months', 'Long-term'],
    datasets: [
      {
        label: 'Risk Mitigation Actions',
        data: [8, 12, 6, 4, 2],
        backgroundColor: 'rgba(75, 192, 192, 0.8)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  const scatterOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Risk Matrix: Probability vs Impact',
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Probability (1-10)',
        },
        min: 0,
        max: 10,
        grid: {
          color: (context: any) => {
            if (context.tick.value === 3 || context.tick.value === 7) {
              return 'rgba(255, 99, 132, 0.3)';
            }
            return 'rgba(0, 0, 0, 0.1)';
          },
        },
      },
      y: {
        title: {
          display: true,
          text: 'Impact (1-10)',
        },
        min: 0,
        max: 10,
        grid: {
          color: (context: any) => {
            if (context.tick.value === 3 || context.tick.value === 7) {
              return 'rgba(255, 99, 132, 0.3)';
            }
            return 'rgba(0, 0, 0, 0.1)';
          },
        },
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
    },
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Risk Assessment Matrix
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Risk positioning based on probability and potential impact
            </Typography>
            <Box height={350}>
              <Scatter data={riskMatrixData} options={scatterOptions} />
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Risk Level Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Overall risk profile categorization
            </Typography>
            <Box height={300}>
              <Doughnut data={riskDistributionData} options={doughnutOptions} />
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Risk Mitigation Timeline
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Planned mitigation actions by timeframe
            </Typography>
            <Box height={300}>
              <Bar data={mitigationTimelineData} options={barOptions} />
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default RiskAssessmentChart;