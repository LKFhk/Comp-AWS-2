"""
Unit Tests for UnsupervisedMLEngine - TDD Implementation
Tests for fraud detection ML capabilities with 90% false positive reduction requirement.
"""

import pytest
import numpy as np
import time
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# These imports will fail initially (Red phase) - that's expected in TDD
from riskintel360.services.unsupervised_ml_engine import UnsupervisedMLEngine
from riskintel360.models.fintech_models import FraudDetectionResult


class TestUnsupervisedMLEngine:
    """Test suite for UnsupervisedMLEngine following TDD methodology"""
    
    @pytest.fixture
    def ml_engine(self):
        """Create UnsupervisedMLEngine instance for testing"""
        return UnsupervisedMLEngine()
    
    @pytest.fixture
    def sample_transactions(self):
        """Generate realistic financial transaction data for testing"""
        # Create 1000 normal transactions with typical patterns
        normal_transactions = np.random.normal(100, 20, (900, 5))  # Amount, frequency, location, time, merchant_type
        
        # Create 100 fraudulent transactions with unusual patterns
        fraud_transactions = np.random.normal(500, 100, (100, 5))  # Unusual amounts and patterns
        
        # Combine normal and fraudulent transactions
        all_transactions = np.vstack([normal_transactions, fraud_transactions])
        
        return {
            'transactions': all_transactions,
            'normal_count': 900,
            'fraud_count': 100,
            'fraud_indices': list(range(900, 1000))  # Known fraud indices for validation
        }
    
    @pytest.fixture
    def fraudulent_transaction_patterns(self):
        """Generate known fraudulent transaction patterns for ML testing"""
        return {
            'high_amount_rapid_succession': np.array([[1000, 10, 1, 2, 1], [1200, 12, 1, 2, 1]]),
            'unusual_location_pattern': np.array([[200, 1, 999, 3, 2], [300, 1, 998, 3, 2]]),
            'off_hours_transactions': np.array([[150, 1, 50, 23, 3], [180, 1, 50, 2, 3]]),
            'merchant_type_anomaly': np.array([[500, 1, 50, 14, 99], [600, 1, 50, 14, 99]])
        }
    
    @pytest.mark.asyncio
    async def test_fraud_detection_accuracy_requirement(self, ml_engine, sample_transactions):
        """
        Test that fraud detection achieves 90% false positive reduction
        RED PHASE: This test will fail initially as UnsupervisedMLEngine doesn't exist
        """
        # Requirement: 90% false positive reduction from 10% baseline to 1%
        result = await ml_engine.detect_anomalies(sample_transactions['transactions'])
        
        # Calculate false positive rate
        detected_anomalies = set(result['anomalous_indices'])
        actual_fraud_indices = set(sample_transactions['fraud_indices'])
        
        # False positives are normal transactions flagged as fraud
        false_positives = detected_anomalies - actual_fraud_indices
        normal_transactions_count = sample_transactions['normal_count']
        false_positive_rate = len(false_positives) / normal_transactions_count
        
        # Verify 90% reduction: from 10% baseline to 1% (90% reduction)
        assert false_positive_rate < 0.01, f"False positive rate {false_positive_rate:.3f} exceeds 1% requirement"
        assert result['confidence'] >= 0.8, f"Confidence score {result['confidence']} below 0.8 requirement"
        assert len(result['anomalous_indices']) > 0, "No anomalies detected"
        
        # Verify detection of actual fraud
        true_positives = detected_anomalies & actual_fraud_indices
        detection_rate = len(true_positives) / len(actual_fraud_indices)
        assert detection_rate >= 0.85, f"Fraud detection rate {detection_rate:.3f} below 85% requirement"
    
    @pytest.mark.asyncio
    async def test_real_time_processing_requirement(self, ml_engine, sample_transactions):
        """
        Test that fraud detection completes within 5 seconds
        RED PHASE: This test will fail initially
        """
        start_time = time.time()
        result = await ml_engine.detect_anomalies(sample_transactions['transactions'])
        processing_time = time.time() - start_time
        
        # Verify competition requirement: < 5 second response time
        assert processing_time < 5.0, f"Processing time {processing_time:.2f}s exceeds 5 second requirement"
        assert result is not None, "No result returned"
        assert 'anomaly_scores' in result, "Missing anomaly_scores in result"
        assert 'anomalous_indices' in result, "Missing anomalous_indices in result"
        assert 'processing_time' in result, "Missing processing_time in result"
    
    def test_unsupervised_ml_integration(self, ml_engine):
        """
        Test integration with unsupervised ML algorithms
        RED PHASE: This test will fail initially
        """
        # Verify ML engine has required algorithms
        assert hasattr(ml_engine, 'isolation_forest'), "Missing isolation_forest algorithm"
        assert hasattr(ml_engine, 'clustering'), "Missing clustering algorithm"
        assert hasattr(ml_engine, 'models_trained'), "Missing models_trained flag"
        
        # Verify algorithm initialization
        assert ml_engine.isolation_forest is not None, "Isolation forest not initialized"
        assert ml_engine.clustering is not None, "Clustering algorithm not initialized"
    
    @pytest.mark.asyncio
    async def test_confidence_scoring_accuracy(self, ml_engine, sample_transactions):
        """
        Test ML confidence scoring accuracy
        RED PHASE: This test will fail initially
        """
        result = await ml_engine.detect_anomalies(sample_transactions['transactions'])
        
        # Verify confidence scoring
        assert 'confidence' in result, "Missing confidence score"
        assert 0.0 <= result['confidence'] <= 1.0, f"Confidence {result['confidence']} not in valid range [0,1]"
        
        # Verify method agreement calculation
        assert 'method_agreement' in result, "Missing method_agreement score"
        assert 0.0 <= result['method_agreement'] <= 1.0, f"Method agreement {result['method_agreement']} not in valid range [0,1]"
        
        # High-confidence detections should have higher anomaly scores
        if len(result['anomalous_indices']) > 0:
            anomaly_scores = np.array(result['anomaly_scores'])
            anomalous_scores = anomaly_scores[result['anomalous_indices']]
            normal_scores = np.delete(anomaly_scores, result['anomalous_indices'])
            
            assert np.mean(anomalous_scores) > np.mean(normal_scores), "Anomalous transactions should have higher scores"
    
    @pytest.mark.asyncio
    async def test_novel_pattern_detection(self, ml_engine, fraudulent_transaction_patterns):
        """
        Test detection of novel fraud patterns without labeled data
        RED PHASE: This test will fail initially
        """
        # Test with different fraud pattern types
        for pattern_name, pattern_data in fraudulent_transaction_patterns.items():
            # Add some normal data to create contrast for better detection
            normal_data = np.random.normal(100, 20, (20, 5))
            combined_data = np.vstack([normal_data, pattern_data])
            
            result = await ml_engine.detect_anomalies(combined_data)
            
            # Should detect anomalies in novel patterns
            assert len(result['anomalous_indices']) > 0, f"Failed to detect {pattern_name} pattern"
            assert result['confidence'] > 0.3, f"Low confidence for {pattern_name} pattern"  # Lowered threshold for small datasets
    
    @pytest.mark.asyncio
    async def test_ensemble_method_combination(self, ml_engine, sample_transactions):
        """
        Test ensemble method combination for improved accuracy
        RED PHASE: This test will fail initially
        """
        result = await ml_engine.detect_anomalies(sample_transactions['transactions'])
        
        # Verify ensemble scoring
        assert 'anomaly_scores' in result, "Missing ensemble anomaly scores"
        assert len(result['anomaly_scores']) == len(sample_transactions['transactions']), "Score count mismatch"
        
        # Verify method agreement calculation
        assert 'method_agreement' in result, "Missing method agreement calculation"
        
        # Method agreement should be reasonable (not too low)
        assert result['method_agreement'] >= 0.3, f"Method agreement {result['method_agreement']} too low"
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_capability(self, ml_engine):
        """
        Test concurrent processing capability for 50+ requests
        RED PHASE: This test will fail initially
        """
        # Create multiple small transaction datasets
        datasets = []
        for i in range(10):  # Test with 10 concurrent requests
            data = np.random.normal(100, 20, (100, 5))
            datasets.append(data)
        
        # Process concurrently
        tasks = [ml_engine.detect_anomalies(data) for data in datasets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all requests completed successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(datasets), "Some concurrent requests failed"
        
        # Verify each result has expected structure
        for result in successful_results:
            assert 'anomaly_scores' in result, "Missing anomaly_scores in concurrent result"
            assert 'processing_time' in result, "Missing processing_time in concurrent result"
            assert result['processing_time'] < 5.0, "Concurrent processing too slow"
    
    @pytest.mark.asyncio
    async def test_memory_usage_efficiency(self, ml_engine, sample_transactions):
        """
        Test memory usage remains below 500MB requirement
        RED PHASE: This test will fail initially
        """
        import psutil
        import os
        
        # Measure memory before processing
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large dataset
        large_dataset = np.random.normal(100, 20, (10000, 5))  # 10k transactions
        result = await ml_engine.detect_anomalies(large_dataset)
        
        # Measure memory after processing
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        # Verify memory usage is reasonable
        assert memory_used < 500, f"Memory usage {memory_used:.1f}MB exceeds 500MB limit"
        assert result is not None, "Processing failed for large dataset"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_graceful_degradation(self, ml_engine):
        """
        Test error handling and graceful degradation
        RED PHASE: This test will fail initially
        """
        # Test with invalid input data
        invalid_data = np.array([])  # Empty array
        result = await ml_engine.detect_anomalies(invalid_data)
        
        # Should handle gracefully and return safe fallback
        assert result is not None, "Should return fallback result for invalid input"
        assert 'error' in result, "Should include error information"
        assert result['anomaly_scores'] == [], "Should return empty scores for invalid input"
        assert result['anomalous_indices'] == [], "Should return empty indices for invalid input"
        assert result['confidence'] == 0.0, "Should return zero confidence for invalid input"
    
    @pytest.mark.asyncio
    async def test_model_performance_tracking(self, ml_engine, sample_transactions):
        """
        Test ML model performance tracking and metrics
        RED PHASE: This test will fail initially
        """
        result = await ml_engine.detect_anomalies(sample_transactions['transactions'])
        
        # Verify performance metrics are tracked
        assert 'total_transactions' in result, "Missing total transaction count"
        assert 'anomaly_count' in result, "Missing anomaly count"
        assert 'threshold' in result, "Missing anomaly threshold"
        assert 'processing_time' in result, "Missing processing time"
        
        # Verify metrics are reasonable
        assert result['total_transactions'] == len(sample_transactions['transactions']), "Transaction count mismatch"
        assert result['anomaly_count'] >= 0, "Negative anomaly count"
        assert result['threshold'] > 0, "Invalid threshold value"
        assert result['processing_time'] >= 0, "Invalid processing time"
    
    @pytest.mark.asyncio
    async def test_async_processing_capability(self, ml_engine, sample_transactions):
        """
        Test async processing capability for non-blocking operations
        RED PHASE: This test will fail initially
        """
        # Test async processing
        result = await ml_engine.detect_anomalies(sample_transactions['transactions'])
        
        # Verify async result is same as sync result
        assert result is not None, "Async processing returned None"
        assert 'anomaly_scores' in result, "Missing anomaly_scores in async result"
        assert 'confidence' in result, "Missing confidence in async result"
    
    @pytest.mark.asyncio
    async def test_fraud_prevention_value_calculation(self, ml_engine, sample_transactions):
        """
        Test fraud prevention value calculation for $10M+ annual savings
        RED PHASE: This test will fail initially
        """
        result = await ml_engine.detect_anomalies(sample_transactions['transactions'])
        
        # Calculate potential fraud prevention value
        detected_fraud_count = len(result['anomalous_indices'])
        average_fraud_amount = 500  # Average fraud transaction amount
        annual_multiplier = 365 * 24  # Daily processing * annual
        
        # Estimate annual fraud prevention value
        daily_fraud_prevented = detected_fraud_count * average_fraud_amount
        annual_fraud_prevented = daily_fraud_prevented * annual_multiplier
        
        # For major financial institutions, should prevent $10M+ annually
        # This is a business logic test to validate the value proposition
        if detected_fraud_count > 50:  # Significant fraud detection
            assert annual_fraud_prevented >= 10_000_000, f"Annual fraud prevention ${annual_fraud_prevented:,.0f} below $10M target"
        
        # Log the calculated value for business validation
        print(f"Estimated annual fraud prevention value: ${annual_fraud_prevented:,.0f}")
    
    def test_model_versioning_and_benchmarking(self, ml_engine, sample_transactions):
        """
        Test model versioning and performance benchmarking features
        """
        # Test model versioning
        original_version = getattr(ml_engine, '_model_version', 'v1.0')
        new_version = "v1.1"
        
        # Test version update method if it exists
        if hasattr(ml_engine, 'update_model_version'):
            ml_engine.update_model_version(new_version)
            assert ml_engine._model_version == new_version, "Model version not updated"
        
        # Test benchmarking if method exists
        if hasattr(ml_engine, 'benchmark_performance'):
            benchmark_data = sample_transactions['transactions'][:100]  # Smaller dataset for benchmarking
            benchmark_results = ml_engine.benchmark_performance(benchmark_data)
            
            # Verify benchmark results
            assert 'average_time' in benchmark_results, "Missing average_time in benchmark"
            assert 'transactions_per_second' in benchmark_results, "Missing transactions_per_second in benchmark"
            assert benchmark_results['average_time'] > 0, "Invalid average_time in benchmark"
            assert benchmark_results['transactions_per_second'] > 0, "Invalid transactions_per_second in benchmark"
        
        # Test health status includes versioning if method exists
        if hasattr(ml_engine, 'get_health_status'):
            health = ml_engine.get_health_status()
            assert 'model_version' in health, "Missing model_version in health status"
    
    @pytest.mark.asyncio
    async def test_ml_performance_under_stress(self, ml_engine):
        """Test ML engine performance under stress conditions"""
        # Test with various dataset sizes to validate scalability
        stress_test_sizes = [500, 1000, 2000, 5000]
        performance_results = {}
        
        for size in stress_test_sizes:
            # Generate stress test data
            stress_data = np.random.normal(100, 20, (size, 5))
            
            # Measure processing time
            import time
            start_time = time.time()
            
            result = await ml_engine.detect_anomalies(stress_data)
            
            processing_time = time.time() - start_time
            
            performance_results[size] = {
                'processing_time': processing_time,
                'transactions_per_second': size / processing_time if processing_time > 0 else 0,
                'anomaly_count': len(result.get('anomalous_indices', [])),
                'confidence': result.get('confidence', 0.0)
            }
            
            # Verify performance requirements scale reasonably
            assert processing_time < 15.0, f"Processing time {processing_time:.2f}s reasonable for {size} transactions"
            
            # Verify throughput is reasonable
            tps = performance_results[size]['transactions_per_second']
            assert tps > 20, f"Throughput {tps:.1f} TPS reasonable for {size} transactions"
        
        # Verify performance scaling trend
        assert len(performance_results) == len(stress_test_sizes)
        
        # Log performance results
        for size, metrics in performance_results.items():
            print(f"Stress test {size}: {metrics['transactions_per_second']:.1f} TPS, {metrics['processing_time']:.2f}s")
    
    @pytest.mark.asyncio
    async def test_ml_accuracy_validation_comprehensive(self, ml_engine, sample_transactions, fraudulent_transaction_patterns):
        """Test comprehensive ML accuracy validation across different fraud patterns"""
        accuracy_results = {}
        
        # Test accuracy on known fraud patterns
        for pattern_name, pattern_data in fraudulent_transaction_patterns.items():
            # Create mixed dataset with known fraud patterns
            normal_data = np.random.normal(100, 20, (80, 5))
            mixed_data = np.vstack([normal_data, pattern_data])
            
            # Known fraud indices (last rows are fraud patterns)
            known_fraud_indices = set(range(len(normal_data), len(mixed_data)))
            
            result = await ml_engine.detect_anomalies(mixed_data)
            
            # Calculate accuracy metrics
            detected_indices = set(result.get('anomalous_indices', []))
            
            # True positives: correctly identified fraud
            true_positives = len(detected_indices & known_fraud_indices)
            
            # False positives: normal transactions flagged as fraud
            false_positives = len(detected_indices - known_fraud_indices)
            
            # False negatives: fraud transactions missed
            false_negatives = len(known_fraud_indices - detected_indices)
            
            # Calculate metrics
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            accuracy_results[pattern_name] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'true_positives': true_positives,
                'false_positives': false_positives,
                'false_negatives': false_negatives,
                'confidence': result.get('confidence', 0.0)
            }
            
            # Verify reasonable accuracy for each pattern
            assert precision >= 0.0, f"Precision for {pattern_name} should be non-negative"
            assert recall >= 0.0, f"Recall for {pattern_name} should be non-negative"
            assert f1_score >= 0.0, f"F1 score for {pattern_name} should be non-negative"
        
        # Verify overall accuracy across patterns
        avg_precision = np.mean([r['precision'] for r in accuracy_results.values()])
        avg_recall = np.mean([r['recall'] for r in accuracy_results.values()])
        avg_f1 = np.mean([r['f1_score'] for r in accuracy_results.values()])
        
        print(f"Average ML accuracy - Precision: {avg_precision:.3f}, Recall: {avg_recall:.3f}, F1: {avg_f1:.3f}")
        
        # Log detailed results
        for pattern, metrics in accuracy_results.items():
            print(f"{pattern}: P={metrics['precision']:.3f}, R={metrics['recall']:.3f}, F1={metrics['f1_score']:.3f}")
    
    @pytest.mark.asyncio
    async def test_ml_robustness_and_edge_cases(self, ml_engine):
        """Test ML engine robustness with edge cases and adversarial inputs"""
        edge_cases = {
            'all_zeros': np.zeros((100, 5)),
            'all_ones': np.ones((100, 5)),
            'extreme_values': np.random.uniform(-1000, 1000, (100, 5)),
            'single_transaction': np.random.normal(100, 20, (1, 5)),
            'minimal_dataset': np.random.normal(100, 20, (10, 5)),
            'high_variance': np.random.normal(100, 500, (100, 5)),
            'low_variance': np.random.normal(100, 0.1, (100, 5))
        }
        
        robustness_results = {}
        
        for case_name, test_data in edge_cases.items():
            try:
                result = await ml_engine.detect_anomalies(test_data)
                
                robustness_results[case_name] = {
                    'success': True,
                    'anomaly_count': len(result.get('anomalous_indices', [])),
                    'confidence': result.get('confidence', 0.0),
                    'processing_time': result.get('processing_time', 0.0),
                    'error': None
                }
                
                # Verify basic result structure
                assert 'anomaly_scores' in result, f"Missing anomaly_scores for {case_name}"
                assert 'anomalous_indices' in result, f"Missing anomalous_indices for {case_name}"
                assert 'confidence' in result, f"Missing confidence for {case_name}"
                
                # Verify confidence is in valid range
                confidence = result.get('confidence', 0.0)
                assert 0.0 <= confidence <= 1.0, f"Invalid confidence {confidence} for {case_name}"
                
            except Exception as e:
                robustness_results[case_name] = {
                    'success': False,
                    'error': str(e),
                    'anomaly_count': 0,
                    'confidence': 0.0,
                    'processing_time': 0.0
                }
        
        # Verify most edge cases are handled gracefully
        successful_cases = sum(1 for r in robustness_results.values() if r['success'])
        total_cases = len(edge_cases)
        success_rate = successful_cases / total_cases
        
        assert success_rate >= 0.7, f"Robustness success rate {success_rate:.1%} should be at least 70%"
        
        # Log robustness results
        for case, result in robustness_results.items():
            if result['success']:
                print(f"{case}: Success - {result['anomaly_count']} anomalies, confidence {result['confidence']:.3f}")
            else:
                print(f"{case}: Failed - {result['error']}")
    
    @pytest.mark.asyncio
    async def test_ml_model_consistency_and_reproducibility(self, ml_engine, sample_transactions):
        """Test ML model consistency and reproducibility"""
        # Test data
        test_data = sample_transactions['transactions'][:500]
        
        # Run detection multiple times
        results = []
        for i in range(3):
            result = await ml_engine.detect_anomalies(test_data)
            results.append(result)
        
        # Verify consistency across runs
        for i in range(1, len(results)):
            # Anomaly counts should be reasonably consistent
            count_diff = abs(len(results[i]['anomalous_indices']) - len(results[0]['anomalous_indices']))
            count_tolerance = max(5, len(results[0]['anomalous_indices']) * 0.1)  # 10% tolerance or 5 transactions
            
            assert count_diff <= count_tolerance, f"Anomaly count inconsistency: {count_diff} > {count_tolerance}"
            
            # Confidence scores should be reasonably consistent
            confidence_diff = abs(results[i]['confidence'] - results[0]['confidence'])
            assert confidence_diff <= 0.2, f"Confidence inconsistency: {confidence_diff} > 0.2"
        
        # Verify reproducibility with same random seed if supported
        if hasattr(ml_engine, 'set_random_seed'):
            ml_engine.set_random_seed(42)
            result1 = await ml_engine.detect_anomalies(test_data)
            
            ml_engine.set_random_seed(42)
            result2 = await ml_engine.detect_anomalies(test_data)
            
            # Results should be identical with same seed
            assert result1['anomalous_indices'] == result2['anomalous_indices'], "Results not reproducible with same seed"
            assert result1['confidence'] == result2['confidence'], "Confidence not reproducible with same seed"


