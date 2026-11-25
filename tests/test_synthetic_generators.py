"""
Unit tests for Synthetic Event Generators (P4 C2, P5 Shell, P6 Exfiltration).
Verifies strict schema compliance, synthetic safety flags, and scenario generators.
"""

from models.envelope import CommonEventEnvelope
from synthetic.p4_generator import P4C2Generator
from synthetic.p5_generator import P5ShellGenerator
from synthetic.p6_generator import P6ExfilGenerator
from synthetic.scenarios import generate_normal_scenario, generate_stalled_scenario


def test_p4_generator_emits_valid_envelopes():
    """Verify all P4 generator methods produce schema-compliant envelopes."""
    p4 = P4C2Generator(campaign_id="test-camp", run_id="run-01")
    agent_id = "agent-test-01"
    task_id = "task-test-01"

    ev1 = p4.register_agent(agent_id=agent_id, timeout_sec=20)
    model1 = CommonEventEnvelope.model_validate(ev1)
    assert model1.source == "p4_c2"
    assert model1.type == "agent_registered"
    assert model1.metadata.is_simulated is True
    assert model1.metadata.inferred is False

    ev2 = p4.beacon_checkin(agent_id=agent_id, counter=1)
    model2 = CommonEventEnvelope.model_validate(ev2)
    assert model2.type == "beacon_checkin"

    ev3 = p4.start_task(agent_id=agent_id, task_id=task_id)
    model3 = CommonEventEnvelope.model_validate(ev3)
    assert model3.type == "task_started"
    assert model3.correlation.parent_id == agent_id

    ev4 = p4.progress_task(agent_id=agent_id, task_id=task_id, progress_percent=50)
    model4 = CommonEventEnvelope.model_validate(ev4)
    assert model4.type == "task_progress"

    ev5 = p4.complete_task(agent_id=agent_id, task_id=task_id)
    model5 = CommonEventEnvelope.model_validate(ev5)
    assert model5.type == "task_completed"
    assert model5.status == "completed"


def test_p5_generator_emits_valid_envelopes():
    """Verify all P5 generator methods produce schema-compliant envelopes."""
    p5 = P5ShellGenerator(campaign_id="test-camp", run_id="run-01")
    session_id = "sess-test-01"

    ev1 = p5.request_connection(session_id=session_id)
    model1 = CommonEventEnvelope.model_validate(ev1)
    assert model1.source == "p5_shell"
    assert model1.type == "connection_requested"
    assert model1.status == "pending"

    ev2 = p5.establish_connection(session_id=session_id)
    model2 = CommonEventEnvelope.model_validate(ev2)
    assert model2.type == "connection_established"
    assert model2.status == "running"

    ev3 = p5.record_activity(session_id=session_id, command_count=1)
    model3 = CommonEventEnvelope.model_validate(ev3)
    assert model3.type == "session_activity"

    ev4 = p5.close_session(session_id=session_id)
    model4 = CommonEventEnvelope.model_validate(ev4)
    assert model4.type == "session_closed"
    assert model4.status == "completed"


def test_p6_generator_emits_valid_envelopes():
    """Verify all P6 generator methods produce schema-compliant envelopes."""
    p6 = P6ExfilGenerator(campaign_id="test-camp", run_id="run-01")
    transfer_id = "xfer-test-01"

    ev1 = p6.start_transfer(transfer_id=transfer_id, total_size=2000, chunk_size=1000)
    model1 = CommonEventEnvelope.model_validate(ev1)
    assert model1.source == "p6_exfil"
    assert model1.type == "transfer_started"
    assert model1.status == "running"

    ev2 = p6.progress_transfer(
        transfer_id=transfer_id,
        chunk_index=0,
        chunks_total=2,
        bytes_transferred_total=1000,
        total_size=2000,
    )
    model2 = CommonEventEnvelope.model_validate(ev2)
    assert model2.type == "transfer_progress"

    ev3 = p6.complete_transfer(transfer_id=transfer_id, total_size=2000, chunks_total=2)
    model3 = CommonEventEnvelope.model_validate(ev3)
    assert model3.type == "transfer_completed"
    assert model3.status == "completed"


def test_scenarios_generate_fully_valid_streams():
    """Verify pre-packaged scenarios generate completely valid event sequences."""
    normal_events = generate_normal_scenario(campaign_id="camp-norm", run_id="run-01")
    assert len(normal_events) >= 8
    for raw in normal_events:
        model = CommonEventEnvelope.model_validate(raw)
        assert model.metadata.is_simulated is True
        assert model.source in ("p4_c2", "p5_shell", "p6_exfil")

    stalled_events = generate_stalled_scenario(campaign_id="camp-stall", run_id="run-01")
    assert len(stalled_events) == 3
    for raw in stalled_events:
        model = CommonEventEnvelope.model_validate(raw)
        assert model.timeout_sec == 1
