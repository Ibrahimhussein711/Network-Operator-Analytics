import copy
import pytest
import jsonschema

def test_canonical_events_validity(schema_validator, canonical_events):
    """Test that all 20 canonical valid events pass JSON Schema Draft 2020-12 validation."""
    for event_name, payload in canonical_events.items():
        try:
            schema_validator.validate(payload)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Canonical event '{event_name}' failed JSON Schema validation: {e.message}")

def test_missing_required_fields(schema_validator, canonical_events):
    """Assert rejection when required root envelope fields are missing."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    del base["event_id"]
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

    base = copy.deepcopy(canonical_events["agent_registered"])
    del base["campaign_id"]
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_invalid_uuid_format(schema_validator, canonical_events):
    """Assert rejection for malformed UUIDv4 strings."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    base["event_id"] = "not-a-valid-uuid"
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_invalid_timestamp_format(schema_validator, canonical_events):
    """Assert rejection for non-UTC or non-ISO8601 timestamps."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    base["ts"] = "2026-11-24 12:00:00"  # missing T and Z
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_host_missing_ip_and_hostname(schema_validator, canonical_events):
    """Host endpoint must have at least one of ip or hostname."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    base["host"]["ip"] = None
    base["host"]["hostname"] = None
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_destination_icmp_with_port_rejected(schema_validator, canonical_events):
    """Destination endpoint with protocol icmp cannot declare a transport port."""
    base = copy.deepcopy(canonical_events["transfer_started"])
    base["destination"]["protocol"] = "icmp"
    base["destination"]["port"] = 80
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_source_type_mismatch(schema_validator, canonical_events):
    """Assert rejection when source and type do not match."""
    base = copy.deepcopy(canonical_events["agent_registered"])
    base["source"] = "p5_shell"  # agent_registered is p4_c2
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_type_status_mismatch(schema_validator, canonical_events):
    """Assert rejection when type and status do not match canonical lifecycle mapping."""
    base = copy.deepcopy(canonical_events["task_started"])
    base["status"] = "completed"  # task_started must be running
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_initiation_timeout_sec_mandatory(schema_validator, canonical_events):
    """Initiation events must have a positive timeout_sec."""
    for ev in ["agent_registered", "task_started", "connection_requested", "connection_established", "transfer_started"]:
        base = copy.deepcopy(canonical_events[ev])
        base["timeout_sec"] = None
        with pytest.raises(jsonschema.ValidationError):
            schema_validator.validate(base)

def test_p4_executor_safety_allowlist(schema_validator, canonical_events):
    """Reject real shell executor strings like bash, cmd, powershell."""
    base = copy.deepcopy(canonical_events["task_started"])
    base["details"]["executor"] = "bash"  # must be simulated_posix, simulated_windows, internal_simulator
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_p4_action_label_allowlist(schema_validator, canonical_events):
    """Reject unlisted action_label in P4 task_started."""
    base = copy.deepcopy(canonical_events["task_started"])
    base["details"]["action_label"] = "execute_arbitrary_code"
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_p4_network_discovery_synthetic_scope(schema_validator, canonical_events):
    """simulate_network_discovery must use synthetic scopes and simulated probe methods."""
    base = copy.deepcopy(canonical_events["task_started"])
    base["details"]["action_label"] = "simulate_network_discovery"
    base["details"]["task_parameters"] = {
        "simulation_scope": "synthetic_lab_segment_01",
        "discovery_method": "simulated_tcp_probe"
    }
    schema_validator.validate(base)

    # Negative: real subnet string
    base["details"]["task_parameters"] = {
        "simulation_scope": "192.168.1.0/24",
        "discovery_method": "simulated_tcp_probe"
    }
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_p5_missing_shell_environment(schema_validator, canonical_events):
    """P5 shell events must declare shell_environment."""
    base = copy.deepcopy(canonical_events["session_activity"])
    del base["details"]["shell_environment"]
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_p5_command_label_allowlist(schema_validator, canonical_events):
    """Reject unlisted command labels in P5 session_activity."""
    base = copy.deepcopy(canonical_events["session_activity"])
    base["details"]["command_label"] = "rm -rf /"
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_p7_provenance_constraints(schema_validator, canonical_events):
    """P7 events must have inferred == True; simulators must have inferred == False."""
    base_p7 = copy.deepcopy(canonical_events["beacon_missed"])
    base_p7["metadata"]["inferred"] = False
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base_p7)

    base_p4 = copy.deepcopy(canonical_events["agent_registered"])
    base_p4["metadata"]["inferred"] = True
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base_p4)

def test_p7_stalled_trigger_mismatch(schema_validator, canonical_events):
    """Reject mismatched trigger_condition for stalled events."""
    base = copy.deepcopy(canonical_events["beacon_missed"])
    base["details"]["trigger_condition"] = "task_progress_timeout"
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)

def test_p7_timeout_expired_grace_period_rules(schema_validator, canonical_events):
    """handshake_timeout requires grace_period_sec == 0; grace_period_expired requires > 0."""
    # Valid handshake_timeout
    base_hs = copy.deepcopy(canonical_events["timeout_expired"])
    base_hs["correlation"]["entity_type"] = "session"
    base_hs["details"]["trigger_condition"] = "handshake_timeout"
    base_hs["details"]["grace_period_sec"] = 0
    schema_validator.validate(base_hs)

    # Invalid: handshake_timeout with grace_period_sec > 0
    base_hs["details"]["grace_period_sec"] = 15
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base_hs)

    # Invalid: grace_period_expired with grace_period_sec == 0
    base_gp = copy.deepcopy(canonical_events["timeout_expired"])
    base_gp["details"]["trigger_condition"] = "grace_period_expired"
    base_gp["details"]["grace_period_sec"] = 0
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base_gp)

def test_bytes_transferred_delta_non_negative(schema_validator, canonical_events):
    """bytes_transferred_delta must be >= 0 when provided."""
    base = copy.deepcopy(canonical_events["beacon_checkin"])
    base["bytes_transferred_delta"] = -10
    with pytest.raises(jsonschema.ValidationError):
        schema_validator.validate(base)
