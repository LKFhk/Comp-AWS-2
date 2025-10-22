# RiskIntel360 Project Structure

## Directory Organization

### Root Level
```
├── .env.example                    # Environment configuration template
├── .kiro/                         # Kiro IDE configuration and specs
├── docker-compose.yml             # Multi-service development environment
├── pyproject.toml                 # Python project configuration
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```

### Core Application (`riskintel360/`)
```
riskintel360/
├── __init__.py
├── agents/                        # AI agent implementations
│   ├── __init__.py
│   ├── base_agent.py             # Base class for all agents
│   ├── agent_factory.py          # Agent creation and management
│   ├── market_research_agent.py  # Market analysis capabilities
│   ├── risk_assessment_agent.py  # Financial risk evaluation
│   ├── regulatory_compliance_agent.py  # NEW: Compliance monitoring
│   ├── fraud_detection_agent.py  # NEW: ML-based fraud detection
│   └── kyc_verification_agent.py # NEW: Customer verification
├── api/                          # REST API endpoints
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── validations.py            # Validation endpoints
│   ├── websockets.py             # Real-time communication
│   ├── credentials.py            # AWS credential management
│   └── fintech_endpoints.py      # NEW: Fintech-specific endpoints
├── models/                       # Data models and schemas
│   ├── __init__.py
│   ├── agent_models.py           # Agent state and configuration
│   ├── workflow_models.py        # Workflow orchestration models
│   └── fintech_models.py         # NEW: Financial data models
├── services/                     # Business logic services
│   ├── __init__.py
│   ├── workflow_orchestrator.py  # Multi-agent coordination
│   ├── bedrock_client.py         # Amazon Bedrock integration
│   ├── external_data_integration_layer.py  # External API integration
│   ├── credential_manager.py     # AWS credential management
│   └── unsupervised_ml_engine.py # NEW: ML fraud detection engine
├── config/                       # Configuration modules
│   ├── __init__.py
│   └── settings.py               # Application settings
└── utils/                        # Helper utilities
    ├── __init__.py
    └── logging.py                # Structured logging
```

### Frontend (`frontend/`)
```
frontend/
├── src/
│   ├── components/               # Reusable UI components
│   │   └── FinTech/             # NEW: Fintech-specific components
│   ├── pages/                   # Page-level components
│   │   ├── CredentialsManagement/  # AWS credential setup
│   │   └── RiskIntelDashboard/  # NEW: Financial risk dashboard
│   ├── services/                # API client services
│   │   ├── credentialsService.ts
│   │   └── fintechService.ts    # NEW: Fintech API client
│   └── types/                   # TypeScript type definitions
├── package.json                 # Node.js dependencies
└── cypress/                     # E2E testing
```

### Infrastructure (`infrastructure/`)
```
infrastructure/
├── app.py                       # CDK application entry point
├── stacks/                      # CDK infrastructure stacks
│   ├── compute_stack.py         # ECS and Lambda resources
│   ├── data_stack.py            # Database and storage
│   ├── networking_stack.py      # VPC and security groups
│   └── ai_stack.py              # Bedrock and AI services
└── config/                      # Environment-specific configs
```

### Testing (`tests/`)
```
tests/
├── unit/                        # Unit tests
│   ├── test_agents/             # Agent-specific tests
│   ├── test_services/           # Service layer tests
│   └── test_models/             # Data model tests
├── integration/                 # Integration tests
│   ├── test_workflow_integration.py
│   ├── test_fintech_workflow_integration.py  # NEW
│   └── test_public_fintech_data_integration.py  # NEW
├── e2e/                         # End-to-end tests
│   ├── test_e2e_api_integration.py
│   └── test_riskintel360_e2e.py  # NEW: Complete fintech workflow
└── fixtures/                    # Test data and mocks
```

## File Naming Conventions

### Python Files
- **Snake case**: `regulatory_compliance_agent.py`
- **Test files**: `test_` prefix (e.g., `test_fraud_detection_agent.py`)
- **Agent files**: `*_agent.py` suffix
- **Service files**: Descriptive names (e.g., `workflow_orchestrator.py`)

### TypeScript/React Files
- **PascalCase** for components: `RiskIntelDashboard.tsx`
- **camelCase** for services: `fintechService.ts`
- **kebab-case** for directories: `risk-intel-dashboard/`

### Configuration Files
- **Lowercase with hyphens**: `docker-compose.yml`
- **Dot files**: `.env.example`, `.gitignore`

## Import Patterns

### Relative Imports (Preferred)
```python
# Within riskintel360 package
from .base_agent import BaseAgent
from ..models.agent_models import AgentType
from ..services.bedrock_client import BedrockClient
```

### Absolute Imports (When Necessary)
```python
# Cross-package imports
from riskintel360.agents.base_agent import BaseAgent
from riskintel360.models.fintech_models import FraudDetectionResult
```

## Extension Guidelines

### Adding New Agents
1. Create new file in `riskintel360/agents/`
2. Inherit from `BaseAgent` class
3. Add agent type to `AgentType` enum
4. Update `AgentFactory` with creation method
5. Add corresponding tests in `tests/unit/test_agents/`

### Adding New Services
1. Create new file in `riskintel360/services/`
2. Follow async/await patterns for I/O operations
3. Add configuration to `config/settings.py`
4. Create unit and integration tests

### Adding New API Endpoints
1. Add endpoints to appropriate file in `riskintel360/api/`
2. Use FastAPI dependency injection for services
3. Include proper error handling and validation
4. Add OpenAPI documentation with docstrings

### Adding New Data Models
1. Use Pydantic v2 syntax for validation
2. Add to appropriate file in `riskintel360/models/`
3. Include field descriptions and validation rules
4. Create corresponding database migrations if needed