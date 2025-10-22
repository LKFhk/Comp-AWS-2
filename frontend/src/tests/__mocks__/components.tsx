import React from 'react';

// Mock components for testing
export const MockDashboard = () => (
  <div data-testid="dashboard">
    <h1>Dashboard</h1>
    <div>Welcome back, Test User</div>
    <div>Risk Analyses Completed</div>
    <div>Recent Risk Analyses</div>
    <button>New Risk Analysis</button>
  </div>
);

export const MockValidationWizard = () => (
  <div data-testid="validation-wizard">
    <h1>New Financial Risk Analysis</h1>
    <label htmlFor="financial-institution">Financial Institution Profile</label>
    <input id="financial-institution" />
    <button>Next</button>
  </div>
);

export const MockValidationProgress = () => (
  <div data-testid="validation-progress">
    <h1>Risk Analysis Progress</h1>
    <div>AI Agent Progress</div>
    <div>Progress: 65%</div>
  </div>
);

export const MockValidationResults = () => (
  <div data-testid="validation-results">
    <h1>Risk Intelligence Report</h1>
    <div>Overall Risk Score</div>
    <div>79</div>
    <button>Download Report</button>
  </div>
);

export const MockSettings = () => (
  <div data-testid="settings">
    <h1>Settings</h1>
    <div>Test User</div>
    <div>test@riskintel360.com</div>
    <button>Save Settings</button>
  </div>
);