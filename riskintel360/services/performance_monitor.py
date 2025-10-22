"""
Performance monitoring service for RiskIntel360.

This service tracks agent response times, workflow execution times, system uptime,
and concurrent request handling capacity to ensure competition requirements are met.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    metric_name: str
    threshold_value: float
    comparison_operator: str = "greater_than"  # "greater_than", "less_than", "equals"
    severity: str = "medium"  # "low", "medium", "high", "critical"
    enabled: bool = True


@dataclass
class SystemHealthStatus:
    """System health status"""
    is_healthy: bool
    uptime_seconds: float
    availability_percentage: float
    active_requests: int
    error_rate: float
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    agent_response_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    workflow_execution_times: Dict[str, float] = field(default_factory=dict)
    system_uptime_start: datetime = field(default_factory=datetime.now)
    concurrent_requests: int = 0
    max_concurrent_requests: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    availability_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_agent_avg_response_time(self, agent_type: str) -> float:
        """Get average response time for an agent type"""
        times = self.agent_response_times.get(agent_type, [])
        return sum(times) / len(times) if times else 0.0
    
    def get_system_uptime(self) -> timedelta:
        """Get current system uptime"""
        return datetime.now() - self.system_uptime_start
    
    def get_availability_percentage(self) -> float:
        """Calculate system availability percentage"""
        if not self.availability_events:
            return 100.0
        
        total_time = self.get_system_uptime().total_seconds()
        downtime = sum(
            event.get('duration', 0) 
            for event in self.availability_events 
            if event.get('type') == 'downtime'
        )
        
        if total_time <= 0:
            return 100.0
        
        availability = ((total_time - downtime) / total_time) * 100
        return max(0.0, min(100.0, availability))


class PerformanceMonitor:
    """
    Performance monitoring service for RiskIntel360.
    
    Tracks:
    - Agent response times (< 5 second requirement)
    - Workflow execution times (< 2 hour requirement)
    - System uptime and availability (99.9% requirement)
    - Concurrent request handling (50+ requests requirement)
    """
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self._active_requests: Dict[str, float] = {}
        self._active_workflows: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._monitoring_active = True  # Start monitoring by default
        self._alert_thresholds = {
            'agent_response_time': 5.0,  # 5 seconds
            'workflow_execution_time': 7200.0,  # 2 hours
            'availability_target': 99.9,  # 99.9%
            'max_concurrent_requests': 50  # 50+ requests
        }
        
        logger.info("PerformanceMonitor initialized with monitoring active")
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        self._monitoring_active = True
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self._monitoring_active = False
        logger.info("Performance monitoring stopped")
    
    async def record_agent_performance(self, agent_id: str, agent_type: Any, 
                                      response_time: float, success_rate: float,
                                      timestamp: datetime = None):
        """Record agent performance metrics"""
        if not self._monitoring_active:
            return
        
        with self._lock:
            agent_type_str = str(agent_type.value if hasattr(agent_type, 'value') else agent_type)
            self.metrics.agent_response_times[agent_type_str].append(response_time)
            self.metrics.total_requests += 1
            
            if success_rate < 1.0:
                self.metrics.failed_requests += 1
        
        logger.debug(f"Recorded performance for agent {agent_id}: {response_time:.2f}s")
    
    async def record_workflow_performance(self, workflow_id: str, workflow_type: str,
                                         execution_time: float, status: str,
                                         start_time: datetime = None, end_time: datetime = None,
                                         agent_count: int = 0, error_message: str = None):
        """Record workflow performance metrics"""
        if not self._monitoring_active:
            return
        
        with self._lock:
            self.metrics.workflow_execution_times[workflow_id] = execution_time
        
        logger.debug(f"Recorded workflow {workflow_id}: {execution_time:.2f}s")
    
    async def record_health_check(self, health_status: SystemHealthStatus):
        """Record system health check"""
        if not self._monitoring_active:
            return
        
        if not health_status.is_healthy:
            with self._lock:
                self.metrics.availability_events.append({
                    'type': 'health_check_failed',
                    'timestamp': health_status.last_check,
                    'error_rate': health_status.error_rate
                })
        
        logger.debug(f"Health check recorded: {'healthy' if health_status.is_healthy else 'unhealthy'}")
    
    async def record_request_start(self, request_id: str, endpoint: str, timestamp: datetime = None):
        """Record request start"""
        if not self._monitoring_active:
            return
        
        with self._lock:
            self._active_requests[request_id] = time.time()
            self.metrics.concurrent_requests += 1
            self.metrics.max_concurrent_requests = max(
                self.metrics.max_concurrent_requests,
                self.metrics.concurrent_requests
            )
    
    async def record_request_completion(self, request_id: str, response_time: float, 
                                       status_code: int, timestamp: datetime = None):
        """Record request completion"""
        if not self._monitoring_active:
            return
        
        with self._lock:
            self._active_requests.pop(request_id, None)
            self.metrics.concurrent_requests = max(0, self.metrics.concurrent_requests - 1)
            
            if status_code >= 400:
                self.metrics.failed_requests += 1
    
    async def get_current_concurrent_requests(self) -> int:
        """Get current number of concurrent requests"""
        with self._lock:
            return self.metrics.concurrent_requests
    
    async def get_agent_metrics(self, time_window: str = "1h") -> List[Dict[str, Any]]:
        """Get agent metrics for specified time window"""
        with self._lock:
            return [
                {
                    'agent_type': agent_type,
                    'avg_response_time': sum(times) / len(times) if times else 0.0,
                    'total_requests': len(times),
                    'max_response_time': max(times) if times else 0.0,
                    'min_response_time': min(times) if times else 0.0
                }
                for agent_type, times in self.metrics.agent_response_times.items()
            ]
    
    async def get_workflow_metrics(self, time_window: str = "1h") -> List[Dict[str, Any]]:
        """Get workflow metrics for specified time window"""
        with self._lock:
            return [
                {
                    'workflow_id': workflow_id,
                    'execution_time': execution_time
                }
                for workflow_id, execution_time in self.metrics.workflow_execution_times.items()
            ]
    
    async def get_uptime_metrics(self, time_window: str = "24h") -> Dict[str, Any]:
        """Get uptime metrics for specified time window"""
        with self._lock:
            return {
                'uptime_seconds': self.metrics.get_system_uptime().total_seconds(),
                'availability_percentage': self.metrics.get_availability_percentage(),
                'downtime_events': len([e for e in self.metrics.availability_events if e.get('type') == 'downtime'])
            }
    
    async def get_request_metrics(self, time_window: str = "1h") -> Any:
        """Get request metrics for specified time window"""
        with self._lock:
            class RequestMetrics:
                def __init__(self, total, failed, max_concurrent):
                    self.total_requests = total
                    self.failed_requests = failed
                    self.max_concurrent_requests = max_concurrent
            
            return RequestMetrics(
                self.metrics.total_requests,
                self.metrics.failed_requests,
                self.metrics.max_concurrent_requests
            )
    
    async def configure_alert_threshold(self, threshold: AlertThreshold):
        """Configure alert threshold"""
        logger.info(f"Configured alert threshold: {threshold.metric_name} = {threshold.threshold_value}")
    
    async def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get active performance alerts"""
        # Placeholder - in production this would return actual alerts
        return []
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data"""
        return self.get_performance_dashboard_data()
    
    @asynccontextmanager
    async def track_agent_request(self, agent_type: str, request_id: str):
        """Context manager to track agent request performance"""
        start_time = time.time()
        
        with self._lock:
            self.metrics.concurrent_requests += 1
            self.metrics.total_requests += 1
            self.metrics.max_concurrent_requests = max(
                self.metrics.max_concurrent_requests,
                self.metrics.concurrent_requests
            )
            self._active_requests[request_id] = start_time
        
        try:
            yield
            
            # Request completed successfully
            end_time = time.time()
            response_time = end_time - start_time
            
            with self._lock:
                self.metrics.agent_response_times[agent_type].append(response_time)
                self.metrics.concurrent_requests -= 1
                self._active_requests.pop(request_id, None)
            
            # Check performance thresholds
            if response_time > self._alert_thresholds['agent_response_time']:
                await self._trigger_alert(
                    'agent_response_time_exceeded',
                    {
                        'agent_type': agent_type,
                        'request_id': request_id,
                        'response_time': response_time,
                        'threshold': self._alert_thresholds['agent_response_time']
                    }
                )
            
            logger.debug(f"Agent {agent_type} request {request_id} completed in {response_time:.2f}s")
            
        except Exception as e:
            # Request failed
            with self._lock:
                self.metrics.failed_requests += 1
                self.metrics.concurrent_requests -= 1
                self._active_requests.pop(request_id, None)
            
            logger.error(f"Agent {agent_type} request {request_id} failed: {e}")
            raise
    
    @asynccontextmanager
    async def track_workflow_execution(self, workflow_id: str):
        """Context manager to track workflow execution performance"""
        start_time = time.time()
        
        with self._lock:
            self._active_workflows[workflow_id] = start_time
        
        try:
            yield
            
            # Workflow completed successfully
            end_time = time.time()
            execution_time = end_time - start_time
            
            with self._lock:
                self.metrics.workflow_execution_times[workflow_id] = execution_time
                self._active_workflows.pop(workflow_id, None)
            
            # Check performance thresholds
            if execution_time > self._alert_thresholds['workflow_execution_time']:
                await self._trigger_alert(
                    'workflow_execution_time_exceeded',
                    {
                        'workflow_id': workflow_id,
                        'execution_time': execution_time,
                        'threshold': self._alert_thresholds['workflow_execution_time']
                    }
                )
            
            logger.info(f"Workflow {workflow_id} completed in {execution_time:.2f}s")
            
        except Exception as e:
            # Workflow failed
            with self._lock:
                self._active_workflows.pop(workflow_id, None)
            
            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise
    
    def record_downtime_event(self, duration_seconds: float, reason: str = "Unknown"):
        """Record a system downtime event"""
        with self._lock:
            self.metrics.availability_events.append({
                'type': 'downtime',
                'timestamp': datetime.now(),
                'duration': duration_seconds,
                'reason': reason
            })
        
        logger.warning(f"Downtime recorded: {duration_seconds}s - {reason}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self._lock:
            return {
                'agent_metrics': {
                    agent_type: {
                        'avg_response_time': self.metrics.get_agent_avg_response_time(agent_type),
                        'total_requests': len(times),
                        'max_response_time': max(times) if times else 0.0,
                        'min_response_time': min(times) if times else 0.0
                    }
                    for agent_type, times in self.metrics.agent_response_times.items()
                },
                'workflow_metrics': {
                    'completed_workflows': len(self.metrics.workflow_execution_times),
                    'avg_execution_time': (
                        sum(self.metrics.workflow_execution_times.values()) / 
                        len(self.metrics.workflow_execution_times)
                        if self.metrics.workflow_execution_times else 0.0
                    ),
                    'active_workflows': len(self._active_workflows)
                },
                'system_metrics': {
                    'uptime_seconds': self.metrics.get_system_uptime().total_seconds(),
                    'availability_percentage': self.metrics.get_availability_percentage(),
                    'concurrent_requests': self.metrics.concurrent_requests,
                    'max_concurrent_requests': self.metrics.max_concurrent_requests,
                    'total_requests': self.metrics.total_requests,
                    'failed_requests': self.metrics.failed_requests,
                    'success_rate': (
                        ((self.metrics.total_requests - self.metrics.failed_requests) / 
                         self.metrics.total_requests * 100)
                        if self.metrics.total_requests > 0 else 100.0
                    )
                },
                'performance_status': self._get_performance_status()
            }
    
    def _get_performance_status(self) -> Dict[str, bool]:
        """Check if performance requirements are being met"""
        status = {}
        
        # Check agent response time requirement (< 5 seconds)
        for agent_type, times in self.metrics.agent_response_times.items():
            if times:
                avg_time = sum(times) / len(times)
                status[f'{agent_type}_response_time_ok'] = avg_time < self._alert_thresholds['agent_response_time']
        
        # Check availability requirement (99.9%)
        availability = self.metrics.get_availability_percentage()
        status['availability_ok'] = availability >= self._alert_thresholds['availability_target']
        
        # Check concurrent request handling (50+ requests)
        status['concurrent_capacity_ok'] = (
            self.metrics.max_concurrent_requests >= self._alert_thresholds['max_concurrent_requests']
        )
        
        return status
    
    async def _trigger_alert(self, alert_type: str, details: Dict[str, Any]):
        """Trigger performance alert"""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now(),
            'details': details,
            'severity': self._get_alert_severity(alert_type, details)
        }
        
        logger.warning(f"Performance alert: {alert_type} - {details}")
        
        # In a production system, this would integrate with alerting systems
        # like CloudWatch Alarms, PagerDuty, etc.
    
    def _get_alert_severity(self, alert_type: str, details: Dict[str, Any]) -> str:
        """Determine alert severity based on type and details"""
        if alert_type == 'agent_response_time_exceeded':
            response_time = details.get('response_time', 0)
            if response_time > 10.0:  # 2x threshold
                return 'critical'
            elif response_time > 7.5:  # 1.5x threshold
                return 'high'
            else:
                return 'medium'
        
        elif alert_type == 'workflow_execution_time_exceeded':
            execution_time = details.get('execution_time', 0)
            if execution_time > 14400:  # 4 hours (2x threshold)
                return 'critical'
            elif execution_time > 10800:  # 3 hours (1.5x threshold)
                return 'high'
            else:
                return 'medium'
        
        return 'medium'
    
    def reset_metrics(self):
        """Reset all performance metrics (useful for testing)"""
        with self._lock:
            self.metrics = PerformanceMetrics()
            self._active_requests.clear()
            self._active_workflows.clear()
        
        logger.info("Performance metrics reset")
    
    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get formatted data for performance dashboard"""
        metrics = self.get_current_metrics()
        
        return {
            'summary': {
                'system_uptime': str(self.metrics.get_system_uptime()),
                'availability': f"{self.metrics.get_availability_percentage():.2f}%",
                'total_requests': self.metrics.total_requests,
                'success_rate': f"{metrics['system_metrics']['success_rate']:.2f}%",
                'concurrent_requests': self.metrics.concurrent_requests
            },
            'agent_performance': [
                {
                    'agent_type': agent_type,
                    'avg_response_time': f"{data['avg_response_time']:.2f}s",
                    'total_requests': data['total_requests'],
                    'status': 'OK' if data['avg_response_time'] < 5.0 else 'WARNING'
                }
                for agent_type, data in metrics['agent_metrics'].items()
            ],
            'workflow_performance': [
                {
                    'workflow_id': workflow_id,
                    'execution_time_seconds': execution_time,
                    'status': 'OK' if execution_time < 7200 else 'WARNING'
                }
                for workflow_id, execution_time in self.metrics.workflow_execution_times.items()
            ],
            'workflow_summary': {
                'completed_workflows': metrics['workflow_metrics']['completed_workflows'],
                'avg_execution_time': f"{metrics['workflow_metrics']['avg_execution_time']:.2f}s",
                'active_workflows': metrics['workflow_metrics']['active_workflows']
            },
            'alerts': self._get_recent_alerts(),
            'performance_requirements': {
                'agent_response_time': {
                    'requirement': '< 5 seconds',
                    'threshold': '5.0s',
                    'current_value': f"{max((data['avg_response_time'] for data in metrics['agent_metrics'].values()), default=0):.1f}s",
                    'status': all(
                        data['avg_response_time'] < 5.0 
                        for data in metrics['agent_metrics'].values()
                    ) if metrics['agent_metrics'] else True
                },
                'workflow_execution_time': {
                    'requirement': '< 2 hours',
                    'threshold': '2.0h',
                    'current_value': f"{max(self.metrics.workflow_execution_times.values(), default=0) / 3600:.1f}h",
                    'status': all(
                        time < 7200 
                        for time in self.metrics.workflow_execution_times.values()
                    ) if self.metrics.workflow_execution_times else True
                },
                'system_availability': {
                    'requirement': '99.9%',
                    'threshold': '99.9%',
                    'current_value': f"{self.metrics.get_availability_percentage():.1f}%",
                    'status': self.metrics.get_availability_percentage() >= 99.9
                },
                'concurrent_requests': {
                    'requirement': '50+ requests',
                    'threshold': '50',
                    'current_value': str(self.metrics.max_concurrent_requests),
                    'status': self.metrics.max_concurrent_requests >= 50
                }
            }
        }
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent performance alerts (placeholder for now)"""
        # In a real implementation, this would return recent alerts from storage
        return []


# Global performance monitor instance
performance_monitor = PerformanceMonitor()