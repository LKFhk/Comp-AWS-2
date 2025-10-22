"""
Monitoring Integration Module
Integrates monitoring service with agents and provides comprehensive observability.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json

from riskintel360.services.monitoring_service import (
    get_monitoring_service, 
    MonitoringService,
    AlertSeverity,
    TraceContext,
    monitor_performance
)
from riskintel360.services.monitoring_dashboards import (
    MonitoringDashboards,
    DashboardType
)
from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)


class MonitoringIntegration:
    """Integration layer for comprehensive platform monitoring"""
    
    def __init__(self):
        self.settings = get_settings()
        self.monitoring = get_monitoring_service()
        self.dashboards = MonitoringDashboards()
        
        # Performance thresholds
        self.performance_thresholds = {
            'agent_response_time_ms': 5000,  # 5 seconds
            'validation_completion_minutes': 120,  # 2 hours
            'error_rate_percent': 5.0,  # 5%
            'availability_percent': 99.9  # 99.9%
        }
        
        # Initialize monitoring
        self._initialize_monitoring()
    
    def _initialize_monitoring(self) -> None:
        """Initialize monitoring integration"""
        try:
            # Register alert handlers
            self.monitoring.add_alert_handler(self._handle_performance_alert)
            self.monitoring.add_alert_handler(self._handle_error_alert)
            
            logger.info("Monitoring integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring integration: {e}")
    
    # Agent Performance Monitoring
    @monitor_performance("agent_execution")
    async def monitor_agent_execution(
        self,
        agent_name: str,
        operation: str,
        execution_func,
        *args,
        **kwargs
    ) -> Any:
        """Monitor agent execution with comprehensive tracking"""
        
        with TraceContext(
            f"{agent_name}_{operation}",
            tags={
                'agent': agent_name,
                'operation': operation,
                'component': 'agent_execution'
            }
        ) as span_id:
            try:
                # Record agent start
                self.monitoring.increment_counter(
                    "AgentExecutionStarted",
                    dimensions={
                        'Agent': agent_name,
                        'Operation': operation
                    }
                )
                
                # Execute agent function
                result = await execution_func(*args, **kwargs)
                
                # Record success metrics
                self.monitoring.increment_counter(
                    "AgentExecutionSuccess",
                    dimensions={
                        'Agent': agent_name,
                        'Operation': operation
                    }
                )
                
                # Record confidence score if available
                if hasattr(result, 'confidence_score'):
                    self.monitoring.record_gauge(
                        "ConfidenceScore",
                        result.confidence_score,
                        "None",
                        dimensions={'Agent': agent_name}
                    )
                
                self.monitoring.add_trace_log(
                    span_id,
                    "info",
                    f"Agent {agent_name} completed {operation} successfully"
                )
                
                return result
                
            except Exception as e:
                # Record error metrics
                self.monitoring.increment_counter(
                    "AgentExecutionError",
                    dimensions={
                        'Agent': agent_name,
                        'Operation': operation,
                        'ErrorType': type(e).__name__
                    }
                )
                
                self.monitoring.add_trace_log(
                    span_id,
                    "error",
                    f"Agent {agent_name} failed {operation}: {str(e)}"
                )
                
                # Create alert for agent failure
                await self.monitoring.create_alert(
                    f"Agent Execution Failed: {agent_name}",
                    f"Agent {agent_name} failed to complete {operation}: {str(e)}",
                    AlertSeverity.ERROR,
                    component=agent_name,
                    metadata={
                        'operation': operation,
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                )
                
                raise
    
    # Validation Workflow Monitoring
    async def monitor_validation_workflow(
        self,
        workflow_id: str,
        user_id: str,
        validation_request: Dict[str, Any]
    ) -> None:
        """Monitor complete validation workflow"""
        
        with TraceContext(
            "validation_workflow",
            tags={
                'workflow_id': workflow_id,
                'user_id': user_id,
                'business_concept': validation_request.get('business_concept', 'unknown')
            }
        ) as span_id:
            
            # Record workflow start
            self.monitoring.increment_counter(
                "ValidationWorkflowStarted",
                dimensions={
                    'UserId': user_id,
                    'BusinessConcept': validation_request.get('business_concept', 'unknown')
                }
            )
            
            # Track workflow progress
            self.monitoring.add_trace_log(
                span_id,
                "info",
                f"Started validation workflow {workflow_id}",
                metadata={
                    'validation_request': validation_request,
                    'user_id': user_id
                }
            )
    
    async def complete_validation_workflow(
        self,
        workflow_id: str,
        duration_minutes: float,
        success: bool,
        results: Optional[Dict[str, Any]] = None
    ) -> None:
        """Complete validation workflow monitoring"""
        
        # Record completion metrics
        if success:
            self.monitoring.increment_counter(
                "ValidationWorkflowCompleted",
                dimensions={'Status': 'Success'}
            )
            
            # Record completion time
            self.monitoring.record_timer(
                "ValidationCompletionTime",
                duration_minutes * 60 * 1000,  # Convert to milliseconds
                dimensions={'Type': 'EndToEnd'}
            )
            
            # Check if completion time exceeds threshold
            if duration_minutes > self.performance_thresholds['validation_completion_minutes']:
                await self.monitoring.create_alert(
                    "Validation Completion Time Exceeded",
                    f"Validation workflow {workflow_id} took {duration_minutes:.1f} minutes (threshold: {self.performance_thresholds['validation_completion_minutes']} minutes)",
                    AlertSeverity.WARNING,
                    component="validation_workflow",
                    metadata={
                        'workflow_id': workflow_id,
                        'duration_minutes': duration_minutes,
                        'threshold_minutes': self.performance_thresholds['validation_completion_minutes']
                    }
                )
            
            # Record business impact metrics
            if results:
                time_saved_hours = results.get('time_saved_hours', 0)
                cost_saved_dollars = results.get('cost_saved_dollars', 0)
                
                self.monitoring.record_gauge(
                    "CostSavings",
                    time_saved_hours * 100,  # Assuming $100/hour
                    "None",
                    dimensions={'Type': 'TimeReduction'}
                )
                
                self.monitoring.record_gauge(
                    "CostSavings",
                    cost_saved_dollars,
                    "None",
                    dimensions={'Type': 'AutomationBenefit'}
                )
        
        else:
            self.monitoring.increment_counter(
                "ValidationWorkflowCompleted",
                dimensions={'Status': 'Failed'}
            )
            
            await self.monitoring.create_alert(
                "Validation Workflow Failed",
                f"Validation workflow {workflow_id} failed to complete",
                AlertSeverity.ERROR,
                component="validation_workflow",
                metadata={'workflow_id': workflow_id}
            )
    
    # System Health Monitoring
    async def monitor_system_health(self) -> Dict[str, Any]:
        """Monitor overall system health"""
        
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'metrics': {},
            'alerts': []
        }
        
        try:
            # Check component health
            components = [
                'bedrock_client',
                'agentcore_client',
                'database',
                'redis',
                'external_apis'
            ]
            
            for component in components:
                try:
                    # Simulate health check (in real implementation, these would be actual checks)
                    await self.monitoring.register_health_check(
                        component,
                        lambda: True,  # Placeholder health check
                        timeout_seconds=5
                    )
                    
                    health_status['components'][component] = 'healthy'
                    
                except Exception as e:
                    health_status['components'][component] = 'unhealthy'
                    health_status['overall_status'] = 'degraded'
                    
                    await self.monitoring.create_alert(
                        f"Component Health Check Failed: {component}",
                        f"Health check for {component} failed: {str(e)}",
                        AlertSeverity.WARNING,
                        component=component
                    )
            
            # Get performance metrics
            perf_stats = self.monitoring.get_performance_stats()
            health_status['metrics'] = {
                'active_operations': len(perf_stats),
                'total_operations': sum(
                    stats.get('total_calls', 0) 
                    for stats in perf_stats.values()
                ),
                'error_rate': self._calculate_error_rate(perf_stats)
            }
            
            # Check error rate threshold
            error_rate = health_status['metrics']['error_rate']
            if error_rate > self.performance_thresholds['error_rate_percent']:
                health_status['overall_status'] = 'degraded'
                
                await self.monitoring.create_alert(
                    "High Error Rate Detected",
                    f"System error rate is {error_rate:.1f}% (threshold: {self.performance_thresholds['error_rate_percent']}%)",
                    AlertSeverity.WARNING,
                    component="system_health",
                    metadata={
                        'error_rate': error_rate,
                        'threshold': self.performance_thresholds['error_rate_percent']
                    }
                )
            
            # Record system health metrics
            health_value = 1.0 if health_status['overall_status'] == 'healthy' else 0.5 if health_status['overall_status'] == 'degraded' else 0.0
            
            self.monitoring.record_gauge(
                "SystemHealth",
                health_value,
                "None",
                dimensions={'System': 'RiskIntel360'}
            )
            
        except Exception as e:
            logger.error(f"Error monitoring system health: {e}")
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    def _calculate_error_rate(self, perf_stats: Dict[str, Any]) -> float:
        """Calculate overall error rate from performance stats"""
        total_calls = 0
        total_errors = 0
        
        for stats in perf_stats.values():
            total_calls += stats.get('total_calls', 0)
            total_errors += stats.get('error_count', 0)
        
        if total_calls == 0:
            return 0.0
        
        return (total_errors / total_calls) * 100
    
    # External API Monitoring
    async def monitor_external_api_call(
        self,
        api_name: str,
        endpoint: str,
        api_call_func,
        *args,
        **kwargs
    ) -> Any:
        """Monitor external API calls"""
        
        with TraceContext(
            f"external_api_{api_name}",
            tags={
                'api': api_name,
                'endpoint': endpoint,
                'component': 'external_api'
            }
        ) as span_id:
            
            timer_id = self.monitoring.start_performance_timer(f"external_api_{api_name}")
            
            try:
                result = await api_call_func(*args, **kwargs)
                
                # Record success
                self.monitoring.end_performance_timer(
                    timer_id, f"external_api_{api_name}", success=True
                )
                
                self.monitoring.increment_counter(
                    "ExternalAPISuccess",
                    dimensions={
                        'API': api_name,
                        'Endpoint': endpoint
                    }
                )
                
                return result
                
            except Exception as e:
                # Record error
                self.monitoring.end_performance_timer(
                    timer_id, f"external_api_{api_name}", success=False, error_message=str(e)
                )
                
                self.monitoring.increment_counter(
                    "ExternalAPIErrors",
                    dimensions={
                        'API': api_name,
                        'Endpoint': endpoint,
                        'ErrorType': type(e).__name__
                    }
                )
                
                self.monitoring.add_trace_log(
                    span_id,
                    "error",
                    f"External API call failed: {api_name}/{endpoint}",
                    metadata={
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                )
                
                raise
    
    # Dashboard Management
    async def create_all_dashboards(self) -> Dict[str, bool]:
        """Create all CloudWatch dashboards"""
        results = {}
        
        try:
            dashboards = self.dashboards.get_all_dashboards()
            dashboard_names = self.dashboards.get_dashboard_names()
            
            for dashboard_type, dashboard_config in dashboards.items():
                dashboard_name = dashboard_names[dashboard_type]
                
                try:
                    # Create dashboard using monitoring service
                    if self.monitoring._cloudwatch_client:
                        self.monitoring._cloudwatch_client.put_dashboard(
                            DashboardName=dashboard_name,
                            DashboardBody=json.dumps(dashboard_config)
                        )
                        results[dashboard_name] = True
                        logger.info(f"Created dashboard: {dashboard_name}")
                    else:
                        results[dashboard_name] = False
                        logger.warning(f"CloudWatch client not available for dashboard: {dashboard_name}")
                        
                except Exception as e:
                    results[dashboard_name] = False
                    logger.error(f"Failed to create dashboard {dashboard_name}: {e}")
            
        except Exception as e:
            logger.error(f"Error creating dashboards: {e}")
        
        return results
    
    # Alert Handlers
    async def _handle_performance_alert(self, alert_data: Dict[str, Any]) -> None:
        """Handle performance-related alerts"""
        try:
            severity = alert_data.get('severity', 'info')
            component = alert_data.get('component', 'unknown')
            
            # Log performance alert
            logger.warning(f"Performance alert for {component}: {alert_data.get('title', 'Unknown')}")
            
            # Record performance degradation metric
            self.monitoring.increment_counter(
                "PerformanceDegradation",
                dimensions={
                    'Component': component,
                    'Severity': severity,
                    'Type': 'ResponseTime'
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling performance alert: {e}")
    
    async def _handle_error_alert(self, alert_data: Dict[str, Any]) -> None:
        """Handle error-related alerts"""
        try:
            severity = alert_data.get('severity', 'info')
            component = alert_data.get('component', 'unknown')
            
            # Log error alert
            logger.error(f"Error alert for {component}: {alert_data.get('title', 'Unknown')}")
            
            # Record error alert metric
            self.monitoring.increment_counter(
                "ErrorAlerts",
                dimensions={
                    'Component': component,
                    'Severity': severity
                }
            )
            
            # If critical, trigger additional monitoring
            if severity == 'critical':
                await self._trigger_critical_monitoring(component, alert_data)
                
        except Exception as e:
            logger.error(f"Error handling error alert: {e}")
    
    async def _trigger_critical_monitoring(
        self,
        component: str,
        alert_data: Dict[str, Any]
    ) -> None:
        """Trigger enhanced monitoring for critical alerts"""
        try:
            # Increase monitoring frequency
            logger.critical(f"Critical alert triggered for {component}, enhancing monitoring")
            
            # Record critical event
            self.monitoring.increment_counter(
                "CriticalEvents",
                dimensions={'Component': component}
            )
            
            # Could trigger additional actions like:
            # - Increase health check frequency
            # - Enable detailed logging
            # - Notify on-call team
            # - Trigger auto-scaling
            
        except Exception as e:
            logger.error(f"Error in critical monitoring trigger: {e}")
    
    # Reporting and Analytics
    def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        try:
            summary = self.monitoring.get_monitoring_summary()
            perf_stats = self.monitoring.get_performance_stats()
            
            report = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_health': {
                    'overall_status': 'healthy',  # Would be calculated from actual health checks
                    'components_monitored': summary['health']['components_monitored'],
                    'healthy_components': summary['health']['healthy_components']
                },
                'performance': {
                    'total_operations': len(perf_stats),
                    'error_rate': self._calculate_error_rate(perf_stats),
                    'avg_response_time': self._calculate_avg_response_time(perf_stats)
                },
                'monitoring': {
                    'active_traces': summary['tracing']['active_traces'],
                    'metrics_buffer_size': summary['metrics']['buffer_size'],
                    'alert_handlers': summary['alerts']['handlers_registered']
                },
                'thresholds': self.performance_thresholds
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating monitoring report: {e}")
            return {'error': str(e)}
    
    def _calculate_avg_response_time(self, perf_stats: Dict[str, Any]) -> float:
        """Calculate average response time across all operations"""
        total_duration = 0
        total_calls = 0
        
        for stats in perf_stats.values():
            total_duration += stats.get('total_duration_ms', 0)
            total_calls += stats.get('total_calls', 0)
        
        if total_calls == 0:
            return 0.0
        
        return total_duration / total_calls


# Global monitoring integration instance
_monitoring_integration: Optional[MonitoringIntegration] = None


def get_monitoring_integration() -> MonitoringIntegration:
    """Get the global monitoring integration instance"""
    global _monitoring_integration
    if _monitoring_integration is None:
        _monitoring_integration = MonitoringIntegration()
    return _monitoring_integration
