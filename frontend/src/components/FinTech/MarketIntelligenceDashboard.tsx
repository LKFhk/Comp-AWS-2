/**
 * Market Intelligence Dashboard Component
 * Interactive financial charts and trend analysis
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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Analytics as AnalyticsIcon,
  ShowChart as ShowChartIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { 
  MarketIntelligence, 
  MarketTrend,
  FinancialAlert 
} from '../../types/fintech';
import { fintechService } from '../../services/fintechService';
import { LoadingState } from '../../design-system/components/LoadingState/LoadingState';
import { ErrorBoundary } from '../../design-system/components/ErrorBoundary/ErrorBoundary';

interface MarketIntelligenceDashboardProps {
  defaultMarketSegment?: string;
  onAlertClick?: (alert: FinancialAlert) => void;
  refreshInterval?: number;
}

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  timestamp: string;
}

interface EconomicIndicator {
  name: string;
  value: number;
  change: number;
  unit: string;
  lastUpdated: string;
  trend: MarketTrend;
}

interface MarketSummary {
  totalMarkets: number;
  bullishMarkets: number;
  bearishMarkets: number;
  neutralMarkets: number;
  avgVolatility: number;
  marketSentiment: string;
  lastUpdated: string;
}

export const MarketIntelligenceDashboard: React.FC<MarketIntelligenceDashboardProps> = ({
  defaultMarketSegment = 'fintech',
  onAlertClick,
  refreshInterval = 60000, // 1 minute
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketIntelligence, setMarketIntelligence] = useState<MarketIntelligence[]>([]);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [economicIndicators, setEconomicIndicators] = useState<EconomicIndicator[]>([]);
  const [alerts, setAlerts] = useState<FinancialAlert[]>([]);
  const [summary, setSummary] = useState<MarketSummary | null>(null);
  const [selectedMarket, setSelectedMarket] = useState<MarketIntelligence | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState(defaultMarketSegment);
  const [tabValue, setTabValue] = useState(0);

  // Fetch market intelligence data
  const fetchMarketData = useCallback(async () => {
    try {
      setError(null);
      
      const response = await fintechService.getMarketIntelligence({
        market_segment: selectedSegment,
        analysis_type: ['trend_analysis', 'volatility_analysis', 'sentiment_analysis'],
        time_horizon: '1d',
        data_sources: ['yahoo_finance', 'fred', 'news_apis'],
      });

      // Mock market intelligence data
      const mockMarketIntelligence: MarketIntelligence[] = [
        {
          market_segment: 'fintech',
          trend_direction: MarketTrend.BULLISH,
          volatility_level: 0.25,
          key_drivers: ['Digital payment adoption', 'Regulatory clarity', 'AI integration'],
          risk_factors: ['Interest rate changes', 'Regulatory uncertainty'],
          opportunities: ['Embedded finance', 'DeFi integration', 'AI-powered services'],
          data_sources: ['yahoo_finance', 'fred', 'financial_news'],
          confidence_score: 0.87,
          ai_insights: 'Fintech sector showing strong momentum driven by increased digital adoption and favorable regulatory environment.',
        },
        {
          market_segment: 'cryptocurrency',
          trend_direction: MarketTrend.VOLATILE,
          volatility_level: 0.65,
          key_drivers: ['Institutional adoption', 'Regulatory developments', 'Market sentiment'],
          risk_factors: ['Regulatory crackdowns', 'Market manipulation', 'Technical issues'],
          opportunities: ['ETF approvals', 'Central bank digital currencies', 'DeFi protocols'],
          data_sources: ['crypto_exchanges', 'news_apis', 'social_sentiment'],
          confidence_score: 0.72,
          ai_insights: 'Cryptocurrency markets remain highly volatile with mixed signals from regulatory and institutional fronts.',
        },
        {
          market_segment: 'traditional_banking',
          trend_direction: MarketTrend.NEUTRAL,
          volatility_level: 0.15,
          key_drivers: ['Interest rate environment', 'Credit quality', 'Digital transformation'],
          risk_factors: ['Economic slowdown', 'Credit losses', 'Fintech competition'],
          opportunities: ['Digital banking', 'Wealth management', 'Commercial lending'],
          data_sources: ['fed_data', 'bank_earnings', 'economic_indicators'],
          confidence_score: 0.81,
          ai_insights: 'Traditional banking sector showing stability with gradual digital transformation initiatives.',
        },
      ];

      setMarketIntelligence(mockMarketIntelligence);

      // Mock market data (stock prices, etc.)
      const mockMarketData: MarketData[] = [
        {
          symbol: 'PYPL',
          price: 58.42,
          change: 2.15,
          changePercent: 3.82,
          volume: 12500000,
          marketCap: 65800000000,
          timestamp: new Date().toISOString(),
        },
        {
          symbol: 'SQ',
          price: 72.18,
          change: -1.23,
          changePercent: -1.68,
          volume: 8900000,
          marketCap: 41200000000,
          timestamp: new Date().toISOString(),
        },
        {
          symbol: 'V',
          price: 245.67,
          change: 4.32,
          changePercent: 1.79,
          volume: 3200000,
          marketCap: 520000000000,
          timestamp: new Date().toISOString(),
        },
      ];

      setMarketData(mockMarketData);

      // Mock economic indicators
      const mockEconomicIndicators: EconomicIndicator[] = [
        {
          name: 'Federal Funds Rate',
          value: 5.25,
          change: 0.25,
          unit: '%',
          lastUpdated: new Date().toISOString(),
          trend: MarketTrend.BULLISH,
        },
        {
          name: 'GDP Growth Rate',
          value: 2.4,
          change: 0.1,
          unit: '%',
          lastUpdated: new Date(Date.now() - 86400000).toISOString(),
          trend: MarketTrend.NEUTRAL,
        },
        {
          name: 'Inflation Rate (CPI)',
          value: 3.2,
          change: -0.3,
          unit: '%',
          lastUpdated: new Date(Date.now() - 172800000).toISOString(),
          trend: MarketTrend.BEARISH,
        },
        {
          name: 'Unemployment Rate',
          value: 3.7,
          change: -0.1,
          unit: '%',
          lastUpdated: new Date(Date.now() - 259200000).toISOString(),
          trend: MarketTrend.BEARISH,
        },
      ];

      setEconomicIndicators(mockEconomicIndicators);

      // Calculate summary
      const totalMarkets = mockMarketIntelligence.length;
      const bullishMarkets = mockMarketIntelligence.filter(m => m.trend_direction === MarketTrend.BULLISH).length;
      const bearishMarkets = mockMarketIntelligence.filter(m => m.trend_direction === MarketTrend.BEARISH).length;
      const neutralMarkets = mockMarketIntelligence.filter(m => m.trend_direction === MarketTrend.NEUTRAL).length;
      const avgVolatility = mockMarketIntelligence.reduce((sum, m) => sum + m.volatility_level, 0) / totalMarkets;

      setSummary({
        totalMarkets,
        bullishMarkets,
        bearishMarkets,
        neutralMarkets,
        avgVolatility: avgVolatility * 100,
        marketSentiment: bullishMarkets > bearishMarkets ? 'Positive' : bearishMarkets > bullishMarkets ? 'Negative' : 'Neutral',
        lastUpdated: new Date().toISOString(),
      });

      // Mock market alerts
      const mockAlerts: FinancialAlert[] = [
        {
          alert_id: 'MKT-001',
          alert_type: 'market_volatility',
          severity: 'medium',
          title: 'Increased Volatility in Crypto Markets',
          description: 'Cryptocurrency markets showing 65% volatility spike',
          created_at: new Date().toISOString(),
          metadata: { market_segment: 'cryptocurrency', volatility_level: 0.65 },
        },
        {
          alert_id: 'MKT-002',
          alert_type: 'economic_indicator',
          severity: 'low',
          title: 'Fed Rate Decision Impact',
          description: 'Federal funds rate increase affecting fintech valuations',
          created_at: new Date(Date.now() - 1800000).toISOString(),
          metadata: { indicator: 'federal_funds_rate', impact: 'moderate' },
        },
      ];

      setAlerts(mockAlerts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch market intelligence data');
    } finally {
      setLoading(false);
    }
  }, [selectedSegment]);

  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMarketData, refreshInterval]);

  const getTrendIcon = (trend: MarketTrend) => {
    switch (trend) {
      case MarketTrend.BULLISH:
        return <TrendingUpIcon color="success" />;
      case MarketTrend.BEARISH:
        return <TrendingDownIcon color="error" />;
      case MarketTrend.VOLATILE:
        return <TimelineIcon color="warning" />;
      default:
        return <TrendingFlatIcon color="info" />;
    }
  };

  const getTrendColor = (trend: MarketTrend) => {
    switch (trend) {
      case MarketTrend.BULLISH:
        return theme.palette.success.main;
      case MarketTrend.BEARISH:
        return theme.palette.error.main;
      case MarketTrend.VOLATILE:
        return theme.palette.warning.main;
      default:
        return theme.palette.info.main;
    }
  };

  const handleMarketClick = (market: MarketIntelligence) => {
    setSelectedMarket(market);
    setDialogOpen(true);
  };

  const handleAlertClick = (alert: FinancialAlert) => {
    onAlertClick?.(alert);
  };

  if (loading) {
    return <LoadingState message="Loading market intelligence..." />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchMarketData}>
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
            Market Intelligence Dashboard
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Market Segment</InputLabel>
              <Select
                value={selectedSegment}
                label="Market Segment"
                onChange={(e) => setSelectedSegment(e.target.value)}
              >
                <MenuItem value="fintech">FinTech</MenuItem>
                <MenuItem value="cryptocurrency">Cryptocurrency</MenuItem>
                <MenuItem value="traditional_banking">Traditional Banking</MenuItem>
                <MenuItem value="payments">Payments</MenuItem>
                <MenuItem value="lending">Lending</MenuItem>
              </Select>
            </FormControl>
            <Tooltip title="Refresh Data">
              <IconButton onClick={fetchMarketData} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => console.log('Export market report')}
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
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AssessmentIcon color="primary" />
                    <Typography color="textSecondary" gutterBottom>
                      Market Sentiment
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" 
                    color={summary.marketSentiment === 'Positive' ? 'success.main' : 
                           summary.marketSentiment === 'Negative' ? 'error.main' : 'info.main'}>
                    {summary.marketSentiment}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {summary.bullishMarkets} bullish, {summary.bearishMarkets} bearish
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ShowChartIcon color="warning" />
                    <Typography color="textSecondary" gutterBottom>
                      Avg Volatility
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="warning.main">
                    {summary.avgVolatility.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    across {summary.totalMarkets} markets
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUpIcon color="success" />
                    <Typography color="textSecondary" gutterBottom>
                      Bullish Markets
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="success.main">
                    {summary.bullishMarkets}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    showing positive trends
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AnalyticsIcon color="info" />
                    <Typography color="textSecondary" gutterBottom>
                      Markets Analyzed
                    </Typography>
                  </Box>
                  <Typography variant="h4" component="div" color="info.main">
                    {summary.totalMarkets}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    real-time monitoring
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Main Content Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Market Analysis" />
            <Tab label="Stock Prices" />
            <Tab label="Economic Indicators" />
            <Tab label="Market Alerts" />
          </Tabs>
        </Paper>

        {/* Tab Content */}
        {tabValue === 0 && (
          <Grid container spacing={3}>
            {/* Market Intelligence Analysis */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Market Intelligence Analysis
                  </Typography>
                  <Grid container spacing={2}>
                    {marketIntelligence.map((market) => (
                      <Grid item xs={12} md={4} key={market.market_segment}>
                        <Card 
                          variant="outlined" 
                          sx={{ cursor: 'pointer', '&:hover': { elevation: 2 } }}
                          onClick={() => handleMarketClick(market)}
                        >
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                              {getTrendIcon(market.trend_direction)}
                              <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
                                {market.market_segment.replace('_', ' ')}
                              </Typography>
                            </Box>
                            
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="body2" color="textSecondary" gutterBottom>
                                Trend Direction
                              </Typography>
                              <Chip
                                label={market.trend_direction}
                                size="small"
                                sx={{
                                  backgroundColor: getTrendColor(market.trend_direction),
                                  color: 'white',
                                }}
                              />
                            </Box>

                            <Box sx={{ mb: 2 }}>
                              <Typography variant="body2" color="textSecondary" gutterBottom>
                                Volatility Level
                              </Typography>
                              <Typography variant="h6">
                                {(market.volatility_level * 100).toFixed(1)}%
                              </Typography>
                            </Box>

                            <Box sx={{ mb: 2 }}>
                              <Typography variant="body2" color="textSecondary" gutterBottom>
                                Key Drivers
                              </Typography>
                              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                {market.key_drivers.slice(0, 2).map((driver) => (
                                  <Chip key={driver} label={driver} size="small" variant="outlined" />
                                ))}
                                {market.key_drivers.length > 2 && (
                                  <Chip label={`+${market.key_drivers.length - 2} more`} size="small" />
                                )}
                              </Box>
                            </Box>

                            <Typography variant="body2" color="textSecondary">
                              Confidence: {(market.confidence_score * 100).toFixed(1)}%
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {tabValue === 1 && (
          <Grid container spacing={3}>
            {/* Stock Prices */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Key Stock Prices
                  </Typography>
                  <List>
                    {marketData.map((stock, index) => (
                      <React.Fragment key={stock.symbol}>
                        <ListItem>
                          <ListItemIcon>
                            {stock.change >= 0 ? 
                              <TrendingUpIcon color="success" /> : 
                              <TrendingDownIcon color="error" />
                            }
                          </ListItemIcon>
                          <ListItemText
                            primaryTypographyProps={{ component: 'div' }}
                            secondaryTypographyProps={{ component: 'div' }}
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Typography variant="h6">{stock.symbol}</Typography>
                                <Typography variant="h6">${stock.price.toFixed(2)}</Typography>
                                <Chip
                                  label={`${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)} (${stock.changePercent.toFixed(2)}%)`}
                                  size="small"
                                  color={stock.change >= 0 ? 'success' : 'error'}
                                />
                              </Box>
                            }
                            secondary={
                              <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                                <Typography variant="body2" color="textSecondary">
                                  Volume: {(stock.volume / 1000000).toFixed(1)}M
                                </Typography>
                                <Typography variant="body2" color="textSecondary">
                                  Market Cap: ${(stock.marketCap / 1000000000).toFixed(1)}B
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItem>
                        {index < marketData.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {tabValue === 2 && (
          <Grid container spacing={3}>
            {/* Economic Indicators */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Key Economic Indicators
                  </Typography>
                  <Grid container spacing={2}>
                    {economicIndicators.map((indicator) => (
                      <Grid item xs={12} sm={6} md={3} key={indicator.name}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              {getTrendIcon(indicator.trend)}
                              <Typography variant="subtitle2">
                                {indicator.name}
                              </Typography>
                            </Box>
                            <Typography variant="h5" component="div">
                              {indicator.value}{indicator.unit}
                            </Typography>
                            <Typography 
                              variant="body2" 
                              color={indicator.change >= 0 ? 'success.main' : 'error.main'}
                            >
                              {indicator.change >= 0 ? '+' : ''}{indicator.change}{indicator.unit}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              Updated: {new Date(indicator.lastUpdated).toLocaleDateString()}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {tabValue === 3 && (
          <Grid container spacing={3}>
            {/* Market Alerts */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Market Alerts
                  </Typography>
                  <List>
                    {alerts.map((alert, index) => (
                      <React.Fragment key={alert.alert_id}>
                        <ListItem
                          button
                          onClick={() => handleAlertClick(alert)}
                        >
                          <ListItemIcon>
                            <AnalyticsIcon color={alert.severity === 'high' ? 'error' : 'warning'} />
                          </ListItemIcon>
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
                        {index < alerts.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Market Detail Dialog */}
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Market Analysis Details
          </DialogTitle>
          <DialogContent>
            {selectedMarket && (
              <Box>
                <Typography variant="h6" gutterBottom sx={{ textTransform: 'capitalize' }}>
                  {selectedMarket.market_segment.replace('_', ' ')} Market
                </Typography>
                
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Trend Direction</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getTrendIcon(selectedMarket.trend_direction)}
                      <Typography variant="h6" sx={{ color: getTrendColor(selectedMarket.trend_direction) }}>
                        {selectedMarket.trend_direction}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Volatility Level</Typography>
                    <Typography variant="h6" color="warning.main">
                      {(selectedMarket.volatility_level * 100).toFixed(1)}%
                    </Typography>
                  </Grid>
                </Grid>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Key Drivers</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedMarket.key_drivers.map((driver) => (
                      <Chip key={driver} label={driver} size="small" color="primary" />
                    ))}
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Risk Factors</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedMarket.risk_factors.map((factor) => (
                      <Chip key={factor} label={factor} size="small" color="error" />
                    ))}
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Opportunities</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedMarket.opportunities.map((opportunity) => (
                      <Chip key={opportunity} label={opportunity} size="small" color="success" />
                    ))}
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>AI Insights</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {selectedMarket.ai_insights}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Chip 
                    label={`Confidence: ${(selectedMarket.confidence_score * 100).toFixed(1)}%`}
                    color="info"
                  />
                  <Chip 
                    label={`Data Sources: ${selectedMarket.data_sources.length}`}
                    variant="outlined"
                  />
                </Box>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>
              Close
            </Button>
            <Button variant="contained">
              Generate Report
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ErrorBoundary>
  );
};

export default MarketIntelligenceDashboard;