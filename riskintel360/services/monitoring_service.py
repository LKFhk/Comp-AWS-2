"""
Comprehensive Monitoring and Observability Service
Provides CloudWatch dashboards, custom metrics, performance monitoring, and distributed tracing.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import boto3
from botocore.exceptions import ClientError

from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be tracked"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """Metric data structure"""
    name: str
    value: float
    unit: str
    dimensions: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    operation: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    response_time_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TraceSpan:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # "ok", "error", "timeout"


class MonitoringService:
    """Comprehensive monitoring and observability service"""
    
    def __init__(self):
        self.settings = get_settings()
        self._cloudwatch_client = None
        self._logs_client = None
        
        # Monitoring state
        self._metrics_buffer: List[MetricData] = []
        self._performance_metrics: List[PerformanceMetric] = []
        self._health_checks: Dict[str, HealthCheck] = {}
        self._active_traces: Dict[str, TraceSpan] = {}
        self._alert_handlers: List[Callable] = []
        
        # Performance tracking
        self._operation_stats: Dict[str, Dict[str, Any]] = {}
        
        # Initialize AWS clients
        self._initialize_clients()
        
        # Start background tasks
        self._monitoring_task = None
        self._start_background_monitoring()
    
    def _initialize_clients(self) -> None:
        """Initialize AWS clients for monitoring"""
        try:
            if self.settings.monitoring.cloudwatch_enabled:
                self._cloudwatch_client = boto3.client('cloudwatch')
                self._logs_client = boto3.client('logs')
                logger.info("CloudWatch clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring clients: {e}")
    
    def _start_background_monitoring(self) -> None:
        """Start background monitoring tasks"""
        if self._monitoring_task is None:
            try:
                # Only start background task if there's a running event loop
                loop = asyncio.get_running_loop()
                self._monitoring_task = asyncio.create_task(self._background_monitoring_loop())
            except RuntimeError:
                # No event loop running, skip background monitoring
                logger.debug("No event loop running, skipping background monitoring")
    
    async def _background_monitoring_loop(self) -> None:
        """Background loop for monitoring tasks"""
        while True:
            try:
                # Flush metrics buffer
                await self._flush_metrics_buffer()
                
                # Perform health checks
                await self._perform_health_checks()
                
                # Clean up old traces
                self._cleanup_old_traces()
                
                # Sleep for monitoring interval
                await asyncio.sleep(self.settings.monitoring.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short sleep on error
    
    # Metrics Management
    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.GAUGE
    ) -> None:
        """Record a custom metric"""
        metric = MetricData(
            name=name,
            value=value,
            unit=unit,
            dimensions=dimensions or {},
            timestamp=datetime.now(timezone.utc),
            metric_type=metric_type
        )
        
        self._metrics_buffer.append(metric)
        
        # Flush buffer if it gets too large
        if len(self._metrics_buffer) >= 20:
            asyncio.create_task(self._flush_metrics_buffer())
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric"""
        self.record_metric(
            name=name,
            value=value,
            unit="Count",
            dimensions=dimensions,
            metric_type=MetricType.COUNTER
        )
    
    def record_gauge(
        self,
        name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric"""
        self.record_metric(
            name=name,
            value=value,
            unit=unit,
            dimensions=dimensions,
            metric_type=MetricType.GAUGE
        )
    
    def record_timer(
        self,
        name: str,
        duration_ms: float,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer metric"""
        self.record_metric(
            name=name,
            value=duration_ms,
            unit="Milliseconds",
            dimensions=dimensions,
            metric_type=MetricType.TIMER
        )
    
    async def _flush_metrics_buffer(self) -> None:
        """Flush metrics buffer to CloudWatch"""
        if not self._metrics_buffer or not self._cloudwatch_client:
            return
        
        try:
            # Prepare metric data for CloudWatch
            metric_data = []
            
            for metric in self._metrics_buffer:
                dimensions = [
                    {'Name': k, 'Value': v} 
                    for k, v in metric.dimensions.items()
                ]
                
                metric_data.append({
                    'MetricName': metric.name,
                    'Dimensions': dimensions,
                    'Value': metric.value,
                    'Unit': metric.unit,
                    'Timestamp': metric.timestamp
                })
            
            # Send metrics to CloudWatch in batches
            batch_size = 20
            for i in range(0, len(metric_data), batch_size):
                batch = metric_data[i:i + batch_size]
                
                self._cloudwatch_client.put_metric_data(
                    Namespace=self.settings.monitoring.cloudwatch_namespace,
                    MetricData=batch
                )
            
            logger.debug(f"Flushed {len(self._metrics_buffer)} metrics to CloudWatch")
            self._metrics_buffer.clear()
            
        except ClientError as e:
            logger.error(f"Failed to flush metrics to CloudWatch: {e}")
        except Exception as e:
            logger.error(f"Unexpected error flushing metrics: {e}")
    
    # Performance Monitoring
    def start_performance_timer(self, operation: str) -> str:
        """Start a performance timer and return timer ID"""
        timer_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Store timer start time
        if operation not in self._operation_stats:
            self._operation_stats[operation] = {
                'active_timers': {},
                'total_calls': 0,
                'total_duration_ms': 0,
                'success_count': 0,
                'error_count': 0,
                'avg_duration_ms': 0
            }
        
        self._operation_stats[operation]['active_timers'][timer_id] = start_time
        return timer_id
    
    def end_performance_timer(
        self,
        timer_id: str,
        operation: str,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """End a performance timer and record the metric"""
        if operation not in self._operation_stats:
            logger.warning(f"No operation stats found for: {operation}")
            return 0.0
        
        active_timers = self._operation_stats[operation]['active_timers']
        if timer_id not in active_timers:
            logger.warning(f"Timer ID {timer_id} not found for operation: {operation}")
            return 0.0
        
        # Calculate duration
        start_time = active_timers.pop(timer_id)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Update operation stats
        stats = self._operation_stats[operation]
        stats['total_calls'] += 1
        stats['total_duration_ms'] += duration_ms
        
        if success:
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1
        
        stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['total_calls']
        
        # Record performance metric
        perf_metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        self._performance_metrics.append(perf_metric)
        
        # Record CloudWatch metrics
        dimensions = {
            'Operation': operation,
            'Success': str(success)
        }
        
        self.record_timer(
            name="OperationDuration",
            duration_ms=duration_ms,
            dimensions=dimensions
        )
        
        self.increment_counter(
            name="OperationCount",
            dimensions=dimensions
        )
        
        if not success:
            self.increment_counter(
                name="OperationErrors",
                dimensions={'Operation': operation}
            )
        
        return duration_ms
    
    def get_performance_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if operation:
            return self._operation_stats.get(operation, {})
        return self._operation_stats.copy()
    
    # Health Monitoring
    async def register_health_check(
        self,
        component: str,
        check_function: Callable[[], bool],
        timeout_seconds: int = 5
    ) -> None:
        """Register a health check for a component"""
        try:
            start_time = time.time()
            
            # Run health check with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.create_task(self._run_health_check(check_function)),
                    timeout=timeout_seconds
                )
                status = "healthy" if result else "unhealthy"
                message = "Health check passed" if result else "Health check failed"
            except asyncio.TimeoutError:
                status = "unhealthy"
                message = f"Health check timed out after {timeout_seconds}s"
                result = False
            except Exception as e:
                status = "unhealthy"
                message = f"Health check error: {str(e)}"
                result = False
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Store health check result
            health_check = HealthCheck(
                component=component,
                status=status,
                message=message,
                response_time_ms=response_time_ms
            )
            
            self._health_checks[component] = health_check
            
            # Record metrics
            self.record_gauge(
                name="HealthCheck",
                value=1.0 if result else 0.0,
                dimensions={'Component': component}
            )
            
            self.record_timer(
                name="HealthCheckDuration",
                duration_ms=response_time_ms,
                dimensions={'Component': component}
            )
            
        except Exception as e:
            logger.error(f"Error in health check for {component}: {e}")
    
    async def _run_health_check(self, check_function: Callable[[], bool]) -> bool:
        """Run a health check function"""
        if asyncio.iscoroutinefunction(check_function):
            return await check_function()
        else:
            return check_function()
    
    async def _perform_health_checks(self) -> None:
        """Perform all registered health checks"""
        # This would be called by the background monitoring loop
        # For now, we'll just record system health metrics
        
        # Record system metrics
        self.record_gauge(
            name="SystemHealth",
            value=1.0,  # Assume healthy for now
            dimensions={'System': 'RiskIntel360'}
        )
        
        # Record active traces count
        self.record_gauge(
            name="ActiveTraces",
            value=len(self._active_traces),
            dimensions={'System': 'RiskIntel360'}
        )
        
        # Record metrics buffer size
        self.record_gauge(
            name="MetricsBufferSize",
            value=len(self._metrics_buffer),
            dimensions={'System': 'RiskIntel360'}
        )
    
    def get_health_status(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get health status for components"""
        if component:
            health_check = self._health_checks.get(component)
            if health_check:
                return {
                    'component': health_check.component,
                    'status': health_check.status,
                    'message': health_check.message,
                    'response_time_ms': health_check.response_time_ms,
                    'timestamp': health_check.timestamp.isoformat()
                }
            return {'error': f'No health check found for component: {component}'}
        
        return {
            component: {
                'status': hc.status,
                'message': hc.message,
                'response_time_ms': hc.response_time_ms,
                'timestamp': hc.timestamp.isoformat()
            }
            for component, hc in self._health_checks.items()
        }
    
    # Distributed Tracing
    def start_trace(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Start a new trace span"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(timezone.utc),
            tags=tags or {}
        )
        
        self._active_traces[span_id] = span
        
        # Record trace start metric
        self.increment_counter(
            name="TraceStarted",
            dimensions={
                'Operation': operation_name,
                'HasParent': str(parent_span_id is not None)
            }
        )
        
        return span_id
    
    def end_trace(
        self,
        span_id: str,
        status: str = "ok",
        error_message: Optional[str] = None
    ) -> Optional[TraceSpan]:
        """End a trace span"""
        if span_id not in self._active_traces:
            logger.warning(f"Trace span {span_id} not found")
            return None
        
        span = self._active_traces.pop(span_id)
        span.end_time = datetime.now(timezone.utc)
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        
        if error_message:
            span.logs.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'level': 'error',
                'message': error_message
            })
        
        # Record trace completion metrics
        self.increment_counter(
            name="TraceCompleted",
            dimensions={
                'Operation': span.operation_name,
                'Status': status
            }
        )
        
        self.record_timer(
            name="TraceDuration",
            duration_ms=span.duration_ms,
            dimensions={
                'Operation': span.operation_name,
                'Status': status
            }
        )
        
        return span
    
    def add_trace_log(
        self,
        span_id: str,
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a log entry to a trace span"""
        if span_id in self._active_traces:
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'level': level,
                'message': message
            }
            
            if metadata:
                log_entry['metadata'] = metadata
            
            self._active_traces[span_id].logs.append(log_entry)
    
    def get_trace(self, span_id: str) -> Optional[Dict[str, Any]]:
        """Get trace information"""
        if span_id in self._active_traces:
            span = self._active_traces[span_id]
            return {
                'trace_id': span.trace_id,
                'span_id': span.span_id,
                'parent_span_id': span.parent_span_id,
                'operation_name': span.operation_name,
                'start_time': span.start_time.isoformat(),
                'end_time': span.end_time.isoformat() if span.end_time else None,
                'duration_ms': span.duration_ms,
                'tags': span.tags,
                'logs': span.logs,
                'status': span.status
            }
        return None
    
    def _cleanup_old_traces(self) -> None:
        """Clean up old trace spans"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        spans_to_remove = []
        for span_id, span in self._active_traces.items():
            if span.start_time < cutoff_time:
                spans_to_remove.append(span_id)
        
        for span_id in spans_to_remove:
            self._active_traces.pop(span_id, None)
        
        if spans_to_remove:
            logger.debug(f"Cleaned up {len(spans_to_remove)} old trace spans")
    
    # Alert Management
    def add_alert_handler(self, handler: Callable) -> None:
        """Add an alert handler function"""
        self._alert_handlers.append(handler)
    
    async def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create and send an alert"""
        alert_id = str(uuid.uuid4())
        
        alert_data = {
            'id': alert_id,
            'title': title,
            'message': message,
            'severity': severity.value,
            'component': component,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }
        
        # Record alert metric
        self.increment_counter(
            name="AlertsCreated",
            dimensions={
                'Severity': severity.value,
                'Component': component or 'Unknown'
            }
        )
        
        # Call alert handlers
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert_data)
                else:
                    handler(alert_data)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        return alert_id
    
    # Dashboard and Reporting
    async def create_cloudwatch_dashboard(self) -> bool:
        """Create CloudWatch dashboard for the platform"""
        if not self._cloudwatch_client:
            logger.warning("CloudWatch client not available")
            return False
        
        try:
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.settings.monitoring.cloudwatch_namespace, "OperationCount"],
                                [self.settings.monitoring.cloudwatch_namespace, "OperationErrors"],
                                [self.settings.monitoring.cloudwatch_namespace, "OperationDuration"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": "us-east-1",
                            "title": "Agent Performance Metrics"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 6,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.settings.monitoring.cloudwatch_namespace, "HealthCheck"],
                                [self.settings.monitoring.cloudwatch_namespace, "SystemHealth"],
                                [self.settings.monitoring.cloudwatch_namespace, "ActiveTraces"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": "us-east-1",
                            "title": "System Health Metrics"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 12,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.settings.monitoring.cloudwatch_namespace, "AlertsCreated"],
                                [self.settings.monitoring.cloudwatch_namespace, "TraceStarted"],
                                [self.settings.monitoring.cloudwatch_namespace, "TraceCompleted"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": "us-east-1",
                            "title": "Monitoring Activity"
                        }
                    }
                ]
            }
            
            self._cloudwatch_client.put_dashboard(
                DashboardName="RiskIntel360-Platform-Dashboard",
                DashboardBody=json.dumps(dashboard_body)
            )
            
            logger.info("CloudWatch dashboard created successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create CloudWatch dashboard: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating dashboard: {e}")
            return False
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        return {
            'metrics': {
                'buffer_size': len(self._metrics_buffer),
                'performance_metrics': len(self._performance_metrics),
                'operation_stats': len(self._operation_stats)
            },
            'health': {
                'components_monitored': len(self._health_checks),
                'healthy_components': sum(
                    1 for hc in self._health_checks.values() 
                    if hc.status == "healthy"
                )
            },
            'tracing': {
                'active_traces': len(self._active_traces),
                'total_operations': len(self._operation_stats)
            },
            'alerts': {
                'handlers_registered': len(self._alert_handlers)
            },
            'cloudwatch': {
                'enabled': self.settings.monitoring.cloudwatch_enabled,
                'namespace': self.settings.monitoring.cloudwatch_namespace
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown monitoring service"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining metrics
        await self._flush_metrics_buffer()
        
        logger.info("Monitoring service shutdown complete")


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


# Decorator for performance monitoring
def monitor_performance(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                monitoring = get_monitoring_service()
                timer_id = monitoring.start_performance_timer(operation_name)
                
                try:
                    result = await func(*args, **kwargs)
                    monitoring.end_performance_timer(timer_id, operation_name, success=True)
                    return result
                except Exception as e:
                    monitoring.end_performance_timer(
                        timer_id, operation_name, success=False, error_message=str(e)
                    )
                    raise
            
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                monitoring = get_monitoring_service()
                timer_id = monitoring.start_performance_timer(operation_name)
                
                try:
                    result = func(*args, **kwargs)
                    monitoring.end_performance_timer(timer_id, operation_name, success=True)
                    return result
                except Exception as e:
                    monitoring.end_performance_timer(
                        timer_id, operation_name, success=False, error_message=str(e)
                    )
                    raise
            
            return sync_wrapper
    
    return decorator


# Context manager for distributed tracing
class TraceContext:
    """Context manager for distributed tracing"""
    
    def __init__(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        self.operation_name = operation_name
        self.parent_span_id = parent_span_id
        self.tags = tags
        self.span_id: Optional[str] = None
        self.monitoring = get_monitoring_service()
    
    def __enter__(self) -> str:
        self.span_id = self.monitoring.start_trace(
            self.operation_name,
            self.parent_span_id,
            self.tags
        )
        return self.span_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span_id:
            status = "error" if exc_type else "ok"
            error_message = str(exc_val) if exc_val else None
            self.monitoring.end_trace(self.span_id, status, error_message)
    
    async def __aenter__(self) -> str:
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)
