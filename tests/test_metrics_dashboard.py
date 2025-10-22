"""
Test Metrics Dashboard

Provides comprehensive test metrics collection, analysis, and reporting
for the RiskIntel360 platform testing framework.
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from jinja2 import Template

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class MetricType(Enum):
    """Types of test metrics"""
    COVERAGE = "coverage"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SECURITY = "security"
    RELIABILITY = "reliability"


@dataclass
class ExecutionMetric:
    """Individual test metric"""
    name: str
    value: float
    unit: str
    metric_type: MetricType
    timestamp: datetime
    test_suite: str
    environment: str
    metadata: Dict[str, Any] = None


@dataclass
class ExecutionRecord:
    """Test execution record"""
    execution_id: str
    test_suite: str
    environment: str
    start_time: datetime
    end_time: Optional[datetime]
    status: ExecutionStatus
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    coverage_percentage: float
    duration_seconds: float
    error_message: Optional[str] = None
    metrics: List[ExecutionMetric] = None


@dataclass
class QualityGate:
    """Quality gate definition and status"""
    name: str
    threshold: float
    current_value: float
    status: str  # passed, failed, warning
    blocking: bool
    description: str
    trend: str = "stable"  # improving, degrading, stable


class MetricsCollector:
    """Collects and stores test metrics"""
    
    def __init__(self, db_path: str = "test_metrics.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Test executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_executions (
                execution_id TEXT PRIMARY KEY,
                test_suite TEXT NOT NULL,
                environment TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL,
                total_tests INTEGER,
                passed_tests INTEGER,
                failed_tests INTEGER,
                skipped_tests INTEGER,
                coverage_percentage REAL,
                duration_seconds REAL,
                error_message TEXT
            )
        """)
        
        # Test metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                metric_type TEXT,
                timestamp TEXT NOT NULL,
                test_suite TEXT,
                environment TEXT,
                metadata TEXT,
                FOREIGN KEY (execution_id) REFERENCES test_executions (execution_id)
            )
        """)
        
        # Quality gates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT,
                name TEXT NOT NULL,
                threshold REAL NOT NULL,
                current_value REAL NOT NULL,
                status TEXT NOT NULL,
                blocking BOOLEAN,
                description TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (execution_id) REFERENCES test_executions (execution_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_test_execution(self, execution: ExecutionRecord) -> str:
        """Record a test execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO test_executions 
            (execution_id, test_suite, environment, start_time, end_time, status,
             total_tests, passed_tests, failed_tests, skipped_tests,
             coverage_percentage, duration_seconds, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution.execution_id,
            execution.test_suite,
            execution.environment,
            execution.start_time.isoformat(),
            execution.end_time.isoformat() if execution.end_time else None,
            execution.status.value,
            execution.total_tests,
            execution.passed_tests,
            execution.failed_tests,
            execution.skipped_tests,
            execution.coverage_percentage,
            execution.duration_seconds,
            execution.error_message
        ))
        
        # Record metrics
        if execution.metrics:
            for metric in execution.metrics:
                cursor.execute("""
                    INSERT INTO test_metrics 
                    (execution_id, name, value, unit, metric_type, timestamp,
                     test_suite, environment, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    metric.name,
                    metric.value,
                    metric.unit,
                    metric.metric_type.value,
                    metric.timestamp.isoformat(),
                    metric.test_suite,
                    metric.environment,
                    json.dumps(metric.metadata) if metric.metadata else None
                ))
        
        conn.commit()
        conn.close()
        
        return execution.execution_id
    
    def record_quality_gate(self, execution_id: str, gate: QualityGate):
        """Record quality gate result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quality_gates 
            (execution_id, name, threshold, current_value, status, blocking, description, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            gate.name,
            gate.threshold,
            gate.current_value,
            gate.status,
            gate.blocking,
            gate.description,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_executions(self, days: int = 30) -> List[ExecutionRecord]:
        """Get recent test executions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT * FROM test_executions 
            WHERE start_time >= ? 
            ORDER BY start_time DESC
        """, (since_date,))
        
        executions = []
        for row in cursor.fetchall():
            execution = ExecutionRecord(
                execution_id=row[0],
                test_suite=row[1],
                environment=row[2],
                start_time=datetime.fromisoformat(row[3]),
                end_time=datetime.fromisoformat(row[4]) if row[4] else None,
                status=ExecutionStatus(row[5]),
                total_tests=row[6],
                passed_tests=row[7],
                failed_tests=row[8],
                skipped_tests=row[9],
                coverage_percentage=row[10],
                duration_seconds=row[11],
                error_message=row[12]
            )
            executions.append(execution)
        
        conn.close()
        return executions
    
    def get_metrics_by_type(self, metric_type: MetricType, days: int = 30) -> List[ExecutionMetric]:
        """Get metrics by type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT name, value, unit, metric_type, timestamp, test_suite, environment, metadata
            FROM test_metrics 
            WHERE metric_type = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (metric_type.value, since_date))
        
        metrics = []
        for row in cursor.fetchall():
            metric = ExecutionMetric(
                name=row[0],
                value=row[1],
                unit=row[2],
                metric_type=MetricType(row[3]),
                timestamp=datetime.fromisoformat(row[4]),
                test_suite=row[5],
                environment=row[6],
                metadata=json.loads(row[7]) if row[7] else None
            )
            metrics.append(metric)
        
        conn.close()
        return metrics


class MetricsDashboard:
    """Generates test metrics dashboard and reports"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.output_dir = Path("test-reports")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_dashboard(self, days: int = 30) -> str:
        """Generate comprehensive test metrics dashboard"""
        logger.info(f"Generating test metrics dashboard for last {days} days...")
        
        # Collect data
        executions = self.collector.get_recent_executions(days)
        coverage_metrics = self.collector.get_metrics_by_type(MetricType.COVERAGE, days)
        performance_metrics = self.collector.get_metrics_by_type(MetricType.PERFORMANCE, days)
        
        # Generate visualizations
        self._generate_test_trend_chart(executions)
        self._generate_coverage_trend_chart(coverage_metrics)
        self._generate_performance_trend_chart(performance_metrics)
        self._generate_test_suite_comparison(executions)
        
        # Generate HTML dashboard
        dashboard_html = self._generate_html_dashboard(executions, coverage_metrics, performance_metrics)
        
        # Save dashboard
        dashboard_path = self.output_dir / "test_metrics_dashboard.html"
        with open(dashboard_path, 'w') as f:
            f.write(dashboard_html)
        
        logger.info(f"Dashboard generated: {dashboard_path}")
        return str(dashboard_path)
    
    def _generate_test_trend_chart(self, executions: List[ExecutionRecord]):
        """Generate test execution trend chart"""
        if not executions:
            return
        
        # Prepare data
        df = pd.DataFrame([
            {
                'date': exec.start_time.date(),
                'test_suite': exec.test_suite,
                'success_rate': (exec.passed_tests / exec.total_tests * 100) if exec.total_tests > 0 else 0,
                'duration': exec.duration_seconds / 60,  # Convert to minutes
                'coverage': exec.coverage_percentage
            }
            for exec in executions
        ])
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Test Execution Trends', fontsize=16)
        
        # Success rate trend
        success_by_date = df.groupby('date')['success_rate'].mean()
        axes[0, 0].plot(success_by_date.index, success_by_date.values, marker='o')
        axes[0, 0].set_title('Test Success Rate Trend')
        axes[0, 0].set_ylabel('Success Rate (%)')
        axes[0, 0].grid(True)
        
        # Duration trend
        duration_by_date = df.groupby('date')['duration'].mean()
        axes[0, 1].plot(duration_by_date.index, duration_by_date.values, marker='o', color='orange')
        axes[0, 1].set_title('Test Duration Trend')
        axes[0, 1].set_ylabel('Duration (minutes)')
        axes[0, 1].grid(True)
        
        # Coverage trend
        coverage_by_date = df.groupby('date')['coverage'].mean()
        axes[1, 0].plot(coverage_by_date.index, coverage_by_date.values, marker='o', color='green')
        axes[1, 0].set_title('Test Coverage Trend')
        axes[1, 0].set_ylabel('Coverage (%)')
        axes[1, 0].grid(True)
        
        # Test suite comparison
        suite_success = df.groupby('test_suite')['success_rate'].mean()
        axes[1, 1].bar(suite_success.index, suite_success.values)
        axes[1, 1].set_title('Success Rate by Test Suite')
        axes[1, 1].set_ylabel('Success Rate (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'test_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_coverage_trend_chart(self, metrics: List[ExecutionMetric]):
        """Generate coverage trend chart"""
        if not metrics:
            return
        
        df = pd.DataFrame([
            {
                'date': metric.timestamp.date(),
                'test_suite': metric.test_suite,
                'coverage': metric.value
            }
            for metric in metrics if metric.name == 'coverage_percentage'
        ])
        
        if df.empty:
            return
        
        plt.figure(figsize=(12, 6))
        
        # Plot coverage by test suite
        for suite in df['test_suite'].unique():
            suite_data = df[df['test_suite'] == suite]
            plt.plot(suite_data['date'], suite_data['coverage'], 
                    marker='o', label=suite, linewidth=2)
        
        plt.title('Test Coverage Trends by Suite', fontsize=14)
        plt.xlabel('Date')
        plt.ylabel('Coverage (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Add threshold line
        plt.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='Minimum Threshold (90%)')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'coverage_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_performance_trend_chart(self, metrics: List[ExecutionMetric]):
        """Generate performance trend chart"""
        if not metrics:
            return
        
        df = pd.DataFrame([
            {
                'date': metric.timestamp.date(),
                'test_suite': metric.test_suite,
                'metric_name': metric.name,
                'value': metric.value,
                'unit': metric.unit
            }
            for metric in metrics
        ])
        
        if df.empty:
            return
        
        # Group by metric type
        response_time_metrics = df[df['metric_name'].str.contains('response_time|duration')]
        throughput_metrics = df[df['metric_name'].str.contains('throughput|requests')]
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # Response time trends
        if not response_time_metrics.empty:
            for suite in response_time_metrics['test_suite'].unique():
                suite_data = response_time_metrics[response_time_metrics['test_suite'] == suite]
                avg_by_date = suite_data.groupby('date')['value'].mean()
                axes[0].plot(avg_by_date.index, avg_by_date.values, 
                           marker='o', label=suite)
            
            axes[0].set_title('Response Time Trends')
            axes[0].set_ylabel('Response Time (seconds)')
            axes[0].legend()
            axes[0].grid(True)
        
        # Throughput trends
        if not throughput_metrics.empty:
            for suite in throughput_metrics['test_suite'].unique():
                suite_data = throughput_metrics[throughput_metrics['test_suite'] == suite]
                avg_by_date = suite_data.groupby('date')['value'].mean()
                axes[1].plot(avg_by_date.index, avg_by_date.values, 
                           marker='o', label=suite)
            
            axes[1].set_title('Throughput Trends')
            axes[1].set_ylabel('Requests/Second')
            axes[1].legend()
            axes[1].grid(True)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'performance_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_test_suite_comparison(self, executions: List[ExecutionRecord]):
        """Generate test suite comparison chart"""
        if not executions:
            return
        
        # Aggregate by test suite
        suite_stats = {}
        for exec in executions:
            if exec.test_suite not in suite_stats:
                suite_stats[exec.test_suite] = {
                    'executions': 0,
                    'total_success_rate': 0,
                    'total_coverage': 0,
                    'total_duration': 0
                }
            
            stats = suite_stats[exec.test_suite]
            stats['executions'] += 1
            stats['total_success_rate'] += (exec.passed_tests / exec.total_tests * 100) if exec.total_tests > 0 else 0
            stats['total_coverage'] += exec.coverage_percentage
            stats['total_duration'] += exec.duration_seconds
        
        # Calculate averages
        for suite, stats in suite_stats.items():
            count = stats['executions']
            stats['avg_success_rate'] = stats['total_success_rate'] / count
            stats['avg_coverage'] = stats['total_coverage'] / count
            stats['avg_duration'] = stats['total_duration'] / count / 60  # Convert to minutes
        
        # Create comparison chart
        suites = list(suite_stats.keys())
        success_rates = [suite_stats[s]['avg_success_rate'] for s in suites]
        coverages = [suite_stats[s]['avg_coverage'] for s in suites]
        durations = [suite_stats[s]['avg_duration'] for s in suites]
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # Success rate comparison
        bars1 = axes[0].bar(suites, success_rates, color='skyblue')
        axes[0].set_title('Average Success Rate by Test Suite')
        axes[0].set_ylabel('Success Rate (%)')
        axes[0].tick_params(axis='x', rotation=45)
        axes[0].set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, value in zip(bars1, success_rates):
            axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{value:.1f}%', ha='center', va='bottom')
        
        # Coverage comparison
        bars2 = axes[1].bar(suites, coverages, color='lightgreen')
        axes[1].set_title('Average Coverage by Test Suite')
        axes[1].set_ylabel('Coverage (%)')
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].set_ylim(0, 100)
        
        for bar, value in zip(bars2, coverages):
            axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{value:.1f}%', ha='center', va='bottom')
        
        # Duration comparison
        bars3 = axes[2].bar(suites, durations, color='salmon')
        axes[2].set_title('Average Duration by Test Suite')
        axes[2].set_ylabel('Duration (minutes)')
        axes[2].tick_params(axis='x', rotation=45)
        
        for bar, value in zip(bars3, durations):
            axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        f'{value:.1f}m', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'test_suite_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_html_dashboard(self, executions: List[ExecutionRecord], 
                                coverage_metrics: List[ExecutionMetric],
                                performance_metrics: List[ExecutionMetric]) -> str:
        """Generate HTML dashboard"""
        
        # Calculate summary statistics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == TestStatus.PASSED])
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        avg_coverage = sum(e.coverage_percentage for e in executions) / len(executions) if executions else 0
        avg_duration = sum(e.duration_seconds for e in executions) / len(executions) if executions else 0
        
        # Recent failures
        recent_failures = [e for e in executions[:10] if e.status == ExecutionStatus.FAILED]
        
        # Template
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiskIntel360 Test Metrics Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-top: 5px; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .status-passed { color: #28a745; }
        .status-failed { color: #dc3545; }
        .status-warning { color: #ffc107; }
        .recent-failures { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .failure-item { padding: 10px; border-left: 4px solid #dc3545; margin-bottom: 10px; background: #f8f9fa; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .timestamp { font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RiskIntel360 Test Metrics Dashboard</h1>
            <p>Generated on {{ timestamp }}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value {{ 'status-passed' if success_rate >= 95 else 'status-warning' if success_rate >= 80 else 'status-failed' }}">
                    {{ "%.1f"|format(success_rate) }}%
                </div>
                <div class="metric-label">Test Success Rate</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {{ 'status-passed' if avg_coverage >= 90 else 'status-warning' if avg_coverage >= 80 else 'status-failed' }}">
                    {{ "%.1f"|format(avg_coverage) }}%
                </div>
                <div class="metric-label">Average Coverage</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">{{ total_executions }}</div>
                <div class="metric-label">Total Test Executions</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">{{ "%.1f"|format(avg_duration/60) }}m</div>
                <div class="metric-label">Average Duration</div>
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="chart-container">
                <h3>Test Execution Trends</h3>
                <img src="test_trends.png" alt="Test Trends" style="width: 100%; max-width: 600px;">
            </div>
            
            <div class="chart-container">
                <h3>Coverage Trends</h3>
                <img src="coverage_trends.png" alt="Coverage Trends" style="width: 100%; max-width: 600px;">
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Test Suite Comparison</h3>
            <img src="test_suite_comparison.png" alt="Test Suite Comparison" style="width: 100%; max-width: 800px;">
        </div>
        
        {% if recent_failures %}
        <div class="recent-failures">
            <h3>Recent Test Failures</h3>
            {% for failure in recent_failures %}
            <div class="failure-item">
                <strong>{{ failure.test_suite }}</strong> - {{ failure.environment }}
                <div class="timestamp">{{ failure.start_time.strftime('%Y-%m-%d %H:%M:%S') }}</div>
                {% if failure.error_message %}
                <div style="margin-top: 5px; font-size: 0.9em;">{{ failure.error_message[:200] }}...</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="chart-container">
            <h3>Recent Test Executions</h3>
            <table>
                <thead>
                    <tr>
                        <th>Test Suite</th>
                        <th>Environment</th>
                        <th>Status</th>
                        <th>Success Rate</th>
                        <th>Coverage</th>
                        <th>Duration</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {% for execution in executions[:20] %}
                    <tr>
                        <td>{{ execution.test_suite }}</td>
                        <td>{{ execution.environment }}</td>
                        <td class="{{ 'status-passed' if execution.status.value == 'passed' else 'status-failed' }}">
                            {{ execution.status.value.upper() }}
                        </td>
                        <td>{{ "%.1f"|format((execution.passed_tests / execution.total_tests * 100) if execution.total_tests > 0 else 0) }}%</td>
                        <td>{{ "%.1f"|format(execution.coverage_percentage) }}%</td>
                        <td>{{ "%.1f"|format(execution.duration_seconds/60) }}m</td>
                        <td class="timestamp">{{ execution.start_time.strftime('%Y-%m-%d %H:%M') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            success_rate=success_rate,
            avg_coverage=avg_coverage,
            total_executions=total_executions,
            avg_duration=avg_duration,
            executions=executions,
            recent_failures=recent_failures
        )
    
    def generate_quality_gates_report(self, execution_id: str) -> Dict[str, Any]:
        """Generate quality gates report for a specific execution"""
        conn = sqlite3.connect(self.collector.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, threshold, current_value, status, blocking, description
            FROM quality_gates 
            WHERE execution_id = ?
        """, (execution_id,))
        
        gates = []
        for row in cursor.fetchall():
            gate = QualityGate(
                name=row[0],
                threshold=row[1],
                current_value=row[2],
                status=row[3],
                blocking=bool(row[4]),
                description=row[5]
            )
            gates.append(gate)
        
        conn.close()
        
        # Analyze gates
        passed_gates = [g for g in gates if g.status == "passed"]
        failed_gates = [g for g in gates if g.status == "failed"]
        blocking_failures = [g for g in failed_gates if g.blocking]
        
        return {
            "execution_id": execution_id,
            "total_gates": len(gates),
            "passed_gates": len(passed_gates),
            "failed_gates": len(failed_gates),
            "blocking_failures": len(blocking_failures),
            "overall_status": "failed" if blocking_failures else "passed",
            "gates": [asdict(g) for g in gates]
        }


# =============================================================================
# GLOBAL METRICS INSTANCE
# =============================================================================

# Global instances for use in tests
test_metrics_collector = MetricsCollector()
test_metrics_dashboard = MetricsDashboard(test_metrics_collector)
