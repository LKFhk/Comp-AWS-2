/**
 * RiskIntel360 Design System - Fraud Heatmap Component
 * Color-coded heatmap for transaction fraud pattern visualization
 */

import React from 'react';
import { Box, Typography, Paper, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { getFraudHeatmapColor } from '../../utils/fintechVisualizations';

export interface FraudDataPoint {
  id: string;
  label: string;
  fraudProbability: number;
  metadata?: Record<string, any>;
}

interface FraudHeatmapProps {
  /**
   * Data points to visualize
   */
  data: FraudDataPoint[];
  /**
   * Number of columns in the grid
   */
  columns?: number;
  /**
   * Size of each cell
   */
  cellSize?: 'small' | 'medium' | 'large';
  /**
   * Show labels on cells
   */
  showLabels?: boolean;
  /**
   * Callback when a cell is clicked
   */
  onCellClick?: (dataPoint: FraudDataPoint) => void;
}

const HeatmapContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius * 2,
}));

interface HeatmapGridProps {
  columns: number;
  cellSize: 'small' | 'medium' | 'large';
}

const HeatmapGrid = styled(Box)<HeatmapGridProps>(({ columns, cellSize }) => {
  const sizeMap = {
    small: 40,
    medium: 60,
    large: 80,
  };

  return {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, ${sizeMap[cellSize]}px)`,
    gap: '4px',
    marginTop: '16px',
  };
});

interface HeatmapCellProps {
  cellSize: 'small' | 'medium' | 'large';
}

const HeatmapCell = styled(Box)<HeatmapCellProps>(({ theme, cellSize }) => {
  const sizeMap = {
    small: 40,
    medium: 60,
    large: 80,
  };

  return {
    width: sizeMap[cellSize],
    height: sizeMap[cellSize],
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.shape.borderRadius,
    cursor: 'pointer',
    transition: theme.transitions.create(['transform', 'box-shadow'], {
      duration: theme.transitions.duration.short,
    }),
    boxShadow: theme.shadows[1],
    '&:hover': {
      transform: 'scale(1.1)',
      boxShadow: theme.shadows[4],
      zIndex: 1,
    },
  };
});

const CellLabel = styled(Typography)(({ theme }) => ({
  fontWeight: theme.typography.fontWeightBold,
  fontSize: '0.625rem',
  color: theme.palette.common.white,
  textAlign: 'center',
  textShadow: '0 1px 2px rgba(0,0,0,0.5)',
}));

export const FraudHeatmap: React.FC<FraudHeatmapProps> = ({
  data,
  columns = 10,
  cellSize = 'medium',
  showLabels = false,
  onCellClick,
}) => {
  return (
    <HeatmapContainer elevation={2}>
      <Typography variant="h6" gutterBottom>
        Fraud Detection Heatmap
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Color-coded transaction fraud probability analysis
      </Typography>

      <HeatmapGrid columns={columns} cellSize={cellSize}>
        {data.map((dataPoint) => {
          const heatmapCell = getFraudHeatmapColor(dataPoint.fraudProbability);
          
          return (
            <Tooltip
              key={dataPoint.id}
              title={
                <Box>
                  <Typography variant="body2" fontWeight="bold">
                    {dataPoint.label}
                  </Typography>
                  <Typography variant="caption">
                    Fraud Probability: {(dataPoint.fraudProbability * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="caption" display="block">
                    Risk Level: {heatmapCell.label}
                  </Typography>
                  {dataPoint.metadata && (
                    <Box sx={{ mt: 1 }}>
                      {Object.entries(dataPoint.metadata).map(([key, value]) => (
                        <Typography key={key} variant="caption" display="block">
                          {key}: {String(value)}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              }
              arrow
            >
              <HeatmapCell
                cellSize={cellSize}
                onClick={() => onCellClick?.(dataPoint)}
                sx={{ backgroundColor: heatmapCell.color }}
              >
                {showLabels && cellSize !== 'small' && (
                  <CellLabel>
                    {(dataPoint.fraudProbability * 100).toFixed(0)}%
                  </CellLabel>
                )}
              </HeatmapCell>
            </Tooltip>
          );
        })}
      </HeatmapGrid>

      {/* Legend */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: getFraudHeatmapColor(0.1).color,
            }}
          />
          <Typography variant="caption">Safe (0-20%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: getFraudHeatmapColor(0.35).color,
            }}
          />
          <Typography variant="caption">Low Risk (20-50%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: getFraudHeatmapColor(0.65).color,
            }}
          />
          <Typography variant="caption">Suspicious (50-80%)</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: getFraudHeatmapColor(0.9).color,
            }}
          />
          <Typography variant="caption">High Risk (80-100%)</Typography>
        </Box>
      </Box>
    </HeatmapContainer>
  );
};

export default FraudHeatmap;
