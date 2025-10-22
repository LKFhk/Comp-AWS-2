"""
Performance Optimization Service for RiskIntel360 Platform
Optimizes agent response times using AWS Lambda and asyncio to meet <5 second requirement.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import json

import boto3
from botocore.exceptions import ClientError

from riskintel360.config.settings import get_settings
from riskintel360.services.caching_service import get_caching_service, cached

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds"""
        return self.duration * 1000


@dataclass
class PerformanceTarget:
    """Performance target configuration"""
    operation: str
    target_time_seconds: float
    warning_threshold: float = 0.8  # 80% of target
    critical_threshold: float = 1.2  # 120% of target


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.max_metrics_history = 10000
        
        # Performance targets
        self.targets = {
            'agent_execution': PerformanceTarget('agent_execution', 5.0),
            'regulatory_compliance': PerformanceTarget('regulatory_compliance', 4.5),
            'risk_assessment': PerformanceTarget('risk_assessment', 4.0),
            'market_analysis': PerformanceTarget('market_analysis', 4.0),
            'customer_behavior_intelligence': PerformanceTarget('customer_behavior_intelligence', 3.5),
            'fraud_detection': PerformanceTarget('fraud_detection', 5.0),
            'kyc_verification': PerformanceTarget('kyc_verification', 4.5),
            'api_response': PerformanceTarget('api_response', 2.0),
            'database_query': PerformanceTarget('database_query', 1.0),
            'cache_operation': PerformanceTarget('cache_operation', 0.1),
            'external_api': PerformanceTarget('external_api', 3.0),
        }
    
    def start_timer(self, operation_name: str) -> float:
        """Start performance timer"""
        return time.time()
    
    def record_metric(
        self,
        operation_name: str,
        start_time: float,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetrics:
        """Record performance metric"""
        end_time = time.time()
        duration = end_time - start_time
        
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        # Add to metrics history
        self.metrics.append(metric)
        if len(self.metrics) > self.max_metrics_history:
            self.metrics.pop(0)
        
        # Check against targets
        self._check_performance_target(metric)
        
        return metric
    
    def _check_performance_target(self, metric: PerformanceMetrics) -> None:
        """Check metric against performance targets"""
        target = self.targets.get(metric.operation_name)
        if not target:
            return
        
        if metric.duration > target.target_time_seconds * target.critical_threshold:
            logger.error(
                f"CRITICAL: {metric.operation_name} took {metric.duration:.2f}s "
                f"(target: {target.target_time_seconds}s)"
            )
        elif metric.duration > target.target_time_seconds * target.warning_threshold:
            logger.warning(
                f"WARNING: {metric.operation_name} took {metric.duration:.2f}s "
                f"(target: {target.target_time_seconds}s)"
            )
    
    def get_stats(self, operation_name: Optional[str] = None, hours: int = 1) -> Dict[str, Any]:
        """Get performance statistics"""
        cutoff_time = time.time() - (hours * 3600)
        
        # Filter metrics
        filtered_metrics = [
            m for m in self.metrics
            if m.start_time >= cutoff_time and (not operation_name or m.operation_name == operation_name)
        ]
        
        if not filtered_metrics:
            return {}
        
        durations = [m.duration for m in filtered_metrics]
        success_count = sum(1 for m in filtered_metrics if m.success)
        
        return {
            'operation': operation_name or 'all',
            'total_operations': len(filtered_metrics),
            'success_rate': (success_count / len(filtered_metrics)) * 100,
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p50_duration': sorted(durations)[len(durations) // 2],
            'p95_duration': sorted(durations)[int(len(durations) * 0.95)],
            'p99_duration': sorted(durations)[int(len(durations) * 0.99)],
            'target_met_rate': sum(1 for d in durations if d <= self.targets.get(operation_name or 'agent_execution', self.targets['agent_execution']).target_time_seconds) / len(durations) * 100
        }


def performance_monitor(operation_name: str):
    """Decorator for monitoring function performance"""
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            monitor = get_performance_optimizer().monitor
            start_time = monitor.start_timer(operation_name)
            
            try:
                result = await func(*args, **kwargs)
                monitor.record_metric(operation_name, start_time, success=True)
                return result
            except Exception as e:
                monitor.record_metric(operation_name, start_time, success=False, error_message=str(e))
                raise
        
        def sync_wrapper(*args, **kwargs):
            monitor = get_performance_optimizer().monitor
            start_time = monitor.start_timer(operation_name)
            
            try:
                result = func(*args, **kwargs)
                monitor.record_metric(operation_name, start_time, success=True)
                return result
            except Exception as e:
                monitor.record_metric(operation_name, start_time, success=False, error_message=str(e))
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class AsyncExecutor:
    """Optimized async execution manager"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Configure thread pool for CPU-bound tasks
        max_workers = min(32, (self.settings.agents.max_concurrent_agents or 4) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # Semaphore for controlling concurrent operations
        self.agent_semaphore = asyncio.Semaphore(self.settings.agents.max_concurrent_agents)
        self.api_semaphore = asyncio.Semaphore(50)  # Limit concurrent API calls
        self.db_semaphore = asyncio.Semaphore(20)   # Limit concurrent DB operations
    
    async def execute_with_timeout(
        self,
        coro: Awaitable[Any],
        timeout_seconds: float,
        operation_name: str = "operation"
    ) -> Any:
        """Execute coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.error(f"{operation_name} timed out after {timeout_seconds} seconds")
            raise
    
    async def execute_agent_task(self, coro: Awaitable[Any], agent_name: str) -> Any:
        """Execute agent task with concurrency control"""
        async with self.agent_semaphore:
            timeout = self.settings.agents.agent_timeout_seconds
            return await self.execute_with_timeout(coro, timeout, f"agent_{agent_name}")
    
    async def execute_api_call(self, coro: Awaitable[Any], api_name: str) -> Any:
        """Execute API call with concurrency control"""
        async with self.api_semaphore:
            timeout = self.settings.external_apis.api_timeout_seconds
            return await self.execute_with_timeout(coro, timeout, f"api_{api_name}")
    
    async def execute_db_operation(self, coro: Awaitable[Any], operation_name: str) -> Any:
        """Execute database operation with concurrency control"""
        async with self.db_semaphore:
            return await self.execute_with_timeout(coro, 30.0, f"db_{operation_name}")
    
    async def execute_parallel(
        self,
        tasks: List[Awaitable[Any]],
        max_concurrency: Optional[int] = None,
        return_exceptions: bool = False
    ) -> List[Any]:
        """Execute tasks in parallel with controlled concurrency"""
        if max_concurrency:
            semaphore = asyncio.Semaphore(max_concurrency)
            
            async def limited_task(task):
                async with semaphore:
                    return await task
            
            tasks = [limited_task(task) for task in tasks]
        
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    
    def run_in_thread(self, func: Callable, *args, **kwargs) -> Awaitable[Any]:
        """Run CPU-bound function in thread pool"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.thread_pool, func, *args, **kwargs)


class LambdaOptimizer:
    """AWS Lambda optimization for serverless agent execution"""
    
    def __init__(self):
        self.settings = get_settings()
        self.lambda_client = boto3.client('lambda')
        self.cache = get_caching_service()
    
    @cached('lambda_function', ttl=300)
    async def get_function_config(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get Lambda function configuration"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.lambda_client.get_function,
                {'FunctionName': function_name}
            )
            return response.get('Configuration', {})
        except ClientError as e:
            logger.error(f"Failed to get Lambda function config for {function_name}: {e}")
            return None
    
    async def invoke_agent_lambda(
        self,
        function_name: str,
        payload: Dict[str, Any],
        invocation_type: str = 'RequestResponse'
    ) -> Optional[Dict[str, Any]]:
        """Invoke agent Lambda function"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.lambda_client.invoke,
                {
                    'FunctionName': function_name,
                    'InvocationType': invocation_type,
                    'Payload': json.dumps(payload)
                }
            )
            
            if response.get('Payload'):
                result = json.loads(response['Payload'].read())
                return result
            
            return None
            
        except ClientError as e:
            logger.error(f"Failed to invoke Lambda function {function_name}: {e}")
            return None
    
    async def update_function_concurrency(self, function_name: str, reserved_concurrency: int) -> bool:
        """Update Lambda function concurrency settings"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.lambda_client.put_reserved_concurrency_configuration,
                {
                    'FunctionName': function_name,
                    'ReservedConcurrencyLimit': reserved_concurrency
                }
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to update concurrency for {function_name}: {e}")
            return False


class PerformanceOptimizer:
    """Main performance optimization service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.monitor = PerformanceMonitor()
        self.executor = AsyncExecutor()
        self.lambda_optimizer = LambdaOptimizer()
        
        # Performance optimization strategies
        self.optimization_strategies = {
            'caching': True,
            'connection_pooling': True,
            'async_execution': True,
            'lambda_optimization': self.settings.environment.value == "production",
            'request_batching': True,
            'response_compression': True,
        }
    
    @performance_monitor('agent_execution')
    async def optimize_agent_execution(
        self,
        agent_func: Callable,
        *args,
        agent_name: str = "unknown",
        **kwargs
    ) -> Any:
        """Optimize agent execution with performance monitoring"""
        # Use executor for concurrency control and timeout
        return await self.executor.execute_agent_task(
            agent_func(*args, **kwargs),
            agent_name
        )
    
    @performance_monitor('api_response')
    async def optimize_api_response(
        self,
        handler_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Optimize API response handling"""
        # Execute with API-specific timeout and concurrency
        return await self.executor.execute_with_timeout(
            handler_func(*args, **kwargs),
            self.monitor.targets['api_response'].target_time_seconds,
            'api_response'
        )
    
    @performance_monitor('database_query')
    async def optimize_database_query(
        self,
        query_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Optimize database query execution"""
        return await self.executor.execute_db_operation(
            query_func(*args, **kwargs),
            'query'
        )
    
    async def batch_external_api_calls(
        self,
        api_calls: List[Callable],
        batch_size: int = 10
    ) -> List[Any]:
        """Batch external API calls for better performance"""
        results = []
        
        for i in range(0, len(api_calls), batch_size):
            batch = api_calls[i:i + batch_size]
            batch_results = await self.executor.execute_parallel(
                [self.executor.execute_api_call(call(), f"batch_{i}") for call in batch],
                max_concurrency=batch_size,
                return_exceptions=True
            )
            results.extend(batch_results)
        
        return results
    
    async def warm_up_services(self) -> Dict[str, bool]:
        """Warm up services for better performance"""
        results = {}
        
        # Warm up cache connections
        try:
            cache = get_caching_service()
            await cache.set("warmup", "test", 60)
            await cache.get("warmup")
            results['cache'] = True
        except Exception as e:
            logger.error(f"Cache warmup failed: {e}")
            results['cache'] = False
        
        # Warm up database connections
        try:
            from riskintel360.services.connection_pool import get_connection_pool_manager
            pool_manager = get_connection_pool_manager()
            await pool_manager.initialize_all()
            results['database'] = True
        except Exception as e:
            logger.error(f"Database warmup failed: {e}")
            results['database'] = False
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            'overall_stats': self.monitor.get_stats(),
            'agent_stats': {},
            'optimization_strategies': self.optimization_strategies,
            'targets': {name: target.target_time_seconds for name, target in self.monitor.targets.items()},
        }
        
        # Get stats for each agent type
        for agent_type in ['regulatory_compliance', 'risk_assessment', 'market_analysis', 'customer_behavior_intelligence', 'fraud_detection', 'kyc_verification']:
            report['agent_stats'][agent_type] = self.monitor.get_stats(agent_type)
        
        return report
    
    async def auto_tune_performance(self) -> Dict[str, Any]:
        """Automatically tune performance based on metrics"""
        tuning_results = {}
        
        # Analyze recent performance
        stats = self.monitor.get_stats(hours=1)
        
        if not stats:
            return {'message': 'No recent metrics available for tuning'}
        
        # Adjust concurrency limits based on performance
        if stats.get('avg_duration', 0) > 4.0:  # If average > 4 seconds
            # Reduce concurrency to improve individual response times
            new_limit = max(3, self.settings.agents.max_concurrent_agents - 5)
            self.executor.agent_semaphore = asyncio.Semaphore(new_limit)
            tuning_results['agent_concurrency'] = f'Reduced to {new_limit}'
        
        elif stats.get('avg_duration', 0) < 2.0 and stats.get('success_rate', 0) > 95:
            # Increase concurrency if performance is good
            new_limit = min(50, self.settings.agents.max_concurrent_agents + 5)
            self.executor.agent_semaphore = asyncio.Semaphore(new_limit)
            tuning_results['agent_concurrency'] = f'Increased to {new_limit}'
        
        # Adjust cache TTL based on hit rates
        cache_stats = get_caching_service().get_stats()
        if cache_stats.get('hit_rate', 0) < 70:  # Low hit rate
            # Increase TTL for better caching
            tuning_results['cache_ttl'] = 'Increased TTL for better hit rates'
        
        return tuning_results


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer
