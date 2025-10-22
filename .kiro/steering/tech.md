# RiskIntel360 Technology Stack

## Core Technologies

### Backend
- **Python 3.13+** - Primary development language
- **FastAPI** - REST API framework with async support
- **Pydantic v2** - Data validation and serialization
- **SQLAlchemy 2.0** - Database ORM with async support
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage

### AI/ML Stack
- **Amazon Bedrock Nova** - Primary LLM (Claude-3 family)
  - Claude-3 Haiku: Fast regulatory compliance checks
  - Claude-3 Sonnet: Complex fraud pattern analysis  
  - Claude-3 Opus: Comprehensive risk assessment reasoning
- **Amazon Bedrock AgentCore** - Multi-agent coordination primitives
- **LangChain** - AI agent framework and orchestration
- **LangGraph** - Agent workflow state management
- **scikit-learn** - Unsupervised ML for fraud detection (isolation forests, clustering)
- **NumPy/Pandas** - Data processing and financial analysis

### Frontend
- **React.js** - User interface framework
- **TypeScript** - Type-safe JavaScript
- **WebSocket** - Real-time updates

### Infrastructure
- **AWS CDK** - Infrastructure as code with multi-environment support
- **Docker** - Containerization for agent runtime
- **Amazon ECS** - Container orchestration (auto-scaling 3-50 instances)
- **Amazon S3** - Financial reports, ML models, and data storage
- **Amazon CloudWatch** - Monitoring, logging, and performance metrics
- **Amazon Aurora Serverless** - Market data warehouse (optional)
- **Amazon DynamoDB** - Agent states and real-time fraud alerts (optional)
- **Amazon ElastiCache Redis** - High-performance caching (optional)

## Build System

### Package Management
- **pyproject.toml** - Python project configuration
- **pip/setuptools** - Dependency management
- **requirements.txt** - Production dependencies

### Development Tools
- **Black** - Code formatting (line length: 88)
- **Flake8** - Linting
- **MyPy** - Type checking
- **pytest** - Testing framework with async support

## Common Commands

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Environment setup
cp .env.example .env
```

### Development Server
```bash
# Start API server with hot-reload
uvicorn riskintel360.api.main:app --reload --host 0.0.0.0 --port 8000

# Using Docker for full stack
docker-compose --profile dev up
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=riskintel360

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

### Code Quality
```bash
# Format code
black riskintel360/

# Lint code
flake8 riskintel360/

# Type checking
mypy riskintel360/
```

### AWS Infrastructure
```bash
# Bootstrap CDK (first time)
cdk bootstrap

# Deploy development
cdk deploy --context environment=development

# Deploy production
cdk deploy --context environment=production
```

## Architecture Patterns

### Agent-Based Architecture
- All agents inherit from `BaseAgent` class
- Use `AgentType` enum for type safety
- Implement `execute_task` method for agent logic
- Leverage existing `BedrockClient` for LLM interactions

### Async/Await Patterns
- Use async/await throughout for I/O operations
- FastAPI async endpoints for non-blocking requests
- Async database operations with SQLAlchemy
- Concurrent agent execution with asyncio

### Configuration Management
- Environment-based configuration with `.env` files
- Pydantic models for configuration validation
- AWS Parameter Store for production secrets

### Error Handling
- Structured logging with correlation IDs
- Graceful degradation for external API failures
- AI-powered error analysis and recovery strategies

## Competition Performance Requirements

### Response Time Targets
- **Individual Agent Response**: < 5 seconds
- **Complete Workflow Execution**: < 2 hours
- **System Uptime**: 99.9% availability
- **Concurrent Request Handling**: 50+ simultaneous requests

### Public Data Integration
- **Primary Sources** (Free): SEC EDGAR, FINRA, CFPB, FRED, Treasury.gov, Yahoo Finance
- **Secondary Sources** (Premium): Bloomberg API, Reuters, S&P Capital IQ
- **Data Quality**: 90% of insights achievable through public sources
- **Cost Optimization**: 80% cost reduction through public-data-first approach

### ML Performance Metrics
- **Fraud Detection Accuracy**: 90% false positive reduction
- **Anomaly Detection**: Real-time transaction analysis
- **Model Adaptation**: Unsupervised learning for new fraud patterns
- **Confidence Scoring**: All ML predictions include confidence levels