-- Test seed data for RiskIntel360 Platform testing
-- This file contains realistic test data for comprehensive testing scenarios

-- Test users for different roles and scenarios
INSERT INTO users (id, email, tenant_id, roles, permissions, created_at, updated_at) VALUES
('test-user-001', 'analyst@testcorp.com', 'test-tenant-001', ARRAY['business_analyst'], ARRAY['validation.create', 'validation.read', 'validation.update'], NOW(), NOW()),
('test-user-002', 'executive@testcorp.com', 'test-tenant-001', ARRAY['executive'], ARRAY['validation.create', 'validation.read', 'validation.update', 'validation.delete', 'admin.read'], NOW(), NOW()),
('test-user-003', 'researcher@testcorp.com', 'test-tenant-001', ARRAY['researcher'], ARRAY['validation.read'], NOW(), NOW()),
('test-user-004', 'admin@testcorp.com', 'test-tenant-001', ARRAY['admin'], ARRAY['validation.create', 'validation.read', 'validation.update', 'validation.delete', 'admin.read', 'admin.write'], NOW(), NOW()),
('test-user-005', 'investor@fundco.com', 'test-tenant-002', ARRAY['investor'], ARRAY['validation.create', 'validation.read'], NOW(), NOW());

-- Test tenants for multi-tenant testing
INSERT INTO tenants (id, name, subscription_tier, settings, created_at, updated_at) VALUES
('test-tenant-001', 'TestCorp Inc.', 'enterprise', '{"max_validations_per_month": 100, "concurrent_validations": 10}', NOW(), NOW()),
('test-tenant-002', 'Fund Co Ventures', 'professional', '{"max_validations_per_month": 50, "concurrent_validations": 5}', NOW(), NOW()),
('test-tenant-003', 'Startup Accelerator', 'basic', '{"max_validations_per_month": 20, "concurrent_validations": 2}', NOW(), NOW());

