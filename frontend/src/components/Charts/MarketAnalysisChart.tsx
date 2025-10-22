import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface MarketAnalysisChartProps {
  data: any;
}

const MarketAnalysisChart = ({ data }: MarketAnalysisChartProps) => {
  if (!data) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6">Market Analysis</Typography>
          <Typography color="text.secondary">No market data available</Typography>
        </CardContent>
      </Card>
    );
  }

  const chartData = {
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
    datasets: [
      {
        label: 'Market Growth',
        data: [12, 19, 3, 5],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Market Analysis Chart',
      },
    },
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Market Analysis
            </Typography>
            <Box sx={{ height: 400 }}>
              <Line data={chartData} options={options} />
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default MarketAnalysisChart;