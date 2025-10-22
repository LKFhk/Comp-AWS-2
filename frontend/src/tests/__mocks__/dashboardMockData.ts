/**
 * Comprehensive mock data for all dashboard tests
 */

import '@testing-library/jest-dom';
import type { FinTechDashboardData } from '../../types/fintech';

// Fixed timestamps for consistent snapshot testing
const FIXED_DATE = '2024-10-20T12:00:00.000Z';
const FIXED_DATE_PLUS_5MIN = '2024-10-20T12:05:00.000Z';
const FIXED_DATE_MINUS_30MIN = '2024-10-20T11:30:00.000Z';

export const mockDashboardData: FinTechDashboardData = {
    summary: {
        active_analyses: 12,
        completed_today: 45,
        fraud_alerts: 3,
        compliance_issues: 1,
    },
    recent_analyses: [
        {
            analysis_id: 'RISK-001',
            status: 'completed',
            message: 'Comprehensive risk analysis completed successfully',
            estimated_completion: FIXED_DATE,
        },
        {
            analysis_id: 'FRAUD-002',
            status: 'in_progress',
            message: 'Fraud detection analysis in progress',
            estimated_completion: FIXED_DATE_PLUS_5MIN,
        },
    ],
    active_alerts: [
        {
            alert_id: 'ALERT-001',
            alert_type: 'fraud_detection',
            severity: 'high',
            title: 'High-Risk Transaction Detected',
            description: 'Transaction TXN-002 flagged with 89% fraud probability',
            created_at: FIXED_DATE,
        },
        {
            alert_id: 'ALERT-002',
            alert_type: 'compliance',
            severity: 'medium',
            title: 'Compliance Review Required',
            description: 'CFPB regulation requires manual review',
            created_at: FIXED_DATE_MINUS_30MIN,
        },
    ],
    performance_metrics: {
        average_response_time: 3.2,
        success_rate: 98.5,
        fraud_detection_accuracy: 95.2,
        compliance_score: 87.3,
    },
    business_value: {
        monthly_savings: 850000,
        fraud_prevented: 2100000,
        compliance_cost_reduction: 450000,
        roi_percentage: 340,
    },
};

export const mockComplianceData: {
    status: string;
    score: number;
    lastCheck: string;
    regulations: Array<{ name: string; status: string; lastUpdate: string }>;
} = {
    status: 'compliant',
    score: 95,
    lastCheck: FIXED_DATE,
    regulations: [
        { name: 'SEC Filing', status: 'compliant', lastUpdate: FIXED_DATE },
        { name: 'FINRA Rules', status: 'compliant', lastUpdate: FIXED_DATE },
    ],
};

export const mockFraudData: {
    detectedCases: number;
    preventedLosses: number;
    falsePositiveRate: number;
    accuracy: number;
    recentCases: Array<{
        id: string;
        amount: number;
        confidence: number;
        status: string;
        timestamp: string;
    }>;
} = {
    detectedCases: 15,
    preventedLosses: 5000000,
    falsePositiveRate: 0.05,
    accuracy: 0.95,
    recentCases: [
        {
            id: '1',
            amount: 50000,
            confidence: 0.98,
            status: 'blocked',
            timestamp: FIXED_DATE,
        },
    ],
};

export const mockMarketData: {
    trends: Array<{ date: string; value: number }>;
    indicators: {
        volatility: number;
        momentum: number;
        sentiment: number;
    };
} = {
    trends: [
        { date: '2024-01', value: 100 },
        { date: '2024-02', value: 105 },
        { date: '2024-03', value: 110 },
    ],
    indicators: {
        volatility: 0.15,
        momentum: 0.08,
        sentiment: 0.65,
    },
};