-- Test validation requests for different business scenarios
INSERT INTO validation_requests (id, user_id, tenant_id, business_concept, target_market, analysis_scope, priority, status, custom_parameters, created_at, updated_at) VALUES
-- SaaS Startup Scenario
('test-validation-001', 'test-user-001', 'test-tenant-001', 
 'AI-powered customer service chatbot for e-commerce platforms', 
 'Small to medium e-commerce businesses in North America', 
 ARRAY['market', 'competitive', 'financial', 'risk', 'customer'], 
 'high', 'completed',
 '{"budget_range": "100000-500000", "timeline": "12-months", "target_revenue": "2000000", "team_size": "5-10"}',
 NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day'),

-- FinTech Innovation Scenario  
('test-validation-002', 'test-user-002', 'test-tenant-001',
 'Digital banking platform for underbanked communities',
 'Underbanked populations in emerging markets',
 ARRAY['market', 'competitive', 'financial', 'risk', 'customer'],
 'high', 'in_progress',
 '{"budget_range": "5000000-10000000", "timeline": "24-months", "regulatory_requirements": "high", "compliance_focus": "financial_services"}',
 NOW() - INTERVAL '1 day', NOW()),

-- HealthTech Platform Scenario
('test-validation-003', 'test-user-005', 'test-tenant-002',
 'Telemedicine platform for rural healthcare access',
 'Rural communities with limited healthcare access',
 ARRAY['market', 'competitive', 'financial', 'risk', 'customer'],
 'medium', 'pending',
 '{"budget_range": "1000000-3000000", "timeline": "18-months", "regulatory_requirements": "high", "target_demographics": "rural_populations"}',
 NOW() - INTERVAL '6 hours', NOW()),

-- EdTech Solution Scenario
('test-validation-004', 'test-user-001', 'test-tenant-001',
 'Professional development platform for remote workers',
 'Remote workers and distributed teams globally',
 ARRAY['market', 'competitive', 'financial', 'customer'],
 'medium', 'draft',
 '{"budget_range": "500000-1000000", "timeline": "9-months", "target_market_size": "global", "delivery_model": "subscription"}',
 NOW() - INTERVAL '3 hours', NOW()),

-- B2B SaaS Scenario
('test-validation-005', 'test-user-002', 'test-tenant-001',
 'Supply chain optimization platform using AI and IoT',
 'Manufacturing companies with complex supply chains',
 ARRAY['market', 'competitive', 'financial', 'risk', 'customer'],
 'high', 'queued',
 '{"budget_range": "2000000-5000000", "timeline": "15-months", "industry_focus": "manufacturing", "technology_stack": "ai_iot"}',
 NOW() - INTERVAL '1 hour', NOW());

-- Test validation results for completed scenarios
INSERT INTO validation_results (id, request_id, overall_score, confidence_level, market_analysis, competitive_analysis, financial_analysis, risk_analysis, customer_analysis, strategic_recommendations, supporting_data, generated_at) VALUES
('test-result-001', 'test-validation-001', 78.5, 0.85,
 '{"market_size": "$2.5B", "growth_rate": "15% CAGR", "key_trends": ["AI adoption", "Remote work", "Digital transformation"], "market_maturity": "growth", "entry_barriers": ["Technology complexity", "Customer acquisition cost"]}',
 '{"direct_competitors": ["Zendesk", "Intercom", "Freshworks"], "indirect_competitors": ["Salesforce Service Cloud", "Microsoft Dynamics"], "competitive_intensity": "high", "market_positioning": "differentiated", "competitive_advantages": ["AI-powered automation", "E-commerce specialization"]}',
 '{"revenue_projection": 2500000, "investment_required": 750000, "roi_estimate": "233%", "break_even_months": 18, "key_metrics": {"customer_acquisition_cost": 150, "lifetime_value": 2400, "monthly_recurring_revenue": 125000}}',
 '{"risk_level": "medium", "key_risks": ["Market competition", "Technology adoption", "Regulatory changes"], "mitigation_strategies": ["Patent protection", "Strategic partnerships", "Compliance monitoring"], "probability_scores": {"market_risk": 0.6, "technology_risk": 0.4, "regulatory_risk": 0.3}}',
 '{"target_segments": ["SMB E-commerce", "Enterprise Retail"], "customer_sentiment": "positive", "adoption_likelihood": "high", "personas": [{"name": "E-commerce Manager", "pain_points": ["Manual customer service", "High response times"], "willingness_to_pay": "high"}]}',
 '[{"recommendation": "Proceed with development", "priority": "high", "rationale": "Strong market demand and competitive differentiation"}, {"recommendation": "Focus on SMB segment initially", "priority": "medium", "rationale": "Lower customer acquisition cost and faster adoption"}]',
 '{"data_sources": ["Market research reports", "Competitor analysis", "Customer surveys"], "confidence_factors": {"market_data": 0.9, "competitive_data": 0.8, "financial_projections": 0.85}}',
 NOW() - INTERVAL '1 day');

-- Test agent execution logs for monitoring and debugging
INSERT INTO agent_execution_logs (id, request_id, agent_id, status, start_time, end_time, execution_time_ms, input_data, output_data, error_message, performance_metrics) VALUES
('test-log-001', 'test-validation-001', 'MARKET_ANALYSIS', 'completed', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '45 seconds', 45000,
 '{"business_concept": "AI-powered customer service chatbot", "target_market": "SMB e-commerce"}',
 '{"market_size": "$2.5B", "growth_rate": "15% CAGR", "confidence_score": 0.85}',
 NULL,
 '{"tokens_used": 1250, "api_calls": 3, "cache_hits": 2, "memory_usage_mb": 128}'),

('test-log-002', 'test-validation-001', 'REGULATORY_COMPLIANCE', 'completed', NOW() - INTERVAL '2 days' + INTERVAL '1 minute', NOW() - INTERVAL '2 days' + INTERVAL '1 minute 38 seconds', 38000,
 '{"business_concept": "AI-powered customer service chatbot", "market_context": "SMB e-commerce"}',
 '{"direct_competitors": ["Zendesk", "Intercom"], "competitive_intensity": "high", "confidence_score": 0.78}',
 NULL,
 '{"tokens_used": 1850, "api_calls": 5, "cache_hits": 1, "memory_usage_mb": 156}'),

('test-log-003', 'test-validation-001', 'FRAUD_DETECTION', 'completed', NOW() - INTERVAL '2 days' + INTERVAL '2 minutes', NOW() - INTERVAL '2 days' + INTERVAL '2 minutes 52 seconds', 52000,
 '{"business_concept": "AI-powered customer service chatbot", "market_size": "$2.5B", "investment_required": 750000}',
 '{"revenue_projection": 2500000, "roi_estimate": "233%", "confidence_score": 0.82}',
 NULL,
 '{"tokens_used": 2100, "api_calls": 4, "cache_hits": 0, "memory_usage_mb": 189}');

-- Test system metrics for performance monitoring
INSERT INTO system_metrics (id, metric_name, metric_value, metric_type, tags, timestamp) VALUES
('test-metric-001', 'validation_completion_time', 7200.0, 'gauge', '{"validation_id": "test-validation-001", "agent_count": 6}', NOW() - INTERVAL '1 day'),
('test-metric-002', 'agent_response_time', 45.0, 'gauge', '{"agent_id": "MARKET_ANALYSIS", "validation_id": "test-validation-001"}', NOW() - INTERVAL '1 day'),
('test-metric-003', 'concurrent_validations', 3.0, 'gauge', '{"tenant_id": "test-tenant-001"}', NOW() - INTERVAL '1 hour'),
('test-metric-004', 'api_request_count', 1250.0, 'counter', '{"endpoint": "/api/v1/validations", "status": "200"}', NOW() - INTERVAL '1 hour'),
('test-metric-005', 'memory_usage', 512.0, 'gauge', '{"service": "riskintel360-api", "container": "test"}', NOW() - INTERVAL '30 minutes');

-- Test API keys and configuration for external services (encrypted/mock values)
INSERT INTO api_configurations (id, service_name, api_key_hash, endpoint_url, rate_limit, is_active, created_at, updated_at) VALUES
('test-config-001', 'alpha_vantage', 'mock_encrypted_key_001', 'https://www.alphavantage.co/query', 5, true, NOW(), NOW()),
('test-config-002', 'news_api', 'mock_encrypted_key_002', 'https://newsapi.org/v2', 1000, true, NOW(), NOW()),
('test-config-003', 'crunchbase', 'mock_encrypted_key_003', 'https://api.crunchbase.com/api/v4', 200, false, NOW(), NOW()),
('test-config-004', 'yahoo_finance', 'mock_encrypted_key_004', 'https://query1.finance.yahoo.com/v8', 2000, true, NOW(), NOW());

-- Test business scenarios for comprehensive testing
INSERT INTO test_scenarios (id, scenario_name, description, input_data, expected_outcomes, test_type, created_at) VALUES
('scenario-001', 'SaaS Startup Market Entry', 'Test complete validation workflow for SaaS startup entering competitive market',
 '{"business_concept": "AI customer service", "target_market": "SMB e-commerce", "budget": 500000, "timeline": 12}',
 '{"overall_score_range": [70, 85], "completion_time_max": 7200, "agent_success_rate": 1.0}',
 'end_to_end', NOW()),

('scenario-002', 'FinTech Regulatory Compliance', 'Test validation workflow with high regulatory requirements',
 '{"business_concept": "Digital banking", "target_market": "Emerging markets", "regulatory_focus": "high", "budget": 5000000}',
 '{"risk_score_min": 0.6, "compliance_flags": ["regulatory", "financial"], "completion_time_max": 7200}',
 'regulatory_focus', NOW()),

('scenario-003', 'High-Load Concurrent Processing', 'Test system performance under high concurrent validation load',
 '{"concurrent_validations": 50, "duration_minutes": 10, "user_types": ["analyst", "executive", "investor"]}',
 '{"success_rate_min": 0.95, "avg_response_time_max": 5.0, "error_rate_max": 0.05}',
 'performance', NOW()),

('scenario-004', 'Error Recovery and Graceful Degradation', 'Test system behavior during external service failures',
 '{"failure_scenarios": ["api_timeout", "database_connection", "redis_unavailable"], "recovery_expected": true}',
 '{"graceful_degradation": true, "user_notification": true, "partial_results": true}',
 'error_handling', NOW()),

('scenario-005', 'Real-time Progress Monitoring', 'Test WebSocket real-time updates during validation workflow',
 '{"websocket_connection": true, "progress_updates": true, "agent_status_tracking": true}',
 '{"update_frequency_max": 5.0, "connection_stability": true, "progress_accuracy": 0.95}',
 'real_time', NOW());

-- Test user preferences and customization settings
INSERT INTO user_preferences (id, user_id, preferences, created_at, updated_at) VALUES
('pref-001', 'test-user-001', '{"dashboard_layout": "executive", "notification_settings": {"email": true, "websocket": true}, "default_analysis_scope": ["market", "competitive", "financial"]}', NOW(), NOW()),
('pref-002', 'test-user-002', '{"dashboard_layout": "detailed", "notification_settings": {"email": true, "websocket": true, "sms": false}, "default_analysis_scope": ["market", "competitive", "financial", "risk", "customer"]}', NOW(), NOW()),
('pref-003', 'test-user-005', '{"dashboard_layout": "investor", "notification_settings": {"email": true, "websocket": false}, "default_analysis_scope": ["financial", "risk"]}', NOW(), NOW());

-- Commit the test data
COMMIT;

-- Create indexes for better test performance
CREATE INDEX IF NOT EXISTS idx_test_validation_requests_user_id ON validation_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_test_validation_requests_status ON validation_requests(status);
CREATE INDEX IF NOT EXISTS idx_test_validation_requests_created_at ON validation_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_test_agent_execution_logs_request_id ON agent_execution_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_test_agent_execution_logs_agent_id ON agent_execution_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_test_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_test_system_metrics_metric_name ON system_metrics(metric_name);

-- Analyze tables for better query performance
ANALYZE validation_requests;
ANALYZE validation_results;
ANALYZE agent_execution_logs;
ANALYZE system_metrics;
ANALYZE users;
ANALYZE tenants;