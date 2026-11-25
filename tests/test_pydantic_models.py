import copy
import pytest
from pydantic import ValidationError
from models.envelope import CommonEventEnvelope
from models.enums import P4ActionLabelEnum, P5CommandLabelEnum, ProtocolEnum, SourceEnum, StatusEnum

def test_pydantic_canonical_events_validity(canonical_events):
    """Test that all 20 canonical valid events validate cleanly in Pydantic."""
    for event_name, payload in canonical_events.items():
        try:
            model = CommonEventEnvelope.model_validate(payload)
            assert model.event_id is not None
            assert model.type == event_name
        except ValidationError as e:
            pytest.fail(f"Canonical event '{event_name}' failed Pydantic validation: {e}")

def test_pydantic_extra_fields_forbidden(canonical_events):
    """Assert rejection when extra unexpected fields are added."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    base["unapproved_extra_field"] = "malicious_payload"
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

def test_pydantic_host_validation(canonical_events):
    """Assert rejection when both ip and hostname are None."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    base["host"]["ip"] = None
    base["host"]["hostname"] = None
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

def test_pydantic_destination_icmp_port_restriction(canonical_events):
    """Assert rejection when ICMP destination specifies a port."""
    base = copy.deepcopy(canonical_events["transfer_started"])
    base["destination"]["protocol"] = "icmp"
    base["destination"]["port"] = 80
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

def test_pydantic_source_type_status_mismatch(canonical_events):
    """Assert rejection when source/type or type/status are mismatched."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    base["source"] = SourceEnum.P5_SHELL
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

    base = copy.deepcopy(canonical_events["task_started"])
    base["status"] = StatusEnum.COMPLETED
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

def test_pydantic_initiation_timeout_sec_mandatory(canonical_events):
    """Initiation events must have a positive timeout_sec."""
    base = copy.deepcopy(canonical_events["task_started"])
    base["timeout_sec"] = None
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

def test_pydantic_p6_cross_field_validators(canonical_events):
    """P6 Tier 2 cross-field validations: chunk_index < chunks_total and bytes <= total."""
    # chunk_index >= chunks_total rejected
    base = copy.deepcopy(canonical_events["transfer_progress"])
    base["details"] = dict(base["details"])
    base["details"]["chunk_index"] = 20
    base["details"]["chunks_total"] = 20
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base)

    # bytes_transferred_total > total_size_bytes rejected
    base2 = copy.deepcopy(canonical_events["transfer_progress"])
    base2["details"] = dict(base2["details"])
    base2["details"]["bytes_transferred_total"] = 20000
    base2["details"]["total_size_bytes"] = 10000
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base2)

def test_pydantic_p4_task_parameters_allowlist(canonical_events):
    """task_parameters must strictly match the action_label allowlist."""
    base = copy.deepcopy(canonical_events["task_started"])
    base["details"]["action_label"] = P4ActionLabelEnum.SIMULATE_PROCESS_ENUMERATION
    base["details"]["task_parameters"] = {
        "filter_system_procs": True,
        "max_results": 100
    }
    model = CommonEventEnvelope.model_validate(base)
    assert model.details.action_label == P4ActionLabelEnum.SIMULATE_PROCESS_ENUMERATION

    # Negative: unlisted key
    base_invalid = copy.deepcopy(canonical_events["task_started"])
    base_invalid["details"]["action_label"] = P4ActionLabelEnum.SIMULATE_PROCESS_ENUMERATION
    base_invalid["details"]["task_parameters"] = {
        "filter_system_procs": True,
        "max_results": 100,
        "unauthorized_command": "rm -rf"
    }
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base_invalid)

def test_pydantic_p7_timeout_expired_grace_period_validation(canonical_events):
    """P7 handshake_timeout requires grace_period_sec == 0; grace_period_expired requires > 0."""
    # Handshake timeout valid
    base_hs = copy.deepcopy(canonical_events["timeout_expired"])
    base_hs["correlation"]["entity_type"] = "session"
    base_hs["details"] = dict(base_hs["details"])
    base_hs["details"]["trigger_condition"] = "handshake_timeout"
    base_hs["details"]["grace_period_sec"] = 0.0
    model = CommonEventEnvelope.model_validate(base_hs)
    assert model.details.grace_period_sec == 0.0

    # Handshake timeout invalid with > 0
    base_hs_invalid = copy.deepcopy(base_hs)
    base_hs_invalid["details"] = dict(base_hs["details"])
    base_hs_invalid["details"]["grace_period_sec"] = 10.0
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base_hs_invalid)

    # Grace period expired invalid with 0
    base_gp = copy.deepcopy(canonical_events["timeout_expired"])
    base_gp["details"] = dict(base_gp["details"])
    base_gp["details"]["trigger_condition"] = "grace_period_expired"
    base_gp["details"]["grace_period_sec"] = 0.0
    with pytest.raises(ValidationError):
        CommonEventEnvelope.model_validate(base_gp)

def test_pydantic_serialization_roundtrip(canonical_events):
    """Verify JSON round-trip serialization."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    model1 = CommonEventEnvelope.model_validate(base)
    json_str = model1.model_dump_json()
    model2 = CommonEventEnvelope.model_validate_json(json_str)
    assert model1.event_id == model2.event_id
    assert model1.source == model2.source