export const mockExecutionData: {
    id: string;
    status: string;
    startTime: string;
    endTime: string;
    results: {
        regulatory_compliance: { status: string; confidence: number };
        fraud_detection: { status: string; confidence: number };
        risk_assessment: { status: string; confidence: number };
    };
    metrics: {
        totalValue: number;
        processingTime: number;
        agentsUsed: number;
    };
} = {
    id: 'exec-123',
    status: 'completed',
    startTime: FIXED_DATE,
    endTime: FIXED_DATE,
    results: {
        regulatory_compliance: { status: 'completed', confidence: 0.92 },
        fraud_detection: { status: 'completed', confidence: 0.95 },
        risk_assessment: { status: 'completed', confidence: 0.88 },
    },
    metrics: {
        totalValue: 25000000,
        processingTime: 120,
        agentsUsed: 5,
    },
};

// Mock demo scenarios
export const mockDemoScenarios = [
    {
        id: 'saas_startup',
        name: 'SaaS Startup',
        description: 'AI-powered customer service automation platform',
        target_market: 'United States - FinCEN MSB, state money transmitter licenses',
        industry: 'SaaS',
        estimated_duration: '90-120 minutes',
        complexity: 'Medium'
    },
    {
        id: 'fintech_expansion',
        name: 'FinTech Expansion',
        description: 'Payment processing platform expansion into new markets',
        target_market: 'United States - Federal Reserve, FDIC, OCC regulated',
        industry: 'FinTech',
        estimated_duration: '120-150 minutes',
        complexity: 'High'
    }
];

// Mock showcase data
export const mockShowcaseData = {
    aws_services_used: [
        'Amazon Bedrock Nova (Claude-3 family)',
        'Amazon Bedrock AgentCore',
        'Amazon ECS Fargate',
        'Amazon CloudWatch',
        'Amazon S3'
    ],
    agentcore_primitives: [
        'Task Distribution',
        'Agent Coordination',
        'Message Routing',
        'State Management'
    ]
};

// Mock impact dashboard with complete chart data
export const mockImpactDashboard = {
    total_executions: 5,
    average_metrics: {
        time_reduction_percentage: 95.2,
        cost_savings_percentage: 82.1,
        confidence_score: 0.89,
        automation_level: 0.96
    },
    competition_totals: {
        autonomous_decisions_made: 120,
        reasoning_steps_completed: 780,
        inter_agent_communications: 210
    }
};

// Mock demo status
export const mockDemoStatus = {
    aws_configured: false,
    mode: 'mock',
    message: 'AWS not configured - using sample output for demonstration'
};

// Mock execution results with complete data
export const mockExecutionResults = {
    execution_id: 'demo-saas-123',
    scenario: 'saas_startup',
    status: 'completed',
    impact_metrics: {
        time_reduction_percentage: 95.2,
        cost_savings_percentage: 82.1,
        traditional_time_weeks: 4,
        ai_time_hours: 1.8,
        traditional_cost_usd: 150000,
        ai_cost_usd: 27000,
        confidence_score: 0.89,
        data_quality_score: 0.92,
        automation_level: 0.96
    },
    competition_metrics: {
        bedrock_nova_usage: {
            'claude-3-haiku': 45,
            'claude-3-sonnet': 32,
            'claude-3-opus': 18
        },
        agentcore_primitives_used: ['Task Distribution', 'Agent Coordination', 'Message Routing'],
        external_api_integrations: 8,
        autonomous_decisions_made: 24,
        reasoning_steps_completed: 156,
        inter_agent_communications: 42
    },
    agent_decision_log: [
        {
            timestamp: FIXED_DATE,
            agent: 'regulatory_compliance',
            decision: 'Compliance requirements identified',
            reasoning: 'Analyzed SEC, FINRA, and CFPB regulations applicable to payment processing',
            confidence: 0.92
        },
        {
            timestamp: FIXED_DATE,
            agent: 'fraud_detection',
            decision: 'Fraud risk assessment completed',
            reasoning: 'ML models detected 3 high-risk transaction patterns requiring monitoring',
            confidence: 0.95
        }
    ],
    before_after_comparison: {
        improvements: {
            time_saved: {
                explanation: '4 weeks → 1.8 hours (95.2% reduction)'
            },
            cost_reduced: {
                explanation: '$150,000 → $27,000 (82% savings)'
            },
            accuracy_improved: {
                explanation: 'AI-powered analysis with cross-agent validation'
            },
            automation_level: {
                explanation: 'Fully automated with human oversight'
            }
        }
    }
};

