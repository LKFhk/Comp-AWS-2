/**
 * Mobile-Optimized Views Component
 * Provides responsive, mobile-first dashboard components
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  BottomNavigation,
  BottomNavigationAction,
  Fab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Collapse,
  Chip,
  Avatar,
  Badge,
  SwipeableDrawer,
  useMediaQuery,
  useTheme,
  AppBar,
  Toolbar,
  Grid,
  Stack,
  Button,
  Dialog,
  DialogContent,
  Slide,
  Paper,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Person as PersonIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { TransitionProps } from '@mui/material/transitions';

// Mobile-specific interfaces
export interface MobileViewConfig {
  showBottomNavigation: boolean;
  showSpeedDial: boolean;
  compactMode: boolean;
  swipeGestures: boolean;
  pullToRefresh: boolean;
}

export interface MobileDashboardCard {
  id: string;
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  onClick?: () => void;
  priority: 'high' | 'medium' | 'low';
}

export interface MobileOptimizedViewsProps {
  cards: MobileDashboardCard[];
  activeView: string;
  onViewChange: (view: string) => void;
  onRefresh?: () => void;
  onSearch?: (query: string) => void;
  onFilter?: () => void;
  config?: MobileViewConfig;
  notifications?: number;
}

const Transition = React.forwardRef(function Transition(
  props: TransitionProps & {
    children: React.ReactElement;
  },
  ref: React.Ref<unknown>,
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

export const MobileOptimizedViews: React.FC<MobileOptimizedViewsProps> = ({
  cards,
  activeView,
  onViewChange,
  onRefresh,
  onSearch,
  onFilter,
  config = {
    showBottomNavigation: true,
    showSpeedDial: true,
    compactMode: false,
    swipeGestures: true,
    pullToRefresh: true,
  },
  notifications = 0,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isSmallMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [speedDialOpen, setSpeedDialOpen] = useState(false);
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [refreshing, setRefreshing] = useState(false);
  const [touchStart, setTouchStart] = useState<{ x: number; y: number } | null>(null);

  // Navigation items
  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
    { id: 'fraud', label: 'Fraud', icon: <SecurityIcon /> },
    { id: 'compliance', label: 'Compliance', icon: <AssessmentIcon /> },
    { id: 'market', label: 'Market', icon: <TrendingUpIcon /> },
    { id: 'kyc', label: 'KYC', icon: <PersonIcon /> },
  ];

  // Speed dial actions
  const speedDialActions = [
    { icon: <RefreshIcon />, name: 'Refresh', onClick: handleRefresh },
    { icon: <SearchIcon />, name: 'Search', onClick: () => setSearchDialogOpen(true) },
    { icon: <FilterIcon />, name: 'Filter', onClick: onFilter },
    { icon: <ShareIcon />, name: 'Share', onClick: () => console.log('Share') },
    { icon: <DownloadIcon />, name: 'Export', onClick: () => console.log('Export') },
  ];

  // Handle pull-to-refresh
  const handleTouchStart = (e: React.TouchEvent) => {
    if (config.pullToRefresh) {
      setTouchStart({
        x: e.touches[0].clientX,
        y: e.touches[0].clientY,
      });
    }
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!touchStart || !config.pullToRefresh) return;

    const touchEnd = {
      x: e.changedTouches[0].clientX,
      y: e.changedTouches[0].clientY,
    };

    const deltaY = touchEnd.y - touchStart.y;
    const deltaX = Math.abs(touchEnd.x - touchStart.x);

    // Pull down gesture (and not too much horizontal movement)
    if (deltaY > 100 && deltaX < 50 && window.scrollY === 0) {
      handleRefresh();
    }

    setTouchStart(null);
  };

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await onRefresh?.();
    } finally {
      setTimeout(() => setRefreshing(false), 1000); // Minimum refresh time for UX
    }
  }

  const handleCardExpand = (cardId: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cardId)) {
        newSet.delete(cardId);
      } else {
        newSet.add(cardId);
      }
      return newSet;
    });
  };

  const getTrendIcon = (trend?: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon sx={{ color: 'success.main', fontSize: 16 }} />;
      case 'down':
        return <TrendingUpIcon sx={{ color: 'error.main', fontSize: 16, transform: 'rotate(180deg)' }} />;
      default:
        return null;
    }
  };

  const sortedCards = [...cards].sort((a, b) => {
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  const renderMobileCard = (card: MobileDashboardCard) => {
    const isExpanded = expandedCards.has(card.id);
    
    return (
      <Card
        key={card.id}
        sx={{
          mb: 1,
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          '&:active': {
            transform: 'scale(0.98)',
          },
        }}
        onClick={() => card.onClick?.()}
      >
        <CardContent sx={{ p: config.compactMode ? 1.5 : 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1 }}>
              <Avatar
                sx={{
                  bgcolor: card.color,
                  width: config.compactMode ? 32 : 40,
                  height: config.compactMode ? 32 : 40,
                }}
              >
                {card.icon}
              </Avatar>
              
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant={config.compactMode ? 'body2' : 'body1'}
                  fontWeight="medium"
                  noWrap
                >
                  {card.title}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography
                    variant={config.compactMode ? 'h6' : 'h5'}
                    fontWeight="bold"
                    color="primary"
                  >
                    {card.value}
                  </Typography>
                  {card.trend && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {getTrendIcon(card.trend)}
                      {card.trendValue && (
                        <Typography
                          variant="caption"
                          color={card.trend === 'up' ? 'success.main' : card.trend === 'down' ? 'error.main' : 'textSecondary'}
                        >
                          {card.trendValue}
                        </Typography>
                      )}
                    </Box>
                  )}
                </Box>
                {card.subtitle && (
                  <Typography variant="caption" color="textSecondary" noWrap>
                    {card.subtitle}
                  </Typography>
                )}
              </Box>
            </Box>

            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleCardExpand(card.id);
              }}
            >
              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={isExpanded}>
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="body2" color="textSecondary">
                Additional details and actions for {card.title} would appear here.
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Button size="small" variant="outlined">
                  View Details
                </Button>
                <Button size="small" variant="text">
                  Configure
                </Button>
              </Stack>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  };

  const renderDesktopView = () => (
    <Grid container spacing={2}>
      {sortedCards.map(card => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={card.id}>
          {renderMobileCard(card)}
        </Grid>
      ))}
    </Grid>
  );

  const renderMobileView = () => (
    <Box
      sx={{ pb: config.showBottomNavigation ? 8 : 2 }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull-to-refresh indicator */}
      {refreshing && (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Typography variant="body2" color="textSecondary">
            Refreshing...
          </Typography>
        </Box>
      )}

      {/* Priority sections for mobile */}
      {['high', 'medium', 'low'].map(priority => {
        const priorityCards = sortedCards.filter(card => card.priority === priority);
        if (priorityCards.length === 0) return null;

        return (
          <Box key={priority} sx={{ mb: 2 }}>
            {priority === 'high' && (
              <Typography variant="subtitle2" color="textSecondary" sx={{ mb: 1, px: 1 }}>
                Critical Metrics
              </Typography>
            )}
            {priorityCards.map(renderMobileCard)}
          </Box>
        );
      })}
    </Box>
  );

  return (
    <Box sx={{ position: 'relative', minHeight: '100vh' }}>
      {/* Mobile App Bar */}
      {isMobile && (
        <AppBar position="sticky" elevation={1}>
          <Toolbar>
            <IconButton
              edge="start"
              color="inherit"
              onClick={() => setDrawerOpen(true)}
            >
              <MenuIcon />
            </IconButton>
            
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {navigationItems.find(item => item.id === activeView)?.label || 'Dashboard'}
            </Typography>

            <IconButton color="inherit" onClick={() => setSearchDialogOpen(true)}>
              <SearchIcon />
            </IconButton>
            
            <IconButton color="inherit">
              <Badge badgeContent={notifications} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Toolbar>
        </AppBar>
      )}

      {/* Main Content */}
      <Box sx={{ p: isMobile ? 1 : 2 }}>
        {isMobile ? renderMobileView() : renderDesktopView()}
      </Box>

      {/* Navigation Drawer */}
      <SwipeableDrawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onOpen={() => setDrawerOpen(true)}
        disableSwipeToOpen={!config.swipeGestures}
      >
        <Box sx={{ width: 280 }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h6">RiskIntel360</Typography>
            <Typography variant="body2" color="textSecondary">
              Financial Intelligence Platform
            </Typography>
          </Box>
          
          <List>
            {navigationItems.map(item => (
              <ListItem
                key={item.id}
                button
                selected={activeView === item.id}
                onClick={() => {
                  onViewChange(item.id);
                  setDrawerOpen(false);
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
          </List>

          <Box sx={{ mt: 'auto', p: 2, borderTop: 1, borderColor: 'divider' }}>
            <ListItem button>
              <ListItemIcon><SettingsIcon /></ListItemIcon>
              <ListItemText primary="Settings" />
            </ListItem>
          </Box>
        </Box>
      </SwipeableDrawer>

      {/* Bottom Navigation */}
      {isMobile && config.showBottomNavigation && (
        <Paper
          sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1000 }}
          elevation={3}
        >
          <BottomNavigation
            value={activeView}
            onChange={(_, newValue) => onViewChange(newValue)}
            showLabels={!isSmallMobile}
          >
            {navigationItems.slice(0, isSmallMobile ? 4 : 5).map(item => (
              <BottomNavigationAction
                key={item.id}
                label={item.label}
                value={item.id}
                icon={item.icon}
              />
            ))}
          </BottomNavigation>
        </Paper>
      )}

      {/* Speed Dial */}
      {config.showSpeedDial && (
        <SpeedDial
          ariaLabel="Quick Actions"
          sx={{
            position: 'fixed',
            bottom: config.showBottomNavigation ? 80 : 16,
            right: 16,
          }}
          icon={<SpeedDialIcon />}
          open={speedDialOpen}
          onClose={() => setSpeedDialOpen(false)}
          onOpen={() => setSpeedDialOpen(true)}
        >
          {speedDialActions.map(action => (
            <SpeedDialAction
              key={action.name}
              icon={action.icon}
              tooltipTitle={action.name}
              onClick={() => {
                action.onClick?.();
                setSpeedDialOpen(false);
              }}
            />
          ))}
        </SpeedDial>
      )}

      {/* Search Dialog */}
      <Dialog
        fullScreen={isMobile}
        open={searchDialogOpen}
        onClose={() => setSearchDialogOpen(false)}
        TransitionComponent={isMobile ? Transition : undefined}
        maxWidth="sm"
        fullWidth
      >
        {isMobile && (
          <AppBar sx={{ position: 'relative' }}>
            <Toolbar>
              <IconButton
                edge="start"
                color="inherit"
                onClick={() => setSearchDialogOpen(false)}
              >
                <CloseIcon />
              </IconButton>
              <Typography sx={{ ml: 2, flex: 1 }} variant="h6">
                Search
              </Typography>
            </Toolbar>
          </AppBar>
        )}
        
        <DialogContent>
          <MobileSearchInterface
            onSearch={(query) => {
              onSearch?.(query);
              setSearchDialogOpen(false);
            }}
            onClose={() => setSearchDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

// Mobile Search Interface Component
const MobileSearchInterface: React.FC<{
  onSearch: (query: string) => void;
  onClose: () => void;
}> = ({ onSearch, onClose }) => {
  const [query, setQuery] = useState('');
  const [recentSearches] = useState([
    'Fraud alerts',
    'Compliance status',
    'Market trends',
    'Risk assessment',
  ]);

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <Box sx={{ pt: 2 }}>
      <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
        <Box sx={{ flex: 1 }}>
          <input
            type="text"
            placeholder="Search dashboards, alerts, reports..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '16px',
              outline: 'none',
            }}
            autoFocus
          />
        </Box>
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={!query.trim()}
        >
          Search
        </Button>
      </Box>

      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
        Recent Searches
      </Typography>
      
      <Stack spacing={1}>
        {recentSearches.map((search, index) => (
          <Chip
            key={index}
            label={search}
            variant="outlined"
            onClick={() => {
              setQuery(search);
              onSearch(search);
            }}
            sx={{ justifyContent: 'flex-start' }}
          />
        ))}
      </Stack>

      <Typography variant="subtitle2" color="textSecondary" sx={{ mt: 3, mb: 1 }}>
        Quick Actions
      </Typography>
      
      <List dense>
        <ListItem button onClick={() => onSearch('active alerts')}>
          <ListItemIcon><NotificationsIcon /></ListItemIcon>
          <ListItemText primary="View Active Alerts" />
        </ListItem>
        <ListItem button onClick={() => onSearch('fraud detection')}>
          <ListItemIcon><SecurityIcon /></ListItemIcon>
          <ListItemText primary="Fraud Detection Status" />
        </ListItem>
        <ListItem button onClick={() => onSearch('compliance report')}>
          <ListItemIcon><AssessmentIcon /></ListItemIcon>
          <ListItemText primary="Latest Compliance Report" />
        </ListItem>
        <ListItem button onClick={() => onSearch('market analysis')}>
          <ListItemIcon><TrendingUpIcon /></ListItemIcon>
          <ListItemText primary="Market Analysis" />
        </ListItem>
      </List>
    </Box>
  );
};

export default MobileOptimizedViews;