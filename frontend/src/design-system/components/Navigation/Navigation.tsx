/**
 * RiskIntel360 Design System - Navigation Components
 * Modern navigation components for fintech applications
 */

import React, { useState, forwardRef } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Collapse,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Box,
  Chip,
  Tooltip,
  useMediaQuery,
  useTheme as useMuiTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  ExpandLess,
  ExpandMore,
  Notifications as NotificationsIcon,
  AccountCircle as AccountCircleIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  AccountBalance as AccountBalanceIcon,
  Gavel as GavelIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  Computer as ComputerIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { useTheme, useThemeMode } from '../../theme/ThemeProvider';

// Navigation item interface
export interface NavigationItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  path?: string;
  badge?: number | string;
  children?: NavigationItem[];
  disabled?: boolean;
  divider?: boolean;
}

// Header props
export interface HeaderProps {
  title?: string;
  logo?: React.ReactNode;
  onMenuClick?: () => void;
  showMenuButton?: boolean;
  actions?: React.ReactNode;
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  notifications?: number;
  onNotificationClick?: () => void;
  onUserMenuClick?: (action: string) => void;
}

// Sidebar props
export interface SidebarProps {
  open: boolean;
  onClose: () => void;
  items: NavigationItem[];
  onItemClick: (item: NavigationItem) => void;
  activeItem?: string;
  variant?: 'permanent' | 'temporary' | 'persistent';
  width?: number;
  collapsible?: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

// Styled components
const StyledAppBar = styled(AppBar)(({ theme }) => ({
  zIndex: theme.zIndex.drawer + 1,
  backgroundColor: theme.palette.background.paper,
  color: theme.palette.text.primary,
  borderBottom: `1px solid ${theme.palette.divider}`,
  boxShadow: theme.shadows[1],
}));

const StyledDrawer = styled(Drawer)<{ width: number; collapsed?: boolean }>(
  ({ theme, width, collapsed }) => ({
    width: collapsed ? 64 : width,
    flexShrink: 0,
    '& .MuiDrawer-paper': {
      width: collapsed ? 64 : width,
      boxSizing: 'border-box',
      borderRight: `1px solid ${theme.palette.divider}`,
      backgroundColor: theme.palette.background.paper,
      transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
      }),
    },
  })
);

const StyledListItem = styled(ListItemButton)<{ active?: boolean }>(
  ({ theme, active }) => ({
    borderRadius: theme.spacing(1),
    margin: theme.spacing(0.5, 1),
    '&:hover': {
      backgroundColor: theme.palette.action.hover,
    },
    ...(active && {
      backgroundColor: theme.palette.primary.main,
      color: theme.palette.primary.contrastText,
      '&:hover': {
        backgroundColor: theme.palette.primary.dark,
      },
      '& .MuiListItemIcon-root': {
        color: theme.palette.primary.contrastText,
      },
    }),
  })
);