// Complete chart data for all dashboards
export const mockChartData = {
    fraudTrends: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
            {
                label: 'Fraud Cases Detected',
                data: [12, 19, 15, 25, 22, 18],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
            },
            {
                label: 'False Positives',
                data: [2, 3, 2, 4, 3, 2],
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
            }
        ]
    },
    complianceTrends: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [
            {
                label: 'Compliance Score',
                data: [92, 94, 93, 95],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
            }
        ]
    },
    riskDistribution: {
        labels: ['Low', 'Medium', 'High', 'Critical'],
        datasets: [
            {
                label: 'Risk Distribution',
                data: [45, 30, 20, 5],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(255, 159, 64, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                ],
            }
        ]
    },
    marketTrends: {
        labels: ['Q1', 'Q2', 'Q3', 'Q4'],
        datasets: [
            {
                label: 'Market Volatility',
                data: [0.12, 0.15, 0.18, 0.14],
                borderColor: 'rgb(153, 102, 255)',
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
            }
        ]
    }
};

// Complete agent results for all agent types
export const mockAgentResults = {
    regulatory_compliance: {
        agent_id: 'regulatory_compliance',
        status: 'completed',
        confidence: 0.92,
        findings: [
            'SEC filing requirements compliant',
            'FINRA rules adherence verified',
            'CFPB regulations reviewed'
        ],
        recommendations: [
            'Update quarterly reporting schedule',
            'Review new FINRA guidance on digital assets'
        ],
        processing_time: 3.2,
        data_sources: ['SEC.gov', 'FINRA.org', 'CFPB.gov']
    },
    fraud_detection: {
        agent_id: 'fraud_detection',
        status: 'completed',
        confidence: 0.95,
        anomalies_detected: 3,
        false_positive_rate: 0.05,
        high_risk_transactions: [
            {
                transaction_id: 'TXN-001',
                amount: 50000,
                fraud_probability: 0.98,
                risk_factors: ['Unusual amount', 'New merchant', 'Velocity spike']
            },
            {
                transaction_id: 'TXN-002',
                amount: 75000,
                fraud_probability: 0.89,
                risk_factors: ['Geographic anomaly', 'Time pattern unusual']
            }
        ],
        processing_time: 2.8,
        ml_models_used: ['isolation_forest', 'autoencoder', 'clustering']
    },
    risk_assessment: {
        agent_id: 'risk_assessment',
        status: 'completed',
        confidence: 0.88,
        overall_risk_score: 0.35,
        risk_level: 'medium',
        risk_categories: {
            credit_risk: 0.25,
            market_risk: 0.40,
            operational_risk: 0.30,
            liquidity_risk: 0.45
        },
        key_risk_factors: [
            'Market volatility elevated',
            'Credit exposure within limits',
            'Operational controls adequate'
        ],
        mitigation_recommendations: [
            'Increase liquidity reserves by 10%',
            'Review market exposure limits',
            'Enhance operational monitoring'
        ],
        processing_time: 4.1
    },
    market_analysis: {
        agent_id: 'market_analysis',
        status: 'completed',
        confidence: 0.87,
        market_segment: 'fintech',
        trend_direction: 'bullish',
        volatility_level: 0.15,
        key_drivers: [
            'Digital payment adoption increasing',
            'Regulatory clarity improving',
            'Investment activity strong'
        ],
        opportunities: [
            'Expansion into embedded finance',
            'B2B payment solutions',
            'Cross-border remittances'
        ],
        processing_time: 3.5,
        data_sources: ['Yahoo Finance', 'FRED', 'Treasury.gov']
    },
    kyc_verification: {
        agent_id: 'kyc_verification',
        status: 'completed',
        confidence: 0.91,
        verification_status: 'approved',
        risk_score: 0.15,
        documents_verified: ['ID', 'Proof of Address', 'Business Registration'],
        sanctions_screening: {
            status: 'clear',
            lists_checked: ['OFAC', 'UN', 'EU']
        },
        pep_screening: {
            status: 'clear',
            matches: 0
        },
        adverse_media_screening: {
            status: 'clear',
            articles_reviewed: 0
        },
        processing_time: 2.3
    },
    customer_behavior_intelligence: {
        agent_id: 'customer_behavior_intelligence',
        status: 'completed',
        confidence: 0.86,
        behavior_patterns: [
            'Regular transaction patterns',
            'Consistent geographic locations',
            'Normal velocity metrics'
        ],
        anomalies: [],
        churn_risk: 0.12,
        lifetime_value_estimate: 125000,
        recommendations: [
            'Maintain current engagement level',
            'Consider premium tier upgrade offer'
        ],
        processing_time: 3.0
    }
};

