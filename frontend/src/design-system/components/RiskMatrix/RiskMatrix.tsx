/**
 * RiskIntel360 Design System - Risk Matrix Component
 * Standard 3x3 risk assessment matrix for financial industry
 */

import React from 'react';
import { Box, Typography, Paper, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { riskMatrix, RiskMatrixCell } from '../../utils/fintechVisualizations';

interface RiskMatrixProps {
  /**
   * Current risk position (optional)
   */
  currentRisk?: {
    likelihood: 'low' | 'medium' | 'high';
    impact: 'low' | 'medium' | 'high';
  };
  /**
   * Show labels on cells
   */
  showLabels?: boolean;
  /**
   * Size of the matrix
   */
  size?: 'small' | 'medium' | 'large';
  /**
   * Callback when a cell is clicked
   */
  onCellClick?: (cell: RiskMatrixCell) => void;
}

const MatrixContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius * 2,
}));

const MatrixGrid = styled(Box)({
  display: 'grid',
  gridTemplateColumns: 'auto 1fr 1fr 1fr',
  gridTemplateRows: 'auto 1fr 1fr 1fr',
  gap: '8px',
  marginTop: '16px',
});

const AxisLabel = styled(Typography)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontWeight: theme.typography.fontWeightMedium,
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
}));

interface MatrixCellProps {
  size: 'small' | 'medium' | 'large';
  isActive?: boolean;
}

const MatrixCell = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'size' && prop !== 'isActive',
})<MatrixCellProps>(({ theme, size, isActive }) => {
  const sizeMap = {
    small: 60,
    medium: 80,
    large: 100,
  };

  return {
    width: sizeMap[size],
    height: sizeMap[size],
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.shape.borderRadius,
    cursor: 'pointer',
    transition: theme.transitions.create(['transform', 'box-shadow'], {
      duration: theme.transitions.duration.short,
    }),
    border: isActive ? `3px solid ${theme.palette.primary.main}` : '2px solid transparent',
    boxShadow: isActive ? theme.shadows[4] : theme.shadows[1],
    '&:hover': {
      transform: 'scale(1.05)',
      boxShadow: theme.shadows[4],
    },
  };
});

const CellLabel = styled(Typography)(({ theme }) => ({
  fontWeight: theme.typography.fontWeightBold,
  fontSize: '0.75rem',
  color: theme.palette.common.white,
  textAlign: 'center',
  textShadow: '0 1px 2px rgba(0,0,0,0.3)',
}));

export const RiskMatrix: React.FC<RiskMatrixProps> = ({
  currentRisk,
  showLabels = true,
  size = 'medium',
  onCellClick,
}) => {
  const isActiveCell = (cell: RiskMatrixCell): boolean => {
    if (!currentRisk) return false;
    return cell.likelihood === currentRisk.likelihood && cell.impact === currentRisk.impact;
  };

  return (
    <MatrixContainer elevation={2}>
      <Typography variant="h6" gutterBottom>
        Risk Assessment Matrix
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Evaluate risk based on likelihood and impact
      </Typography>

      <MatrixGrid>
        {/* Top-left corner (empty) */}
        <Box />

        {/* Column headers (Likelihood) */}
        <AxisLabel>Low</AxisLabel>
        <AxisLabel>Medium</AxisLabel>
        <AxisLabel>High</AxisLabel>

        {/* Row 1: High Impact */}
        <AxisLabel>High Impact</AxisLabel>
        {riskMatrix[0].map((cell, index) => (
          <Tooltip
            key={`high-${index}`}
            title={`${cell.label} Risk: ${cell.likelihood} likelihood, ${cell.impact} impact`}
            arrow
          >
            <MatrixCell
              size={size}
              isActive={isActiveCell(cell)}
              onClick={() => onCellClick?.(cell)}
              sx={{ backgroundColor: cell.color }}
            >
              {showLabels && <CellLabel>{cell.label}</CellLabel>}
            </MatrixCell>
          </Tooltip>
        ))}

        {/* Row 2: Medium Impact */}
        <AxisLabel>Medium Impact</AxisLabel>
        {riskMatrix[1].map((cell, index) => (
          <Tooltip
            key={`medium-${index}`}
            title={`${cell.label} Risk: ${cell.likelihood} likelihood, ${cell.impact} impact`}
            arrow
          >
            <MatrixCell
              size={size}
              isActive={isActiveCell(cell)}
              onClick={() => onCellClick?.(cell)}
              sx={{ backgroundColor: cell.color }}
            >
              {showLabels && <CellLabel>{cell.label}</CellLabel>}
            </MatrixCell>
          </Tooltip>
        ))}

        {/* Row 3: Low Impact */}
        <AxisLabel>Low Impact</AxisLabel>
        {riskMatrix[2].map((cell, index) => (
          <Tooltip
            key={`low-${index}`}
            title={`${cell.label} Risk: ${cell.likelihood} likelihood, ${cell.impact} impact`}
            arrow
          >
            <MatrixCell
              size={size}
              isActive={isActiveCell(cell)}
              onClick={() => onCellClick?.(cell)}
              sx={{ backgroundColor: cell.color }}
            >
              {showLabels && <CellLabel>{cell.label}</CellLabel>}
            </MatrixCell>
          </Tooltip>
        ))}
      </MatrixGrid>

      {/* Legend */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: riskMatrix[2][0].color,
            }}
          />
          <Typography variant="caption">Low Risk</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: riskMatrix[1][1].color,
            }}
          />
          <Typography variant="caption">Medium Risk</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: riskMatrix[0][1].color,
            }}
          />
          <Typography variant="caption">High Risk</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: 1,
              backgroundColor: riskMatrix[0][2].color,
            }}
          />
          <Typography variant="caption">Critical Risk</Typography>
        </Box>
      </Box>
    </MatrixContainer>
  );
};

export default RiskMatrix;
