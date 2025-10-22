/**
 * RiskIntel360 Design System - Component Index
 * Central export for all design system components
 */

// Core components
export { Button, type ButtonProps } from './Button/Button';
export { Card, type CardProps } from './Card/Card';
export { LoadingState, type LoadingStateProps } from './LoadingState/LoadingState';
export { ErrorBoundary } from './ErrorBoundary/ErrorBoundary';
export {
  EmptyState,
  NoDataEmptyState,
  SearchEmptyState,
  FinancialEmptyState,
  DashboardEmptyState,
  type EmptyStateProps,
} from './EmptyState/EmptyState';

// Layout components
export {
  GridContainer,
  GridItem,
  FlexGrid,
  Container,
  Stack,
  type GridContainerProps,
  type GridItemProps,
  type FlexGridProps,
  type ContainerProps,
  type StackProps,
} from './Grid/Grid';

// Navigation components
export {
  Header,
  Sidebar,
  defaultNavigationItems,
  type HeaderProps,
  type SidebarProps,
  type NavigationItem,
} from './Navigation/Navigation';

// Fintech-specific components
export { RiskMatrix } from './RiskMatrix';
export { ComplianceGauge } from './ComplianceGauge';
export { FraudHeatmap, type FraudDataPoint } from './FraudHeatmap';

// Re-export commonly used MUI components with consistent styling
export {
  Typography,
  Box,
  Paper,
  Divider,
  Chip,
  Avatar,
  Badge,
  Tooltip,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  FormLabel,
  FormHelperText,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Menu,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tabs,
  Tab,
  // TabPanel, // Not available in MUI core
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Breadcrumbs,
  Link,
  CircularProgress,
  LinearProgress,
  Skeleton,
} from '@mui/material';

// Icons
export {
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  AccountBalance as AccountBalanceIcon,
  Gavel as GavelIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Filter as FilterIcon,
  Sort as SortIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreVertIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  Computer as ComputerIcon,
} from '@mui/icons-material';