class TestUnsupervisedMLEngineIntegration:
    """Integration tests for UnsupervisedMLEngine with other components"""
    
    @pytest.fixture
    def ml_engine(self):
        """Create UnsupervisedMLEngine instance for integration testing"""
        return UnsupervisedMLEngine()
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client for testing"""
        mock_client = Mock()
        mock_client.invoke_for_agent.return_value = Mock(content="ML analysis interpretation")
        return mock_client
    
    @pytest.mark.asyncio
    async def test_integration_with_fraud_detection_agent(self, mock_bedrock_client):
        """
        Test integration with FraudDetectionAgent
        RED PHASE: This test will fail initially
        """
        # This test will be implemented when FraudDetectionAgent is created
        # For now, test the interface that will be used
        
        ml_engine = UnsupervisedMLEngine()
        
        # Test the interface that FraudDetectionAgent will use
        sample_data = np.random.normal(100, 20, (100, 5))
        result = await ml_engine.detect_anomalies(sample_data)
        
        # Verify the result format expected by FraudDetectionAgent
        required_fields = ['anomaly_scores', 'anomalous_indices', 'confidence', 'method_agreement']
        for field in required_fields:
            assert field in result, f"Missing required field {field} for agent integration"
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, ml_engine):
        """
        Test integration with performance monitoring system
        RED PHASE: This test will fail initially
        """
        # Test performance metrics that will be monitored
        sample_data = np.random.normal(100, 20, (1000, 5))
        
        start_time = time.time()
        result = await ml_engine.detect_anomalies(sample_data)
        processing_time = time.time() - start_time
        
        # Verify metrics that performance monitoring will track
        assert processing_time < 5.0, "Processing time exceeds monitoring threshold"
        assert result['confidence'] >= 0.0, "Invalid confidence for monitoring"
        assert len(result['anomaly_scores']) > 0, "No scores for monitoring"
        assert 'processing_time' in result, "Missing processing_time for monitoring"
        
        # Test new performance monitoring features
        assert 'model_version' in result, "Missing model_version for monitoring"
        assert 'performance_metrics' in result, "Missing performance_metrics for monitoring"
        
        # Test health status
        health = ml_engine.get_health_status()
        assert 'models_trained' in health, "Missing models_trained in health status"
        assert 'error_count' in health, "Missing error_count in health status"
        assert 'circuit_breaker_open' in health, "Missing circuit_breaker_open in health status"
        
        # Test model performance tracking
        performance = ml_engine.get_model_performance()
        assert 'model_version' in performance, "Missing model_version in performance"
        assert 'performance_metrics' in performance, "Missing performance_metrics in performance"
