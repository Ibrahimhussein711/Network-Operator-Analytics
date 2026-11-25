import copy
import pytest
import jsonschema
from pydantic import ValidationError
from models.envelope import CommonEventEnvelope

def test_structural_parity_on_valid_events(schema_validator, canonical_events):
    """Assert that every valid canonical event is accepted by BOTH JSON Schema and Pydantic."""
    for event_name, payload in canonical_events.items():
        # JSON Schema check
        schema_validator.validate(payload)
        # Pydantic check
        CommonEventEnvelope.model_validate(payload)

@pytest.mark.parametrize("event_type", [
    "agent_registered", "task_started", "connection_requested", "transfer_started", "beacon_missed"
])
def test_structural_parity_on_missing_envelope_fields(schema_validator, canonical_events, event_type):
    """Assert that missing envelope fields fail both JSON Schema and Pydantic."""
    base = copy.deepcopy(canonical_events[event_type])
    del base["ts"]
    
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

@pytest.mark.parametrize("invalid_source", ["p4_c2", "p5_shell", "p6_exfil"])
def test_structural_parity_on_inferred_flag(schema_validator, canonical_events, invalid_source):
    """Simulators with inferred == True must fail in both JSON Schema and Pydantic."""
    event_type = {
        "p4_c2": "agent_registered",
        "p5_shell": "connection_requested",
        "p6_exfil": "transfer_started"
    }[invalid_source]

    base = copy.deepcopy(canonical_events[event_type])
    base["metadata"]["inferred"] = True

    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

def test_structural_parity_on_negative_bytes(schema_validator, canonical_events):
    """Negative bytes_transferred_delta must fail in both JSON Schema and Pydantic."""
    base = copy.deepcopy(canonical_events["task_progress"])
    base["bytes_transferred_delta"] = -5

    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)
