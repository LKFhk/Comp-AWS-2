/**
 * Compliance Monitoring Dashboard Component
 * Real-time regulatory alerts and compliance status monitoring
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Badge,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { 
  ComplianceAssessment, 
  ComplianceStatus, 
  RiskLevel, 
  FinancialAlert 
} from '../../types/fintech';
import { fintechService } from '../../services/fintechService';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';

interface ComplianceMonitoringDashboardProps {
  businessType?: string;
  jurisdiction?: string;
  onAlertClick?: (alert: FinancialAlert) => void;
  refreshInterval?: number;
}

interface ComplianceSummary {
  totalRegulations: number;
  compliantCount: number;
  nonCompliantCount: number;
  pendingReviewCount: number;
  overallScore: number;
  lastUpdated: string;
}

export const ComplianceMonitoringDashboard = ({
  businessType = 'fintech',
  jurisdiction = 'US',
  onAlertClick,
  refreshInterval = 30000, // 30 seconds
}: ComplianceMonitoringDashboardProps) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [complianceData, setComplianceData] = useState<ComplianceAssessment[]>([]);
  const [alerts, setAlerts] = useState<FinancialAlert[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<FinancialAlert | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Fetch compliance data
  const fetchComplianceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Simulate async data fetch with a small delay
      await new Promise(resolve => setTimeout(resolve, 10));

      // Simulate compliance validation data for financial risk assessment
      const mockComplianceData: ComplianceAssessment[] = [
        {
          regulation_id: 'SEC-REG-001',
          regulation_name: 'SEC Securities Registration & Reporting (SEC.gov)',
          compliance_status: ComplianceStatus.COMPLIANT,
          risk_level: RiskLevel.LOW,
          requirements: ['File quarterly 10-Q reports per SEC Rule 13a-13', 'Maintain comprehensive audit trail per SEC Rule 17a-4', 'Disclose material events per SEC Regulation S-K'],
          gaps: [],
          remediation_plan: {},
          confidence_score: 0.95,
          ai_reasoning: 'All SEC filing requirements validated per SEC.gov guidance. Entity maintains proper documentation and timely reporting in compliance with Securities Exchange Act of 1934.',
        },
        {
          regulation_id: 'FINRA-REG-002',
          regulation_name: 'FINRA Customer Protection & Trade Reporting (FINRA.org)',
          compliance_status: ComplianceStatus.REQUIRES_REVIEW,
          risk_level: RiskLevel.MEDIUM,
          requirements: ['Customer suitability assessment per FINRA Rule 2111', 'Real-time trade reporting per FINRA Rule 6380', 'Risk disclosure documentation per FINRA Rule 2210'],
          gaps: ['Missing customer risk profiles for 15% of high-value accounts - violates FINRA Rule 2111 suitability requirements', 'Incomplete suitability assessments for complex products - requires enhanced documentation per FINRA.org guidance'],
          remediation_plan: {
            action: 'Complete customer risk assessments per FINRA Rule 2111 and enhance suitability documentation following FINRA.org best practices',
            timeline: '30 days',
            responsible_party: 'Compliance & Risk Management Team',
            estimated_cost: '$45,000',
            regulatory_guidance: 'FINRA Regulatory Notice 12-25: Suitability Obligations'
          },
          confidence_score: 0.78,
          ai_reasoning: 'Most FINRA requirements validated per FINRA.org standards, but customer risk profiling gaps require immediate attention to avoid regulatory penalties under FINRA Rule 2111.',
        },
        {
          regulation_id: 'CFPB-REG-003',
          regulation_name: 'CFPB Consumer Financial Protection (CFPB.gov)',
          compliance_status: ComplianceStatus.NON_COMPLIANT,
          risk_level: RiskLevel.HIGH,
          requirements: ['Fair lending practices validation per ECOA/Regulation B', 'Consumer protection disclosures per TILA/Regulation Z', 'Complaint handling procedures per CFPB Bulletin 2012-06'],
          gaps: ['Incomplete fair lending statistical analysis - violates ECOA requirements monitored by CFPB.gov', 'Missing consumer disclosure documentation - non-compliant with TILA/Regulation Z', 'Inadequate complaint resolution tracking - fails CFPB Bulletin 2012-06 standards'],
          remediation_plan: {
            action: 'Implement comprehensive fair lending program per ECOA/Regulation B and enhance consumer protection measures following CFPB.gov guidance',
            timeline: '60 days',
            responsible_party: 'Legal, Compliance & Operations',
            estimated_cost: '$125,000',
            regulatory_guidance: 'CFPB Compliance Bulletin 2012-06: Fair Lending Examination Procedures'
          },
          confidence_score: 0.85,
          ai_reasoning: 'Critical compliance gaps identified in consumer protection measures per CFPB.gov standards. Immediate remediation required to avoid CFPB enforcement actions under ECOA and potential fines.',
        },
        {
          regulation_id: 'MIFID-REG-004',
          regulation_name: 'MiFID II Market Conduct & Transparency',
          compliance_status: ComplianceStatus.COMPLIANT,
          risk_level: RiskLevel.LOW,
          requirements: ['Best execution reporting per MiFID II Article 27', 'Transaction reporting per MiFID II RTS 22', 'Product governance per MiFID II Article 16(3)'],
          gaps: [],
          remediation_plan: {},
          confidence_score: 0.92,
          ai_reasoning: 'MiFID II requirements validated for EU operations. Best execution policies and transaction reporting systems meet regulatory standards.',
        },
        {
          regulation_id: 'BASEL-REG-005',
          regulation_name: 'Basel III Capital & Liquidity Requirements',
          compliance_status: ComplianceStatus.REQUIRES_REVIEW,
          risk_level: RiskLevel.MEDIUM,
          requirements: ['Maintain minimum CET1 ratio of 4.5% per Basel III', 'Liquidity Coverage Ratio (LCR) ≥ 100%', 'Net Stable Funding Ratio (NSFR) ≥ 100%'],
          gaps: ['LCR approaching minimum threshold - requires enhanced liquidity management', 'Stress testing documentation needs quarterly updates per Basel III standards'],
          remediation_plan: {
            action: 'Enhance liquidity management framework and update stress testing procedures per Basel III guidelines',
            timeline: '45 days',
            responsible_party: 'Treasury & Risk Management',
            estimated_cost: '$75,000',
            regulatory_guidance: 'Basel Committee on Banking Supervision: Basel III Framework'
          },
          confidence_score: 0.81,
          ai_reasoning: 'Capital ratios meet Basel III requirements, but liquidity metrics require monitoring and enhanced stress testing documentation.',
        },
      ];

      setComplianceData(mockComplianceData);

      // Calculate summary
      const totalRegulations = mockComplianceData.length;
      const compliantCount = mockComplianceData.filter(
        (item) => item.compliance_status === ComplianceStatus.COMPLIANT
      ).length;
      const nonCompliantCount = mockComplianceData.filter(
        (item) => item.compliance_status === ComplianceStatus.NON_COMPLIANT
      ).length;
      const pendingReviewCount = mockComplianceData.filter(
        (item) => item.compliance_status === ComplianceStatus.REQUIRES_REVIEW
      ).length;

      setSummary({
        totalRegulations,
        compliantCount,
        nonCompliantCount,
        pendingReviewCount,
        overallScore: (compliantCount / totalRegulations) * 100,
        lastUpdated: new Date().toISOString(),
      });

      // Mock compliance validation alerts
      const mockAlerts: FinancialAlert[] = [
        {
          alert_id: 'ALERT-001',
          alert_type: 'compliance',
          severity: 'high',
          title: 'CFPB Regulation Non-Compliance Detected (CFPB.gov)',
          description: 'Critical compliance gaps identified in consumer protection measures per CFPB.gov standards. Estimated regulatory penalty risk: $500K-$2M under ECOA enforcement.',
          created_at: new Date().toISOString(),
          metadata: { 
            regulation_id: 'CFPB-REG-003',
            risk_score: 0.82,
            estimated_penalty: '$500,000 - $2,000,000',
            remediation_cost: '$125,000',
            regulatory_source: 'CFPB.gov',
            guidance_reference: 'CFPB Compliance Bulletin 2012-06'
          },
        },
        {
          alert_id: 'ALERT-002',
          alert_type: 'regulatory_update',
          severity: 'medium',
          title: 'New SEC Cybersecurity Disclosure Requirements (SEC.gov)',
          description: 'Updated cybersecurity incident reporting requirements per SEC.gov effective Q1 2025. Compliance validation required under Securities Exchange Act amendments.',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          metadata: {
            effective_date: '2025-01-01',
            impact_level: 'medium',
            preparation_time: '90 days',
            regulatory_source: 'SEC.gov',
            guidance_reference: 'SEC Release No. 34-97989'
          },
        },
        {
          alert_id: 'ALERT-003',
          alert_type: 'compliance',
          severity: 'medium',
          title: 'FINRA Customer Risk Profile Gaps (FINRA.org)',
          description: '15% of high-value accounts missing required risk assessments per FINRA Rule 2111. Potential regulatory examination finding based on FINRA.org guidance.',
          created_at: new Date(Date.now() - 7200000).toISOString(),
          metadata: {
            regulation_id: 'FINRA-REG-002',
            affected_accounts: 127,
            risk_score: 0.65,
            remediation_timeline: '30 days',
            regulatory_source: 'FINRA.org',
            guidance_reference: 'FINRA Regulatory Notice 12-25'
          },
        },
        {
          alert_id: 'ALERT-004',
          alert_type: 'regulatory_update',
          severity: 'low',
          title: 'Basel III Liquidity Monitoring Update',
          description: 'Enhanced liquidity stress testing requirements per Basel Committee guidance. Review and update procedures recommended.',
          created_at: new Date(Date.now() - 10800000).toISOString(),
          metadata: {
            regulation_id: 'BASEL-REG-005',
            impact_level: 'low',
            preparation_time: '45 days',
            regulatory_source: 'Basel Committee on Banking Supervision',
            guidance_reference: 'Basel III Framework - Liquidity Standards'
          },
        },
      ];

      setAlerts(mockAlerts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch compliance data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplianceData();
    const interval = setInterval(fetchComplianceData, refreshInterval);
    return () => clearInterval(interval);
  }, [businessType, jurisdiction, refreshInterval]);

  const getStatusColor = (status: ComplianceStatus) => {
    switch (status) {
      case ComplianceStatus.COMPLIANT:
        return theme.palette.success.main;
      case ComplianceStatus.NON_COMPLIANT:
        return theme.palette.error.main;
      case ComplianceStatus.REQUIRES_REVIEW:
        return theme.palette.warning.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getStatusIcon = (status: ComplianceStatus) => {
    switch (status) {
      case ComplianceStatus.COMPLIANT:
        return <CheckCircleIcon color="success" />;
      case ComplianceStatus.NON_COMPLIANT:
        return <ErrorIcon color="error" />;
      case ComplianceStatus.REQUIRES_REVIEW:
        return <WarningIcon color="warning" />;
      default:
        return <ScheduleIcon color="disabled" />;
    }
  };

  const getRiskLevelColor = (riskLevel: RiskLevel) => {
    switch (riskLevel) {
      case RiskLevel.LOW:
        return theme.palette.success.main;
      case RiskLevel.MEDIUM:
        return theme.palette.warning.main;
      case RiskLevel.HIGH:
        return theme.palette.error.main;
      case RiskLevel.CRITICAL:
        return theme.palette.error.dark;
      default:
        return theme.palette.grey[500];
    }
  };

  const handleAlertClick = (alert: FinancialAlert) => {
    setSelectedAlert(alert);
    setDialogOpen(true);
    onAlertClick?.(alert);
  };

  const handleExportReport = () => {
    // Implementation for exporting compliance report
    console.log('Exporting compliance report...');
  };

  if (loading) {
    return <LoadingState message="Loading compliance data..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchComplianceData}>
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
          <Typography variant="h4" component="h1">
            Regulatory Compliance Monitoring
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh Data">
              <IconButton onClick={fetchComplianceData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportReport}
            >
              Export Report
            </Button>
          </Box>
        </Box>

        {/* Summary Cards */}
        {summary && (
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Overall Compliance Score
                  </Typography>
                  <Typography variant="h4" component="div">
                    {summary.overallScore.toFixed(1)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={summary.overallScore}
                    sx={{ mt: 1 }}
                    color={summary.overallScore >= 80 ? 'success' : summary.overallScore >= 60 ? 'warning' : 'error'}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Compliant Regulations
                  </Typography>
                  <Typography variant="h4" component="div" color="success.main">
                    {summary.compliantCount}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    of {summary.totalRegulations} total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Requires Review
                  </Typography>
                  <Typography variant="h4" component="div" color="warning.main">
                    {summary.pendingReviewCount}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    pending action
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Non-Compliant
                  </Typography>
                  <Typography variant="h4" component="div" color="error.main">
                    {summary.nonCompliantCount}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    critical issues
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Grid container spacing={3}>
          {/* Compliance Status List */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Regulatory Compliance Status
                </Typography>
                <List>
                  {complianceData.map((item, index) => (
                    <React.Fragment key={item.regulation_id}>
                      <ListItem>
                        <ListItemIcon>
                          {getStatusIcon(item.compliance_status)}
                        </ListItemIcon>
                        <ListItemText
                          primaryTypographyProps={{ component: 'div' }}
                          secondaryTypographyProps={{ component: 'div' }}
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                              <Typography variant="subtitle1">
                                {item.regulation_name}
                              </Typography>
                              <Chip
                                label={item.compliance_status.replace('_', ' ')}
                                size="small"
                                sx={{
                                  backgroundColor: getStatusColor(item.compliance_status),
                                  color: 'white',
                                }}
                              />
                              <Chip
                                label={item.risk_level}
                                size="small"
                                variant="outlined"
                                sx={{
                                  borderColor: getRiskLevelColor(item.risk_level),
                                  color: getRiskLevelColor(item.risk_level),
                                }}
                              />
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="body2" color="textSecondary">
                                {item.ai_reasoning}
                              </Typography>
                              {item.gaps.length > 0 && (
                                <Box sx={{ mt: 1 }}>
                                  <Typography variant="body2" color="error.main" fontWeight="bold">
                                    Compliance Gaps:
                                  </Typography>
                                  {item.gaps.map((gap, idx) => (
                                    <Typography key={idx} variant="body2" color="error.main" sx={{ ml: 2 }}>
                                      • {gap}
                                    </Typography>
                                  ))}
                                </Box>
                              )}
                              {item.remediation_plan && Object.keys(item.remediation_plan).length > 0 && (
                                <Box sx={{ mt: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                                  <Typography variant="body2" fontWeight="bold">
                                    Remediation Plan:
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    {item.remediation_plan.action}
                                  </Typography>
                                  {item.remediation_plan.regulatory_guidance && (
                                    <Typography variant="caption" color="primary.main" sx={{ mt: 0.5, display: 'block' }}>
                                      Guidance: {item.remediation_plan.regulatory_guidance}
                                    </Typography>
                                  )}
                                </Box>
                              )}
                              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                                Confidence: {(item.confidence_score * 100).toFixed(1)}%
                              </Typography>
                            </Box>
                          }
                        />
                        <IconButton size="small">
                          <VisibilityIcon />
                        </IconButton>
                      </ListItem>
                      {index < complianceData.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Alerts Panel */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <NotificationsIcon />
                  <Typography variant="h6">
                    Active Alerts
                  </Typography>
                  <Badge badgeContent={alerts.length} color="error" />
                </Box>
                <List dense>
                  {alerts.map((alert) => (
                    <ListItem
                      key={alert.alert_id}
                      button
                      onClick={() => handleAlertClick(alert)}
                      sx={{
                        border: 1,
                        borderColor: alert.severity === 'high' ? 'error.main' : 'warning.main',
                        borderRadius: 1,
                        mb: 1,
                      }}
                    >
                      <ListItemText
                        primaryTypographyProps={{ component: 'div' }}
                        secondaryTypographyProps={{ component: 'div' }}
                        primary={alert.title}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              {alert.description}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {new Date(alert.created_at).toLocaleString()}
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip
                        label={alert.severity}
                        size="small"
                        color={alert.severity === 'high' ? 'error' : 'warning'}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Alert Detail Dialog */}
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Alert Details
          </DialogTitle>
          <DialogContent>
            {selectedAlert && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  {selectedAlert.title}
                </Typography>
                <Typography variant="body1" paragraph>
                  {selectedAlert.description}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Chip label={`Severity: ${selectedAlert.severity}`} />
                  <Chip label={`Type: ${selectedAlert.alert_type}`} />
                </Box>
                <Typography variant="body2" color="textSecondary">
                  Created: {new Date(selectedAlert.created_at).toLocaleString()}
                </Typography>
                {selectedAlert.metadata && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Additional Information:
                    </Typography>
                    <Typography 
                      component="div" 
                      sx={{ 
                        fontSize: '0.875rem', 
                        color: 'text.secondary',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                        backgroundColor: 'grey.100',
                        p: 1,
                        borderRadius: 1
                      }}
                    >
                      {JSON.stringify(selectedAlert.metadata, null, 2)}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>
              Close
            </Button>
            <Button variant="contained" onClick={() => setDialogOpen(false)}>
              Mark as Resolved
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ErrorBoundary>
  );
};

export default ComplianceMonitoringDashboard;