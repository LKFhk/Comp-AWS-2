"""
Test Pydantic v2 Compliance
Verifies that all Pydantic models in the codebase use Pydantic v2 syntax.
"""

import warnings
import pytest
from pydantic import __version__ as pydantic_version


def test_pydantic_version():
    """Verify Pydantic v2 is installed"""
    major_version = int(pydantic_version.split('.')[0])
    assert major_version >= 2, f"Pydantic v2 required, found v{pydantic_version}"


def test_no_deprecation_warnings_agent_models():
    """Test that agent models import without deprecation warnings"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        from riskintel360.models import agent_models
        
        # Check for any deprecation warnings
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, f"Found deprecation warnings: {[str(w.message) for w in deprecation_warnings]}"


def test_no_deprecation_warnings_core_models():
    """Test that core models import without deprecation warnings"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        from riskintel360.models import core
        
        # Check for any deprecation warnings
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, f"Found deprecation warnings: {[str(w.message) for w in deprecation_warnings]}"


def test_no_deprecation_warnings_fintech_models():
    """Test that fintech models import without deprecation warnings"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        from riskintel360.models import fintech_models
        
        # Check for any deprecation warnings
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, f"Found deprecation warnings: {[str(w.message) for w in deprecation_warnings]}"


def test_no_deprecation_warnings_database_models():
    """Test that database models import without deprecation warnings"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        from riskintel360.models import database
        
        # Check for any deprecation warnings
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, f"Found deprecation warnings: {[str(w.message) for w in deprecation_warnings]}"


def test_no_deprecation_warnings_api_models():
    """Test that API models import without deprecation warnings"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        from riskintel360.api import models
        
        # Check for any deprecation warnings
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, f"Found deprecation warnings: {[str(w.message) for w in deprecation_warnings]}"


def test_no_deprecation_warnings_auth_models():
    """Test that auth models import without deprecation warnings"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        from riskintel360.auth import models
        
        # Check for any deprecation warnings
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 0, f"Found deprecation warnings: {[str(w.message) for w in deprecation_warnings]}"


def test_agent_state_model_v2_syntax():
    """Test that AgentState uses Pydantic v2 syntax"""
    from riskintel360.models.agent_models import AgentState, AgentType, SessionStatus
    from datetime import datetime, UTC
    
    # Verify model_config exists (Pydantic v2 pattern)
    assert hasattr(AgentState, 'model_config')
    assert isinstance(AgentState.model_config, dict)
    
    # Test model instantiation
    agent_state = AgentState(
        agent_id="test-agent",
        agent_type=AgentType.FRAUD_DETECTION,
        status=SessionStatus.RUNNING
    )
    
    assert agent_state.agent_id == "test-agent"
    assert agent_state.agent_type == AgentType.FRAUD_DETECTION
    assert agent_state.status == SessionStatus.RUNNING


def test_validation_request_model_v2_syntax():
    """Test that ValidationRequest uses Pydantic v2 syntax"""
    from riskintel360.models.core import ValidationRequest, Priority
    
    # Verify model_config exists (Pydantic v2 pattern)
    assert hasattr(ValidationRequest, 'model_config')
    assert isinstance(ValidationRequest.model_config, dict)
    
    # Test model instantiation
    request = ValidationRequest(
        user_id="test-user",
        business_concept="Test business concept for validation",
        target_market="Fintech sector"
    )
    
    assert request.user_id == "test-user"
    assert request.priority == Priority.MEDIUM


def test_compliance_assessment_model_v2_syntax():
    """Test that ComplianceAssessment uses Pydantic v2 syntax"""
    from riskintel360.models.fintech_models import ComplianceAssessment, ComplianceStatus, RiskLevel
    
    # Verify model_config exists (Pydantic v2 pattern)
    assert hasattr(ComplianceAssessment, 'model_config')
    assert isinstance(ComplianceAssessment.model_config, dict)
    
    # Test model instantiation
    assessment = ComplianceAssessment(
        regulation_id="SEC-001",
        regulation_name="SEC Regulation Test",
        compliance_status=ComplianceStatus.COMPLIANT,
        risk_level=RiskLevel.LOW,
        confidence_score=0.95,
        ai_reasoning="Test reasoning"
    )
    
    assert assessment.regulation_id == "SEC-001"
    # Model uses use_enum_values=True, so enum is converted to string value
    assert assessment.compliance_status == "compliant"


def test_field_validator_v2_syntax():
    """Test that field validators use Pydantic v2 syntax"""
    from riskintel360.models.agent_models import AgentState
    import inspect
    
    # Check that validators use field_validator decorator (v2 syntax)
    # and not @validator (v1 syntax)
    source = inspect.getsource(AgentState)
    
    # Should use field_validator
    assert '@field_validator' in source or 'field_validator' in source
    
    # Should NOT use old @validator syntax
    assert '@validator(' not in source


def test_no_class_config_pattern():
    """Test that models don't use old class Config pattern"""
    from riskintel360.models import agent_models, core, fintech_models
    import inspect
    
    # Check agent_models
    source = inspect.getsource(agent_models)
    assert 'class Config:' not in source, "Found old 'class Config:' pattern in agent_models"
    
    # Check core
    source = inspect.getsource(core)
    assert 'class Config:' not in source, "Found old 'class Config:' pattern in core"
    
    # Check fintech_models
    source = inspect.getsource(fintech_models)
    assert 'class Config:' not in source, "Found old 'class Config:' pattern in fintech_models"


def test_model_dump_instead_of_dict():
    """Test that models use model_dump() instead of dict()"""
    from riskintel360.models.agent_models import AgentState, AgentType, SessionStatus
    
    agent_state = AgentState(
        agent_id="test-agent",
        agent_type=AgentType.FRAUD_DETECTION,
        status=SessionStatus.RUNNING
    )
    
    # Pydantic v2 uses model_dump() instead of dict()
    assert hasattr(agent_state, 'model_dump')
    data = agent_state.model_dump()
    assert isinstance(data, dict)
    assert data['agent_id'] == "test-agent"


def test_model_validation_v2():
    """Test that model validation works with Pydantic v2"""
    from riskintel360.models.core import ValidationRequest
    from pydantic import ValidationError
    import pytest
    
    # Test valid model
    request = ValidationRequest(
        user_id="test-user",
        business_concept="Valid business concept with sufficient length",
        target_market="Fintech"
    )
    assert request.user_id == "test-user"
    
    # Test validation error for short business_concept
    with pytest.raises(ValidationError) as exc_info:
        ValidationRequest(
            user_id="test-user",
            business_concept="Short",  # Too short (min_length=10)
            target_market="Fintech"
        )
    
    # Verify error structure is Pydantic v2 format
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert 'type' in errors[0]  # v2 error format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