// Header component
export const Header = forwardRef<HTMLDivElement, HeaderProps>(
  (
    {
      title = 'RiskIntel360',
      logo,
      onMenuClick,
      showMenuButton = true,
      actions,
      user,
      notifications = 0,
      onNotificationClick,
      onUserMenuClick,
    },
    ref
  ) => {
    const muiTheme = useMuiTheme();
    const { mode, toggleTheme, setThemeMode } = useThemeMode();
    const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
    const [themeMenuAnchor, setThemeMenuAnchor] = useState<null | HTMLElement>(null);

    const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
      setUserMenuAnchor(event.currentTarget);
    };

    const handleUserMenuClose = () => {
      setUserMenuAnchor(null);
    };

    const handleThemeMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
      setThemeMenuAnchor(event.currentTarget);
    };

    const handleThemeMenuClose = () => {
      setThemeMenuAnchor(null);
    };

    const handleUserMenuClick = (action: string) => {
      handleUserMenuClose();
      onUserMenuClick?.(action);
    };

    const handleThemeChange = (newMode: 'light' | 'dark' | 'system') => {
      setThemeMode(newMode);
      handleThemeMenuClose();
    };

    const getThemeIcon = () => {
      switch (mode) {
        case 'light':
          return <LightModeIcon />;
        case 'dark':
          return <DarkModeIcon />;
        case 'system':
        default:
          return <ComputerIcon />;
      }
    };

    return (
      <StyledAppBar ref={ref} position="fixed" elevation={0}>
        <Toolbar>
          {/* Menu button */}
          {showMenuButton && (
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={onMenuClick}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {/* Logo and title */}
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            {logo && <Box sx={{ mr: 2 }}>{logo}</Box>}
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
              {title}
            </Typography>
          </Box>

          {/* Actions */}
          {actions && <Box sx={{ mr: 2 }}>{actions}</Box>}

          {/* Theme toggle */}
          <Tooltip title="Change theme">
            <IconButton color="inherit" onClick={handleThemeMenuOpen}>
              {getThemeIcon()}
            </IconButton>
          </Tooltip>

          {/* Notifications */}
          {onNotificationClick && (
            <Tooltip title="Notifications">
              <IconButton color="inherit" onClick={onNotificationClick}>
                <Badge badgeContent={notifications} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>
          )}

          {/* User menu */}
          {user && (
            <Tooltip title="Account">
              <IconButton
                edge="end"
                color="inherit"
                onClick={handleUserMenuOpen}
                sx={{ ml: 1 }}
              >
                {user.avatar ? (
                  <Avatar src={user.avatar} sx={{ width: 32, height: 32 }} />
                ) : (
                  <AccountCircleIcon />
                )}
              </IconButton>
            </Tooltip>
          )}

          {/* Theme menu */}
          <Menu
            anchorEl={themeMenuAnchor}
            open={Boolean(themeMenuAnchor)}
            onClose={handleThemeMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={() => handleThemeChange('light')}>
              <ListItemIcon>
                <LightModeIcon fontSize="small" />
              </ListItemIcon>
              Light
            </MenuItem>
            <MenuItem onClick={() => handleThemeChange('dark')}>
              <ListItemIcon>
                <DarkModeIcon fontSize="small" />
              </ListItemIcon>
              Dark
            </MenuItem>
            <MenuItem onClick={() => handleThemeChange('system')}>
              <ListItemIcon>
                <ComputerIcon fontSize="small" />
              </ListItemIcon>
              System
            </MenuItem>
          </Menu>

          {/* User menu */}
          {user && (
            <Menu
              anchorEl={userMenuAnchor}
              open={Boolean(userMenuAnchor)}
              onClose={handleUserMenuClose}
              transformOrigin={{ horizontal: 'right', vertical: 'top' }}
              anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            >
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="subtitle2">{user.name}</Typography>
                <Typography variant="body2" color="textSecondary">
                  {user.email}
                </Typography>
              </Box>
              <Divider />
              <MenuItem onClick={() => handleUserMenuClick('profile')}>
                <ListItemIcon>
                  <AccountCircleIcon fontSize="small" />
                </ListItemIcon>
                Profile
              </MenuItem>
              <MenuItem onClick={() => handleUserMenuClick('settings')}>
                <ListItemIcon>
                  <SettingsIcon fontSize="small" />
                </ListItemIcon>
                Settings
              </MenuItem>
              <Divider />
              <MenuItem onClick={() => handleUserMenuClick('logout')}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" />
                </ListItemIcon>
                Logout
              </MenuItem>
            </Menu>
          )}
        </Toolbar>
      </StyledAppBar>
    );
  }
);

Header.displayName = 'Header';

// Sidebar navigation item component
const NavigationItemComponent: React.FC<{
  item: NavigationItem;
  active: boolean;
  collapsed: boolean;
  onClick: (item: NavigationItem) => void;
  level?: number;
}> = ({ item, active, collapsed, onClick, level = 0 }) => {
  const [open, setOpen] = useState(false);
  const hasChildren = item.children && item.children.length > 0;

  const handleClick = () => {
    if (hasChildren && !collapsed) {
      setOpen(!open);
    } else {
      onClick(item);
    }
  };

  const handleChildClick = (childItem: NavigationItem) => {
    onClick(childItem);
  };

  return (
    <>
      <StyledListItem
        active={active}
        onClick={handleClick}
        disabled={item.disabled}
        sx={{ pl: collapsed ? 1 : 2 + level * 2 }}
      >
        {item.icon && (
          <ListItemIcon sx={{ minWidth: collapsed ? 0 : 40 }}>
            {item.icon}
          </ListItemIcon>
        )}
        {!collapsed && (
          <>
            <ListItemText
              primary={item.label}
              primaryTypographyProps={{
                variant: 'body2',
                fontWeight: active ? 600 : 400,
              }}
            />
            {item.badge && (
              <Chip
                label={item.badge}
                size="small"
                color="primary"
                sx={{ ml: 1, height: 20, fontSize: '0.75rem' }}
              />
            )}
            {hasChildren && (open ? <ExpandLess /> : <ExpandMore />)}
          </>
        )}
      </StyledListItem>

      {hasChildren && !collapsed && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {item.children!.map((child) => (
              <NavigationItemComponent
                key={child.id}
                item={child}
                active={child.id === item.id}
                collapsed={false}
                onClick={handleChildClick}
                level={level + 1}
              />
            ))}
          </List>
        </Collapse>
      )}

      {item.divider && !collapsed && <Divider sx={{ my: 1 }} />}
    </>
  );
};

