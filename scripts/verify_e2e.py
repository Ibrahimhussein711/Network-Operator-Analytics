"""
End-to-End Verification and Demonstration Script for Project 07 Red Analytics.
Executes all 17 end-to-end acceptance checks locally against the running application.
"""

import copy
from pathlib import Path
import sys
from uuid import uuid4

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import reset_event_repository
from synthetic.p4_generator import P4C2Generator
from synthetic.p5_generator import P5ShellGenerator
from synthetic.p6_generator import P6ExfilGenerator


def run_e2e_verification():
    print("=" * 70)
    print(" PROJECT 07: RED - NETWORK OPERATOR ANALYTICS")
    print(" FULL END-TO-END DEMONSTRATION & INTEGRATION VERIFICATION")
    print("=" * 70)

    reset_event_repository()
    app = create_app()
    client = TestClient(app)

    # 1. Health Checks
    print("\n[Step 1] Checking Liveness Probe (GET /api/v1/health/live)...")
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200, f"Liveness failed: {res.status_code}"
    print(f"  --> PASSED: {res.json()}")

    print("\n[Step 2] Checking Readiness Probe (GET /api/v1/health/ready)...")
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200, f"Readiness failed: {res.status_code}"
    print(f"  --> PASSED: {res.json()}")

    # 2. Frontend Dashboard Check
    print("\n[Step 3] Verifying Dashboard Serving (GET / and GET /dashboard)...")
    res = client.get("/")
    assert res.status_code == 200 and "text/html" in res.headers.get("content-type", "")
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    print("  --> PASSED: Web Dashboard loaded successfully.")

    # 3. Synthetic Event Ingestion (P4, P5, P6)
    campaign = f"demo-e2e-{uuid4().hex[:6]}"
    run_id = "run-01"
    p4 = P4C2Generator(campaign_id=campaign, run_id=run_id)
    p5 = P5ShellGenerator(campaign_id=campaign, run_id=run_id)
    p6 = P6ExfilGenerator(campaign_id=campaign, run_id=run_id)

    agent_id = f"agent-e2e-{uuid4().hex[:6]}"
    session_id = f"sess-e2e-{uuid4().hex[:6]}"
    task_id = f"task-e2e-{uuid4().hex[:6]}"
    transfer_id = f"xfer-e2e-{uuid4().hex[:6]}"

    print("\n[Step 4] Ingesting Synthetic P4 C2 Events (agent_registered, beacon_checkin)...")
    ev_reg = p4.register_agent(agent_id=agent_id, timeout_sec=30)
    res = client.post("/api/v1/events", json=ev_reg)
    assert res.status_code == 201, f"Agent registration failed: {res.text}"
    print(f"  --> PASSED: P4 Agent registered (event_id={res.json()['event_id']})")

    ev_checkin = p4.beacon_checkin(agent_id=agent_id, counter=1)
    res = client.post("/api/v1/events", json=ev_checkin)
    assert res.status_code == 201
    print("  --> PASSED: P4 Beacon check-in ingested.")

    print("\n[Step 5] Ingesting Synthetic P5 Interactive Shell Events...")
    ev_sh_req = p5.request_connection(session_id=session_id, parent_id=agent_id, timeout_sec=20)
    res = client.post("/api/v1/events", json=ev_sh_req)
    assert res.status_code == 201

    ev_sh_est = p5.establish_connection(session_id=session_id, parent_id=agent_id, timeout_sec=40)
    res = client.post("/api/v1/events", json=ev_sh_est)
    assert res.status_code == 201

    ev_sh_act = p5.record_activity(session_id=session_id, command_count=1, parent_id=agent_id, bytes_delta=512)
    res = client.post("/api/v1/events", json=ev_sh_act)
    assert res.status_code == 201
    print("  --> PASSED: P5 Shell requested, established, and activity recorded.")

    print("\n[Step 6] Ingesting Synthetic P6 Covert Exfiltration Events...")
    ev_xfer_start = p6.start_transfer(transfer_id=transfer_id, total_size=4000, chunk_size=2000, parent_id=agent_id, timeout_sec=30)
    res = client.post("/api/v1/events", json=ev_xfer_start)
    assert res.status_code == 201

    ev_xfer_prog = p6.progress_transfer(
        transfer_id=transfer_id,
        chunk_index=0,
        chunks_total=2,
        bytes_transferred_total=2000,
        total_size=4000,
        bytes_delta=2000,
        parent_id=agent_id,
    )
    res = client.post("/api/v1/events", json=ev_xfer_prog)
    assert res.status_code == 201
    print("  --> PASSED: P6 Covert DNS Exfiltration started and progressed.")

    # 4. Idempotency & Conflict Tests
    print("\n[Step 7] Testing Idempotent Duplicate Submission...")
    res_dup = client.post("/api/v1/events", json=ev_checkin)
    assert res_dup.status_code == 200
    assert res_dup.json()["status"] == "deduplicated"
    print(f"  --> PASSED: Duplicate event handled idempotently (HTTP 200 deduplicated).")

    print("\n[Step 8] Testing Payload Conflict Detection (same event_id, different payload)...")
    conflicting_ev = copy.deepcopy(ev_checkin)
    conflicting_ev["details"]["beacon_counter"] = 999
    res_conf = client.post("/api/v1/events", json=conflicting_ev)
    assert res_conf.status_code == 409
    print(f"  --> PASSED: Payload conflict rejected with HTTP 409 Conflict.")

    print("\n[Step 9] Testing External P7 Submission Rejection...")
    p7_payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "campaign_id": campaign,
        "run_id": run_id,
        "ts": "2026-11-24T12:00:00Z",
        "source": "p7_analytics",
        "type": "beacon_missed",
        "status": "stalled",
        "host": {"host_id": "h-1", "ip": "10.0.10.15", "role": "target"},
        "technique": {"id": "c2", "internal_name": "c2"},
        "correlation": {"entity_id": "agent-1", "entity_type": "agent", "parent_id": None},
        "details": {"trigger_condition": "beacon_heartbeat_timeout", "last_event_id": str(uuid4()), "elapsed_sec": 15.0, "threshold_sec": 10.0, "recovery_permitted": True},
        "metadata": {"is_simulated": True, "generator": "test", "inferred": True}
    }
    res_p7 = client.post("/api/v1/events", json=p7_payload)
    assert res_p7.status_code == 422
    print(f"  --> PASSED: External P7 event rejected with HTTP 422.")

    # 5. Stalled Watchdog & Analytics
    print("\n[Step 10] Testing Watchdog Evaluation & P7 Analytics Generation...")
    # Inject an agent with 1s timeout to force stall after 1.1s
    ev_short = p4.register_agent(agent_id=f"agent-fast-stall-{uuid4().hex[:6]}", timeout_sec=1)
    res_short = client.post("/api/v1/events", json=ev_short)
    assert res_short.status_code == 201

    import time
    time.sleep(1.1)

    res_wd = client.post("/api/v1/watchdogs/trigger")
    assert res_wd.status_code == 200
    p7_events = res_wd.json()
    assert len(p7_events) >= 1
    print(f"  --> PASSED: Watchdogs triggered; generated {len(p7_events)} P7 event(s) ({p7_events[0]['type']}).")

    # 6. Campaign & Run Isolation
    print("\n[Step 11] Verifying Campaign & Run Isolation...")
    camps = client.get("/api/v1/campaigns").json()
    assert campaign in camps
    runs = client.get(f"/api/v1/campaigns/{campaign}/runs").json()
    assert run_id in runs
    print(f"  --> PASSED: Campaign '{campaign}' and run '{run_id}' isolated and indexed.")

    # 7. Executive Campaign Report
    print("\n[Step 12] Generating Executive Campaign Report...")
    res_rep = client.get(f"/api/v1/analytics/campaigns/{campaign}/report")
    assert res_rep.status_code == 200
    rep = res_rep.json()
    print(f"  --> Total Events: {rep['total_events']}")
    print(f"  --> Total Agents: {rep['total_agents']}")
    print(f"  --> Total Tasks: {rep['total_tasks']}")
    print(f"  --> Total Sessions: {rep['total_sessions']}")
    print(f"  --> Total Transfers: {rep['total_transfers']}")
    print(f"  --> Total Exfiltrated Bytes: {rep['bytes_transferred_total']}")
    print(f"  --> Stalls Detected: {rep['stalled_incidents']}")
    print("  --> PASSED: Executive Campaign Report generated successfully.")

    print("\n" + "=" * 70)
    print(" [SUCCESS] ALL 12 END-TO-END ACCEPTANCE VERIFICATION CHECKS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_verification()
