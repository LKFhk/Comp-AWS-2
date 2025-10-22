/**
 * RiskIntel360 Design System - Compliance Gauge Component
 * Circular gauge chart for compliance score visualization (0-100 scale)
 */

import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';
import { getComplianceGaugeConfig } from '../../utils/fintechVisualizations';

interface ComplianceGaugeProps {
  /**
   * Compliance score (0-100)
   */
  score: number;
  /**
   * Label for the gauge
   */
  label?: string;
  /**
   * Size of the gauge
   */
  size?: 'small' | 'medium' | 'large';
  /**
   * Show score label
   */
  showScore?: boolean;
  /**
   * Show status label
   */
  showStatus?: boolean;
}

const GaugeContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 2,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: theme.spacing(2),
}));

interface GaugeSvgProps {
  size: 'small' | 'medium' | 'large';
}

const GaugeSvg = styled('svg')<GaugeSvgProps>(({ size }) => {
  const sizeMap = {
    small: 120,
    medium: 160,
    large: 200,
  };

  return {
    width: sizeMap[size],
    height: sizeMap[size],
  };
});

const ScoreText = styled(Typography)(({ theme }) => ({
  fontWeight: theme.typography.fontWeightBold,
  fontSize: '2rem',
  lineHeight: 1,
}));

const StatusText = styled(Typography)(({ theme }) => ({
  fontWeight: theme.typography.fontWeightMedium,
  fontSize: '0.875rem',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
}));

export const ComplianceGauge: React.FC<ComplianceGaugeProps> = ({
  score,
  label = 'Compliance Score',
  size = 'medium',
  showScore = true,
  showStatus = true,
}) => {
  const config = getComplianceGaugeConfig(score);
  
  const sizeMap = {
    small: 120,
    medium: 160,
    large: 200,
  };
  
  const svgSize = sizeMap[size];
  const center = svgSize / 2;
  const radius = (svgSize / 2) - 20;
  const strokeWidth = size === 'small' ? 12 : size === 'medium' ? 16 : 20;
  
  // Calculate arc path for the gauge
  const startAngle = -135; // Start at bottom-left
  const endAngle = 135; // End at bottom-right
  const totalAngle = endAngle - startAngle;
  const scoreAngle = startAngle + (totalAngle * (score / 100));
  
  const polarToCartesian = (angle: number) => {
    const angleInRadians = (angle * Math.PI) / 180;
    return {
      x: center + radius * Math.cos(angleInRadians),
      y: center + radius * Math.sin(angleInRadians),
    };
  };
  
  const backgroundStart = polarToCartesian(startAngle);
  const backgroundEnd = polarToCartesian(endAngle);
  const scoreEnd = polarToCartesian(scoreAngle);
  
  const largeArcFlag = totalAngle > 180 ? 1 : 0;
  const scoreLargeArcFlag = (scoreAngle - startAngle) > 180 ? 1 : 0;
  
  const backgroundPath = `
    M ${backgroundStart.x} ${backgroundStart.y}
    A ${radius} ${radius} 0 ${largeArcFlag} 1 ${backgroundEnd.x} ${backgroundEnd.y}
  `;
  
  const scorePath = `
    M ${backgroundStart.x} ${backgroundStart.y}
    A ${radius} ${radius} 0 ${scoreLargeArcFlag} 1 ${scoreEnd.x} ${scoreEnd.y}
  `;

  return (
    <GaugeContainer elevation={2}>
      {label && (
        <Typography variant="h6" align="center">
          {label}
        </Typography>
      )}
      
      <Box sx={{ position: 'relative', display: 'inline-block' }}>
        <GaugeSvg size={size} viewBox={`0 0 ${svgSize} ${svgSize}`}>
          {/* Background arc */}
          <path
            d={backgroundPath}
            fill="none"
            stroke="#e0e0e0"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          
          {/* Score arc */}
          <path
            d={scorePath}
            fill="none"
            stroke={config.color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 1s ease-in-out',
            }}
          />
          
          {/* Center circle for score display */}
          {showScore && (
            <circle
              cx={center}
              cy={center}
              r={radius - strokeWidth - 10}
              fill="white"
              stroke="#e0e0e0"
              strokeWidth="2"
            />
          )}
        </GaugeSvg>
        
        {/* Score text overlay */}
        {showScore && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
            }}
          >
            <ScoreText sx={{ color: config.color }}>
              {Math.round(score)}
            </ScoreText>
            <Typography variant="caption" color="text.secondary">
              / 100
            </Typography>
          </Box>
        )}
      </Box>
      
      {showStatus && (
        <StatusText sx={{ color: config.color }}>
          {config.label}
        </StatusText>
      )}
    </GaugeContainer>
  );
};

export default ComplianceGauge;