// Complete alert data for all alert types
export const mockAlerts = {
    fraud_alerts: [
        {
            alert_id: 'FRAUD-001',
            alert_type: 'fraud_detection',
            severity: 'high',
            title: 'High-Risk Transaction Detected',
            description: 'Transaction TXN-001 flagged with 98% fraud probability',
            entity_id: 'TXN-001',
            created_at: FIXED_DATE,
            metadata: {
                amount: 50000,
                merchant: 'Unknown Merchant',
                risk_factors: ['Unusual amount', 'New merchant']
            }
        },
        {
            alert_id: 'FRAUD-002',
            alert_type: 'fraud_detection',
            severity: 'medium',
            title: 'Suspicious Pattern Detected',
            description: 'Multiple transactions from same IP address',
            entity_id: 'PATTERN-001',
            created_at: FIXED_DATE_MINUS_30MIN,
            metadata: {
                transaction_count: 5,
                time_window: '15 minutes'
            }
        }
    ],
    compliance_alerts: [
        {
            alert_id: 'COMP-001',
            alert_type: 'compliance',
            severity: 'medium',
            title: 'Compliance Review Required',
            description: 'CFPB regulation requires manual review',
            entity_id: 'REG-CFPB-2024',
            created_at: FIXED_DATE_MINUS_30MIN,
            metadata: {
                regulation: 'CFPB Consumer Protection',
                deadline: '2024-11-01'
            }
        },
        {
            alert_id: 'COMP-002',
            alert_type: 'compliance',
            severity: 'low',
            title: 'Quarterly Report Due',
            description: 'SEC quarterly filing due in 30 days',
            entity_id: 'FILING-Q3-2024',
            created_at: FIXED_DATE,
            metadata: {
                filing_type: '10-Q',
                due_date: '2024-11-15'
            }
        }
    ],
    risk_alerts: [
        {
            alert_id: 'RISK-001',
            alert_type: 'risk_assessment',
            severity: 'high',
            title: 'Market Volatility Spike',
            description: 'Market volatility exceeded threshold',
            entity_id: 'MARKET-VOL-001',
            created_at: FIXED_DATE,
            metadata: {
                volatility_level: 0.25,
                threshold: 0.20,
                affected_positions: 15
            }
        }
    ],
    kyc_alerts: [
        {
            alert_id: 'KYC-001',
            alert_type: 'kyc_verification',
            severity: 'medium',
            title: 'Document Verification Pending',
            description: 'Customer KYC documents require review',
            entity_id: 'CUST-12345',
            created_at: FIXED_DATE,
            metadata: {
                customer_id: 'CUST-12345',
                documents_pending: ['Proof of Address']
            }
        }
    ]
};

