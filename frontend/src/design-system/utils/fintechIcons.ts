/**
 * RiskIntel360 Design System - Fintech Icon Utilities
 * Standardized icon mapping for financial industry use cases
 */

import {
  // Risk & Security Icons
  Shield as ShieldIcon,
  Security as SecurityIcon,
  Lock as LockIcon,
  VerifiedUser as VerifiedUserIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  
  // Compliance & Legal Icons
  Gavel as GavelIcon,
  Balance as BalanceIcon,
  Policy as PolicyIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  
  // Financial & Market Icons
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ShowChart as ShowChartIcon,
  Assessment as AssessmentIcon,
  AccountBalance as AccountBalanceIcon,
  AttachMoney as AttachMoneyIcon,
  MonetizationOn as MonetizationOnIcon,
  
  // Analytics & Data Icons
  Analytics as AnalyticsIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  
  // User & Identity Icons
  Person as PersonIcon,
  PersonSearch as PersonSearchIcon,
  Badge as BadgeIcon,
  Fingerprint as FingerprintIcon,
  
  // Transaction & Payment Icons
  Payment as PaymentIcon,
  CreditCard as CreditCardIcon,
  AccountBalanceWallet as WalletIcon,
  SwapHoriz as TransactionIcon,
  
  // Alert & Notification Icons
  Notifications as NotificationsIcon,
  NotificationImportant as AlertIcon,
  Report as ReportIcon,
  Flag as FlagIcon,
  
  // Status Icons
  CheckCircleOutline as SuccessIcon,
  ErrorOutline as ErrorOutlineIcon,
  InfoOutlined as InfoIcon,
  HelpOutline as HelpIcon,
  
  // Action Icons
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Settings as SettingsIcon,
  
  // Document Icons
  Description as DocumentIcon,
  Article as ArticleIcon,
  Receipt as ReceiptIcon,
  
  // Time & Date Icons
  Schedule as ScheduleIcon,
  DateRange as DateRangeIcon,
  History as HistoryIcon,
  
  // Communication Icons
  Email as EmailIcon,
  Phone as PhoneIcon,
  Message as MessageIcon,
  
  // Navigation Icons
  Dashboard as DashboardIcon,
  Home as HomeIcon,
  ArrowForward as ArrowForwardIcon,
  ArrowBack as ArrowBackIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

/**
 * Fintech-specific icon mappings
 * Provides semantic icon selection for financial use cases
 */
export const fintechIcons = {
  // Fraud Detection Icons
  fraud: {
    detection: ShieldIcon,
    alert: AlertIcon,
    high: ErrorIcon,
    medium: WarningIcon,
    low: InfoIcon,
    none: CheckCircleIcon,
    analysis: AnalyticsIcon,
  },
  
  // Compliance Icons
  compliance: {
    monitoring: BalanceIcon,
    compliant: CheckCircleIcon,
    nonCompliant: CancelIcon,
    pending: ScheduleIcon,
    underReview: AssignmentIcon,
    regulation: GavelIcon,
    policy: PolicyIcon,
    audit: AssessmentIcon,
  },
  
  // Risk Assessment Icons
  risk: {
    assessment: AssessmentIcon,
    low: CheckCircleIcon,
    medium: WarningIcon,
    high: ErrorIcon,
    critical: ReportIcon,
    analysis: ShowChartIcon,
    monitoring: SpeedIcon,
  },
  
  // Market Analysis Icons
  market: {
    analysis: ShowChartIcon,
    bullish: TrendingUpIcon,
    bearish: TrendingDownIcon,
    neutral: TimelineIcon,
    volatility: BarChartIcon,
    trends: TimelineIcon,
    intelligence: AnalyticsIcon,
  },
  
  // KYC Verification Icons
  kyc: {
    verification: VerifiedUserIcon,
    identity: FingerprintIcon,
    document: DocumentIcon,
    approved: CheckCircleIcon,
    rejected: CancelIcon,
    pending: ScheduleIcon,
    search: PersonSearchIcon,
    badge: BadgeIcon,
  },
  
  // Transaction Icons
  transaction: {
    payment: PaymentIcon,
    transfer: TransactionIcon,
    wallet: WalletIcon,
    card: CreditCardIcon,
    bank: AccountBalanceIcon,
    money: MonetizationOnIcon,
    receipt: ReceiptIcon,
  },
  
  // Financial Metrics Icons
  financial: {
    revenue: TrendingUpIcon,
    cost: TrendingDownIcon,
    profit: MonetizationOnIcon,
    loss: AttachMoneyIcon,
    balance: AccountBalanceIcon,
    chart: BarChartIcon,
    report: AssessmentIcon,
  },
  
  // Security Icons
  security: {
    secure: LockIcon,
    shield: ShieldIcon,
    verified: VerifiedUserIcon,
    encryption: SecurityIcon,
    alert: AlertIcon,
    warning: WarningIcon,
  },
  
  // Status Icons
  status: {
    success: SuccessIcon,
    error: ErrorOutlineIcon,
    warning: WarningIcon,
    info: InfoIcon,
    help: HelpIcon,
    pending: ScheduleIcon,
  },
  
  // Action Icons
  action: {
    refresh: RefreshIcon,
    download: DownloadIcon,
    upload: UploadIcon,
    search: SearchIcon,
    filter: FilterIcon,
    settings: SettingsIcon,
  },
  
  // Navigation Icons
  navigation: {
    dashboard: DashboardIcon,
    home: HomeIcon,
    forward: ArrowForwardIcon,
    back: ArrowBackIcon,
    expand: ExpandMoreIcon,
    collapse: ExpandLessIcon,
  },
  
  // Communication Icons
  communication: {
    email: EmailIcon,
    phone: PhoneIcon,
    message: MessageIcon,
    notification: NotificationsIcon,
  },
  
  // Time Icons
  time: {
    schedule: ScheduleIcon,
    date: DateRangeIcon,
    history: HistoryIcon,
  },
} as const;

/**
 * Get icon component for fraud detection level
 */
export const getFraudIcon = (level: 'none' | 'low' | 'medium' | 'high') => {
  return fintechIcons.fraud[level];
};

/**
 * Get icon component for compliance status
 */
export const getComplianceIcon = (status: 'compliant' | 'nonCompliant' | 'pending' | 'underReview') => {
  return fintechIcons.compliance[status];
};

/**
 * Get icon component for risk level
 */
export const getRiskIcon = (level: 'low' | 'medium' | 'high' | 'critical') => {
  return fintechIcons.risk[level];
};

/**
 * Get icon component for market trend
 */
export const getMarketIcon = (trend: 'bullish' | 'bearish' | 'neutral') => {
  return fintechIcons.market[trend];
};

/**
 * Get icon component for KYC status
 */
export const getKYCIcon = (status: 'approved' | 'rejected' | 'pending') => {
  return fintechIcons.kyc[status];
};

/**
 * Icon size presets for consistent sizing
 */
export const iconSizes = {
  xs: { fontSize: 16 },
  sm: { fontSize: 20 },
  md: { fontSize: 24 },
  lg: { fontSize: 32 },
  xl: { fontSize: 48 },
  xxl: { fontSize: 64 },
} as const;

/**
 * Get icon size style
 */
export const getIconSize = (size: keyof typeof iconSizes = 'md') => {
  return iconSizes[size];
};

export type FintechIconCategory = keyof typeof fintechIcons;
export type KYCStatus = 'approved' | 'rejected' | 'pending';

// Note: RiskLevel, ComplianceStatus, MarketTrend, and FraudLevel are exported from fintechVisualizations.ts
// to avoid duplicate exports
