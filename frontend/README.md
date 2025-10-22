# RiskIntel360 Platform Frontend

A modern React.js web application for the RiskIntel360 multi-agent financial intelligence platform.

## Features

- **Professional Business Interface**: Clean, responsive design built with Material-UI
- **Real-time Progress Monitoring**: WebSocket-powered live updates during validation
- **Interactive Data Visualizations**: Charts and graphs using Chart.js and Plotly
- **Step-by-step Validation Wizard**: Guided form for creating validation requests
- **Comprehensive Results Dashboard**: Detailed analysis results with multiple views
- **User Preference Management**: Customizable settings and notifications
- **Accessibility Compliant**: WCAG 2.1 AA compliance for inclusive access

## Technology Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for professional business styling
- **Chart.js & Plotly.js** for data visualizations
- **React Router** for navigation
- **Axios** for API communication
- **Socket.io** for real-time WebSocket connections
- **Jest & React Testing Library** for comprehensive testing

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- RiskIntel360 backend API running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment configuration:
```bash
cp .env.example .env.local
```

3. Configure environment variables:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### Development

Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000` with hot-reload enabled.

### Testing

Run the test suite:
```bash
# Run tests once
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm test -- --coverage
```

### Building for Production

Create an optimized production build:
```bash
npm run build
```

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── Common/          # Generic components (LoadingSpinner, ProgressBar)
│   ├── Charts/          # Data visualization components
│   └── Layout/          # Layout components (Navigation, Header)
├── contexts/            # React contexts for state management
│   ├── AuthContext.tsx  # Authentication state
│   └── NotificationContext.tsx  # Notification system
├── pages/               # Page components
│   ├── Dashboard/       # Main dashboard
│   ├── Login/           # Authentication
│   ├── ValidationWizard/ # Step-by-step validation creation
│   ├── ValidationProgress/ # Real-time progress monitoring
│   ├── ValidationResults/ # Results visualization
│   └── Settings/        # User preferences
├── services/            # API and external service integrations
│   ├── api.ts          # REST API client
│   └── websocket.ts    # WebSocket service
├── tests/              # Integration and E2E tests
└── App.tsx             # Main application component
```

## Key Components

### Dashboard
- **Executive Overview**: Key metrics and recent validations
- **Quick Actions**: Fast access to common operations
- **Real-time Stats**: Live updates of validation progress

### Validation Wizard
- **Multi-step Form**: Guided validation request creation
- **Smart Defaults**: Pre-filled values based on user preferences
- **Real-time Validation**: Form validation with helpful error messages
- **Progress Indicators**: Clear visual progress through steps

### Progress Monitoring
- **Real-time Updates**: WebSocket-powered live progress tracking
- **Agent Status**: Individual AI agent progress and status
- **Time Estimates**: Dynamic completion time calculations
- **Interactive Timeline**: Visual representation of validation workflow

### Results Visualization
- **Interactive Charts**: Market analysis, competitive positioning, financial projections
- **Tabbed Interface**: Organized analysis results by category
- **Export Options**: PDF reports and data export functionality
- **Executive Summary**: High-level insights and recommendations

### Settings & Preferences
- **User Profile**: Account information and preferences
- **Notification Settings**: Customizable alert preferences
- **Default Configurations**: Pre-set validation parameters
- **Theme & Language**: Appearance and localization options

## API Integration

The frontend integrates with the RiskIntel360 backend API:

- **Authentication**: JWT-based authentication with automatic token refresh
- **Validation Management**: CRUD operations for validation requests
- **Real-time Updates**: WebSocket connections for live progress
- **Data Visualization**: Endpoints for chart data and visualizations
- **File Operations**: Report generation and export functionality

## WebSocket Integration

Real-time features powered by WebSocket connections:

- **Progress Updates**: Live validation progress and agent status
- **Notifications**: System alerts and completion notifications
- **Error Handling**: Automatic reconnection and error recovery
- **Connection Management**: Efficient connection pooling and cleanup

## Testing Strategy

Comprehensive testing approach:

- **Unit Tests**: Individual component testing with Jest
- **Integration Tests**: Component interaction and API integration
- **Accessibility Tests**: WCAG compliance and keyboard navigation
- **Visual Regression**: UI consistency and responsive design
- **Performance Tests**: Load times and rendering performance

## Accessibility Features

WCAG 2.1 AA compliant design:

- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Proper ARIA labels and roles
- **High Contrast**: Support for high contrast mode
- **Reduced Motion**: Respects user motion preferences
- **Focus Management**: Clear focus indicators and logical tab order

## Performance Optimizations

- **Code Splitting**: Lazy loading of route components
- **Image Optimization**: Responsive images and lazy loading
- **Bundle Analysis**: Webpack bundle optimization
- **Caching Strategy**: Efficient API response caching
- **Progressive Enhancement**: Core functionality without JavaScript

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow the existing code style and conventions
2. Write tests for new features and bug fixes
3. Ensure accessibility compliance for UI changes
4. Update documentation for API changes
5. Test across supported browsers and devices

## Environment Variables

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_DEBUG=false

# Build Configuration
GENERATE_SOURCEMAP=true
```

## Deployment

The application can be deployed to any static hosting service:

- **Netlify**: Automatic deployments from Git
- **Vercel**: Optimized React deployments
- **AWS S3 + CloudFront**: Scalable static hosting
- **Docker**: Containerized deployment with nginx

## License

This project is part of the RiskIntel360 Platform for the AWS AI Agent Competition.