// Complete analysis data for all analysis types
export const mockAnalysisData = {
    risk_analysis: {
        analysis_id: 'RISK-ANALYSIS-001',
        entity_id: 'ENTITY-001',
        entity_type: 'portfolio',
        status: 'completed',
        message: 'Risk analysis completed successfully',
        estimated_completion: FIXED_DATE,
        results: {
            overall_risk_score: 0.35,
            risk_level: 'medium',
            risk_categories: mockAgentResults.risk_assessment.risk_categories,
            key_risk_factors: mockAgentResults.risk_assessment.key_risk_factors,
            mitigation_recommendations: mockAgentResults.risk_assessment.mitigation_recommendations
        },
        processing_time: 4.1,
        confidence_score: 0.88
    },
    compliance_check: {
        analysis_id: 'COMP-CHECK-001',
        business_type: 'fintech_startup',
        jurisdiction: 'US',
        status: 'completed',
        message: 'Compliance check completed successfully',
        estimated_completion: FIXED_DATE,
        results: {
            compliance_status: 'compliant',
            compliance_score: 95,
            regulations_checked: ['SEC', 'FINRA', 'CFPB'],
            findings: mockAgentResults.regulatory_compliance.findings,
            recommendations: mockAgentResults.regulatory_compliance.recommendations
        },
        processing_time: 3.2,
        confidence_score: 0.92
    },
    fraud_detection: {
        analysis_id: 'FRAUD-DETECT-001',
        status: 'completed',
        message: 'Fraud detection analysis completed',
        estimated_completion: FIXED_DATE,
        results: {
            transactions_analyzed: 1000,
            anomalies_detected: 3,
            risk_level: 'medium',
            high_risk_transactions: mockAgentResults.fraud_detection.high_risk_transactions,
            false_positive_rate: 0.05
        },
        processing_time: 2.8,
        confidence_score: 0.95
    },
    market_intelligence: {
        analysis_id: 'MARKET-INTEL-001',
        market_segment: 'fintech',
        status: 'completed',
        message: 'Market intelligence analysis completed',
        estimated_completion: FIXED_DATE,
        results: {
            trend_direction: 'bullish',
            volatility_level: 0.15,
            key_drivers: mockAgentResults.market_analysis.key_drivers,
            opportunities: mockAgentResults.market_analysis.opportunities
        },
        processing_time: 3.5,
        confidence_score: 0.87
    },
    kyc_verification: {
        analysis_id: 'KYC-VERIFY-001',
        customer_id: 'CUST-12345',
        status: 'completed',
        message: 'KYC verification completed',
        estimated_completion: FIXED_DATE,
        results: {
            verification_status: 'approved',
            risk_score: 0.15,
            documents_verified: mockAgentResults.kyc_verification.documents_verified,
            sanctions_screening: mockAgentResults.kyc_verification.sanctions_screening
        },
        processing_time: 2.3,
        confidence_score: 0.91
    }
};

// Complete dashboard metrics for all metric types
export const mockDashboardMetrics = {
    fraud_prevention: {
        total_cases_detected: 156,
        total_losses_prevented: 5000000,
        false_positive_rate: 0.05,
        detection_accuracy: 0.95,
        average_response_time: 2.8,
        monthly_trend: [12, 15, 18, 14, 16, 15]
    },
    compliance_score: {
        overall_score: 95,
        sec_compliance: 98,
        finra_compliance: 94,
        cfpb_compliance: 93,
        trend: [92, 93, 94, 95],
        issues_resolved: 45,
        issues_pending: 2
    },
    risk_score: {
        overall_risk: 0.35,
        credit_risk: 0.25,
        market_risk: 0.40,
        operational_risk: 0.30,
        liquidity_risk: 0.45,
        trend: [0.38, 0.36, 0.34, 0.35],
        high_risk_entities: 5
    },
    market_intelligence: {
        market_sentiment: 0.65,
        volatility_index: 0.15,
        trend_direction: 'bullish',
        opportunities_identified: 12,
        risk_factors_monitored: 8,
        data_sources_active: 5
    },
    kyc_verification: {
        total_verifications: 234,
        approved: 198,
        rejected: 12,
        pending: 24,
        average_processing_time: 2.3,
        high_risk_customers: 8
    },
    business_value: {
        monthly_savings: 850000,
        fraud_prevented: 2100000,
        compliance_cost_reduction: 450000,
        roi_percentage: 340,
        payback_period_months: 3.5,
        total_annual_value: 10200000
    }
};

