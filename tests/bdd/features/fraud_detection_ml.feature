Feature: Advanced Fraud Detection with Unsupervised ML
  As a security analyst
  I want ML-powered fraud detection with 90% false positive reduction
  So that I can prevent $10M+ annual fraud losses through early detection

  Background:
    Given the RiskIntel360 platform is deployed
    And the Fraud Detection Agent is active with trained ML models
    And the UnsupervisedMLEngine is initialized with isolation forest and clustering algorithms

  Scenario: Real-time fraud detection with 90% false positive reduction
    Given a stream of 1000 financial transactions is processed
    And the historical false positive rate was 10% with traditional methods
    When the unsupervised ML engine analyzes transaction patterns
    Then it should identify anomalous transactions with confidence scores
    And the false positive rate should be less than 1% (90% reduction from 10% baseline)
    And processing time should be under 5 seconds
    And fraud alerts should include ML-based explanations
    And the confidence score should be above 0.8 for high-risk transactions

  Scenario: Automatic adaptation to new fraud patterns
    Given the ML models are trained on historical transaction data
    And no labeled fraud examples are available for new patterns
    When new, previously unseen fraud patterns are introduced in transaction data
    Then the unsupervised algorithms should detect anomalies without labeled data
    And the models should automatically update fraud detection rules
    And the confidence scores should reflect pattern novelty
    And the system should alert security teams of new pattern discovery
    And the anomaly detection accuracy should remain above 85%

  Scenario: Ensemble method fraud scoring with high confidence
    Given multiple ML algorithms are available (isolation forest, clustering, autoencoders)
    And a suspicious transaction is being analyzed
    When the UnsupervisedMLEngine processes the transaction
    Then it should use ensemble methods to combine algorithm results
    And it should provide a weighted fraud probability score
    And it should include individual algorithm confidence scores
    And the ensemble confidence should be higher than individual algorithm confidence
    And method agreement percentage should be calculated and reported

  Scenario: Real-time processing performance requirement
    Given the fraud detection system is under load
    And 50+ concurrent transaction analysis requests are received
    When the UnsupervisedMLEngine processes all requests
    Then each individual analysis should complete within 5 seconds
    And the system should maintain 99.9% uptime
    And memory usage should remain below 500MB per analysis
    And CPU usage should not exceed 80% during peak load

  Scenario: ML model performance monitoring and adaptation
    Given the fraud detection models have been running for 24 hours
    And transaction patterns have evolved during this period
    When the system evaluates model performance
    Then it should track anomaly detection accuracy over time
    And it should identify when model retraining is needed
    And it should automatically adapt to new transaction patterns
    And it should maintain fraud prevention value above $10M annually
    And it should log model performance metrics for audit purposes

  Scenario: Integration with LLM interpretation for explainable AI
    Given an anomalous transaction has been detected by ML algorithms
    And the transaction has high fraud probability scores
    When the system generates fraud alerts
    Then it should provide ML-based technical explanations
    And it should include LLM-generated human-readable interpretations
    And it should explain which features contributed to the anomaly score
    And it should provide recommended actions based on fraud type
    And it should include confidence levels for both ML and LLM components