// Sidebar component
export const Sidebar = forwardRef<HTMLDivElement, SidebarProps>(
  (
    {
      open,
      onClose,
      items,
      onItemClick,
      activeItem,
      variant = 'temporary',
      width = 280,
      collapsible = false,
      collapsed = false,
      onToggleCollapse,
    },
    ref
  ) => {
    const muiTheme = useMuiTheme();
    const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));

    const drawerVariant = isMobile ? 'temporary' : variant;
    const drawerOpen = isMobile ? open : variant === 'permanent' ? true : open;

    const handleItemClick = (item: NavigationItem) => {
      onItemClick(item);
      if (isMobile) {
        onClose();
      }
    };

    return (
      <StyledDrawer
        ref={ref}
        variant={drawerVariant}
        open={drawerOpen}
        onClose={onClose}
        width={width}
        collapsed={collapsed && !isMobile}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
      >
        {/* Collapse toggle */}
        {collapsible && !isMobile && (
          <Box sx={{ p: 1, textAlign: 'right' }}>
            <IconButton onClick={onToggleCollapse} size="small">
              {collapsed ? <MenuIcon /> : <CloseIcon />}
            </IconButton>
          </Box>
        )}

        {/* Navigation items */}
        <List sx={{ pt: collapsible && !isMobile ? 0 : 2 }}>
          {items.map((item) => (
            <NavigationItemComponent
              key={item.id}
              item={item}
              active={activeItem === item.id}
              collapsed={collapsed && !isMobile}
              onClick={handleItemClick}
            />
          ))}
        </List>
      </StyledDrawer>
    );
  }
);

Sidebar.displayName = 'Sidebar';

// Default navigation items for RiskIntel360
export const defaultNavigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    id: 'risk-analysis',
    label: 'Risk Analysis',
    icon: <AssessmentIcon />,
    path: '/risk-analysis',
    children: [
      {
        id: 'risk-overview',
        label: 'Overview',
        path: '/risk-analysis/overview',
      },
      {
        id: 'risk-assessment',
        label: 'Risk Assessment',
        path: '/risk-analysis/assessment',
      },
      {
        id: 'risk-monitoring',
        label: 'Monitoring',
        path: '/risk-analysis/monitoring',
      },
    ],
  },
  {
    id: 'compliance',
    label: 'Compliance',
    icon: <GavelIcon />,
    path: '/compliance',
    badge: 3,
    children: [
      {
        id: 'compliance-dashboard',
        label: 'Dashboard',
        path: '/compliance/dashboard',
      },
      {
        id: 'regulatory-updates',
        label: 'Regulatory Updates',
        path: '/compliance/updates',
        badge: 2,
      },
      {
        id: 'compliance-reports',
        label: 'Reports',
        path: '/compliance/reports',
      },
    ],
  },
  {
    id: 'fraud-detection',
    label: 'Fraud Detection',
    icon: <SecurityIcon />,
    path: '/fraud-detection',
    children: [
      {
        id: 'fraud-dashboard',
        label: 'Dashboard',
        path: '/fraud-detection/dashboard',
      },
      {
        id: 'fraud-alerts',
        label: 'Alerts',
        path: '/fraud-detection/alerts',
        badge: 5,
      },
      {
        id: 'fraud-patterns',
        label: 'Pattern Analysis',
        path: '/fraud-detection/patterns',
      },
    ],
  },
  {
    id: 'market-intelligence',
    label: 'Market Intelligence',
    icon: <TrendingUpIcon />,
    path: '/market-intelligence',
    children: [
      {
        id: 'market-overview',
        label: 'Overview',
        path: '/market-intelligence/overview',
      },
      {
        id: 'market-trends',
        label: 'Trends',
        path: '/market-intelligence/trends',
      },
      {
        id: 'market-analysis',
        label: 'Analysis',
        path: '/market-intelligence/analysis',
      },
    ],
  },
  {
    id: 'kyc-verification',
    label: 'KYC Verification',
    icon: <AccountBalanceIcon />,
    path: '/kyc-verification',
    children: [
      {
        id: 'kyc-dashboard',
        label: 'Dashboard',
        path: '/kyc-verification/dashboard',
      },
      {
        id: 'kyc-pending',
        label: 'Pending Reviews',
        path: '/kyc-verification/pending',
        badge: 12,
      },
      {
        id: 'kyc-completed',
        label: 'Completed',
        path: '/kyc-verification/completed',
      },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <SettingsIcon />,
    path: '/settings',
    divider: true,
  },
];

export default { Header, Sidebar, defaultNavigationItems };