// Mock fetch responses with proper types
export const mockFetchResponses: Record<string, any> = {
    '/api/v1/dashboard/data': mockDashboardData,
    '/api/v1/compliance/status': mockComplianceData,
    '/api/v1/fraud/analytics': mockFraudData,
    '/api/v1/market/data': mockMarketData,
    '/api/v1/demo/executions': [mockExecutionData],
    '/api/v1/demo/executions/exec-123/results': mockExecutionData,
    '/api/v1/demo/impact-dashboard': mockImpactDashboard,
    '/api/v1/demo/status': mockDemoStatus,
    '/api/v1/demo/scenarios': mockDemoScenarios,
    '/api/v1/demo/competition-showcase': mockShowcaseData,
    '/api/v1/demo/executions/demo-saas-123/status': {
        execution_id: 'demo-saas-123',
        status: 'completed',
        impact_metrics: mockExecutionResults.impact_metrics
    },
    '/api/v1/demo/executions/demo-saas-123/results': mockExecutionResults,
    '/api/v1/charts/fraud-trends': mockChartData.fraudTrends,
    '/api/v1/charts/compliance-trends': mockChartData.complianceTrends,
    '/api/v1/charts/risk-distribution': mockChartData.riskDistribution,
    '/api/v1/charts/market-trends': mockChartData.marketTrends,
    '/api/v1/agents/regulatory-compliance/results': mockAgentResults.regulatory_compliance,
    '/api/v1/agents/fraud-detection/results': mockAgentResults.fraud_detection,
    '/api/v1/agents/risk-assessment/results': mockAgentResults.risk_assessment,
    '/api/v1/agents/market-analysis/results': mockAgentResults.market_analysis,
    '/api/v1/agents/kyc-verification/results': mockAgentResults.kyc_verification,
    '/api/v1/agents/customer-behavior/results': mockAgentResults.customer_behavior_intelligence,
    '/api/v1/alerts/fraud': mockAlerts.fraud_alerts,
    '/api/v1/alerts/compliance': mockAlerts.compliance_alerts,
    '/api/v1/alerts/risk': mockAlerts.risk_alerts,
    '/api/v1/alerts/kyc': mockAlerts.kyc_alerts,
    '/api/v1/analysis/risk': mockAnalysisData.risk_analysis,
    '/api/v1/analysis/compliance': mockAnalysisData.compliance_check,
    '/api/v1/analysis/fraud': mockAnalysisData.fraud_detection,
    '/api/v1/analysis/market': mockAnalysisData.market_intelligence,
    '/api/v1/analysis/kyc': mockAnalysisData.kyc_verification,
    '/api/v1/metrics/fraud-prevention': mockDashboardMetrics.fraud_prevention,
    '/api/v1/metrics/compliance-score': mockDashboardMetrics.compliance_score,
    '/api/v1/metrics/risk-score': mockDashboardMetrics.risk_score,
    '/api/v1/metrics/market-intelligence': mockDashboardMetrics.market_intelligence,
    '/api/v1/metrics/kyc-verification': mockDashboardMetrics.kyc_verification,
    '/api/v1/metrics/business-value': mockDashboardMetrics.business_value,
};

// Helper to setup fetch mocks with proper typing
export const setupFetchMocks = (): void => {
    // Create a proper jest mock function
    const mockFn = jest.fn((url: string | Request | URL): Promise<Response> => {
        const urlStr = typeof url === 'string' ? url : url.toString();
        const endpoint = Object.keys(mockFetchResponses).find(key => urlStr.includes(key));

        if (endpoint) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockFetchResponses[endpoint]),
                status: 200,
                statusText: 'OK',
            } as Response);
        }

        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({}),
            status: 200,
            statusText: 'OK',
        } as Response);
    });

    global.fetch = mockFn as any;
};

// Helper to reset fetch mocks with proper typing
export const resetFetchMocks = (): void => {
    if (global.fetch && jest.isMockFunction(global.fetch)) {
        (global.fetch as jest.Mock).mockClear();
    }
};
