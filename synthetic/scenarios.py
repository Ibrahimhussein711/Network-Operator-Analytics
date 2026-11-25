"""
Pre-packaged operational scenarios for testing and demonstrating Project 07.
Generates correlated event streams modeling real red-team operational campaigns.
"""

from typing import Any, Dict, List
from uuid import uuid4

from .p4_generator import P4C2Generator
from .p5_generator import P5ShellGenerator
from .p6_generator import P6ExfilGenerator


def generate_normal_scenario(
    campaign_id: str = "campaign-demo-normal",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    1. Normal Run: Complete, healthy red-team campaign run incorporating
    P4 (C2), P5 (Interactive Shell), and P6 (Covert Exfiltration).
    All entities transition cleanly to completion.
    """
    p4 = P4C2Generator(campaign_id=campaign_id, run_id=run_id)
    p5 = P5ShellGenerator(campaign_id=campaign_id, run_id=run_id)
    p6 = P6ExfilGenerator(campaign_id=campaign_id, run_id=run_id)

    agent_id = f"agent-c2-{uuid4().hex[:6]}"
    task_id = f"task-inv-{uuid4().hex[:6]}"
    session_id = f"sess-sh-{uuid4().hex[:6]}"
    transfer_id = f"xfer-dns-{uuid4().hex[:6]}"

    events: List[Dict[str, Any]] = []

    # P4 Agent Registration & Checkin
    events.append(p4.register_agent(agent_id=agent_id, timeout_sec=60))
    events.append(p4.beacon_checkin(agent_id=agent_id, counter=1, latency_ms=28))

    # P5 Interactive Shell requested & established
    events.append(p5.request_connection(session_id=session_id, parent_id=agent_id, timeout_sec=30))
    events.append(p5.establish_connection(session_id=session_id, parent_id=agent_id, timeout_sec=60))
    events.append(p5.record_activity(session_id=session_id, command_count=1, uptime_sec=5, parent_id=agent_id))

    # P4 Task started, progressed, and completed
    events.append(p4.start_task(agent_id=agent_id, task_id=task_id, timeout_sec=60))
    events.append(p4.progress_task(agent_id=agent_id, task_id=task_id, progress_percent=50, bytes_delta=1024))
    events.append(p4.complete_task(agent_id=agent_id, task_id=task_id, duration_ms=1800, output_bytes=2048))

    # P6 Covert DNS Exfiltration started, progressed, and completed
    events.append(p6.start_transfer(transfer_id=transfer_id, total_size=3000, chunk_size=1000, parent_id=agent_id, timeout_sec=45))
    events.append(p6.progress_transfer(
        transfer_id=transfer_id,
        chunk_index=0,
        chunks_total=3,
        bytes_transferred_total=1000,
        total_size=3000,
        bytes_delta=1000,
        parent_id=agent_id,
    ))
    events.append(p6.progress_transfer(
        transfer_id=transfer_id,
        chunk_index=1,
        chunks_total=3,
        bytes_transferred_total=2000,
        total_size=3000,
        bytes_delta=1000,
        parent_id=agent_id,
    ))
    events.append(p6.complete_transfer(
        transfer_id=transfer_id,
        total_size=3000,
        chunks_total=3,
        duration_sec=8.4,
        parent_id=agent_id,
    ))

    # Close session
    events.append(p5.close_session(session_id=session_id, total_duration_sec=25, total_commands=1, parent_id=agent_id))

    return events


def generate_agent_stalled_scenario(
    campaign_id: str = "campaign-demo-agent-stall",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    2. Agent Stalled Scenario: Agent registered with a short heartbeat timeout
    and fails to check in, triggering beacon_missed watchdog event.
    """
    p4 = P4C2Generator(campaign_id=campaign_id, run_id=run_id)
    agent_id = f"agent-stall-{uuid4().hex[:6]}"
    return [
        p4.register_agent(agent_id=agent_id, timeout_sec=1),
    ]


def generate_task_stalled_scenario(
    campaign_id: str = "campaign-demo-task-stall",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    3. Task Stalled Scenario: Task started under an agent with 1s timeout
    and no progress is emitted, triggering task_stalled.
    """
    p4 = P4C2Generator(campaign_id=campaign_id, run_id=run_id)
    agent_id = f"agent-parent-{uuid4().hex[:6]}"
    task_id = f"task-stall-{uuid4().hex[:6]}"
    return [
        p4.register_agent(agent_id=agent_id, timeout_sec=60),
        p4.start_task(agent_id=agent_id, task_id=task_id, timeout_sec=1),
    ]


def generate_session_handshake_timeout_scenario(
    campaign_id: str = "campaign-demo-handshake-to",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    4. Session Handshake Timeout Scenario: Connection requested with 1s timeout
    and never established. Watchdog directly produces timeout_expired (grace=0).
    """
    p5 = P5ShellGenerator(campaign_id=campaign_id, run_id=run_id)
    session_id = f"sess-hs-{uuid4().hex[:6]}"
    return [
        p5.request_connection(session_id=session_id, timeout_sec=1),
    ]


def generate_established_session_stalled_scenario(
    campaign_id: str = "campaign-demo-session-stall",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    5. Established Session Stalled Scenario: Shell requested and established with 1s idle timeout.
    No further activity sent, triggering session_stalled.
    """
    p5 = P5ShellGenerator(campaign_id=campaign_id, run_id=run_id)
    session_id = f"sess-est-{uuid4().hex[:6]}"
    return [
        p5.request_connection(session_id=session_id, timeout_sec=30),
        p5.establish_connection(session_id=session_id, timeout_sec=1),
    ]


def generate_transfer_stalled_scenario(
    campaign_id: str = "campaign-demo-xfer-stall",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    6. Transfer Stalled Scenario: Chunked transfer started with 1s timeout.
    No subsequent chunks sent, triggering transfer_stalled.
    """
    p6 = P6ExfilGenerator(campaign_id=campaign_id, run_id=run_id)
    transfer_id = f"xfer-stall-{uuid4().hex[:6]}"
    return [
        p6.start_transfer(transfer_id=transfer_id, total_size=5000, chunk_size=1000, timeout_sec=1),
    ]


def generate_mixed_campaign_scenario(
    campaign_id: str = "campaign-demo-mixed",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    7. Mixed Campaign: Contains a mix of successful operations and stalled/failing entities
    across multiple sources to demonstrate concurrent operational intelligence.
    """
    events: List[Dict[str, Any]] = []
    # 1. Healthy C2 + Shell
    events.extend(generate_normal_scenario(campaign_id=campaign_id, run_id=run_id))
    # 2. Stalled Agent
    events.extend(generate_agent_stalled_scenario(campaign_id=campaign_id, run_id=run_id))
    # 3. Handshake Timeout Session
    events.extend(generate_session_handshake_timeout_scenario(campaign_id=campaign_id, run_id=run_id))
    # 4. Stalled Transfer
    events.extend(generate_transfer_stalled_scenario(campaign_id=campaign_id, run_id=run_id))
    return events


def generate_stalled_scenario(
    campaign_id: str = "campaign-demo-stall",
    run_id: str = "run-01",
) -> List[Dict[str, Any]]:
    """
    Standard stalled scenario: generates 3 entities configured with timeout_sec=1:
    - 1 P4 Agent registered
    - 1 P4 Task started
    - 1 P5 Shell connection requested
    """
    p4 = P4C2Generator(campaign_id=campaign_id, run_id=run_id)
    p5 = P5ShellGenerator(campaign_id=campaign_id, run_id=run_id)
    stalled_agent_id = f"agent-stall-{uuid4().hex[:6]}"
    stalled_task_id = f"task-stall-{uuid4().hex[:6]}"
    unestablished_session_id = f"sess-unest-{uuid4().hex[:6]}"
    return [
        p4.register_agent(agent_id=stalled_agent_id, timeout_sec=1),
        p4.start_task(agent_id=stalled_agent_id, task_id=stalled_task_id, timeout_sec=1),
        p5.request_connection(session_id=unestablished_session_id, timeout_sec=1),
    ]
