import copy
import concurrent.futures
from datetime import datetime, timezone
import pytest
from uuid import uuid4

from models.envelope import CommonEventEnvelope
from api.storage.interface import IngestionResultStatus
from api.storage.memory import ThreadSafeInMemoryEventRepository

@pytest.fixture
def memory_repo():
    return ThreadSafeInMemoryEventRepository()

@pytest.fixture
def sample_event(canonical_events):
    raw = copy.deepcopy(canonical_events["agent_registered"])
    raw["received_at"] = datetime.now(timezone.utc)
    return CommonEventEnvelope.model_validate(raw)

def test_new_event_returns_created(memory_repo, sample_event):
    """1. New event returns CREATED."""
    outcome = memory_repo.save_if_absent(sample_event, "hash-aaa-111")
    assert outcome.status == IngestionResultStatus.CREATED
    assert outcome.stored_event.event_id == sample_event.event_id
    assert memory_repo.count() == 1

def test_same_event_and_same_hash_returns_duplicate(memory_repo, sample_event):
    """2. Same event and same hash returns DUPLICATE."""
    outcome1 = memory_repo.save_if_absent(sample_event, "hash-aaa-111")
    assert outcome1.status == IngestionResultStatus.CREATED

    outcome2 = memory_repo.save_if_absent(sample_event, "hash-aaa-111")
    assert outcome2.status == IngestionResultStatus.DUPLICATE
    assert outcome2.stored_event.event_id == sample_event.event_id
    assert memory_repo.count() == 1

def test_same_event_id_with_different_hash_returns_conflict(memory_repo, sample_event):
    """3. Same event ID with different hash returns CONFLICT."""
    outcome1 = memory_repo.save_if_absent(sample_event, "hash-original")
    assert outcome1.status == IngestionResultStatus.CREATED

    # Conflicting payload with different hash
    outcome2 = memory_repo.save_if_absent(sample_event, "hash-mutated-conflict")
    assert outcome2.status == IngestionResultStatus.CONFLICT
    assert outcome2.stored_event.event_id == sample_event.event_id
    assert memory_repo.count() == 1

def test_original_record_remains_unchanged_after_duplicate(memory_repo, sample_event):
    """4. Original record remains unchanged after duplicate."""
    outcome1 = memory_repo.save_if_absent(sample_event, "hash-1")
    original_recv_at = outcome1.stored_event.received_at

    # Attempt duplicate with mutated incoming object
    mutated_event = copy.deepcopy(sample_event)
    mutated_event.campaign_id = "altered-campaign-should-not-persist"
    outcome2 = memory_repo.save_if_absent(mutated_event, "hash-1")

    assert outcome2.status == IngestionResultStatus.DUPLICATE
    stored = memory_repo.get_by_id(sample_event.event_id)
    assert stored.campaign_id == sample_event.campaign_id
    assert stored.received_at == original_recv_at

def test_original_record_remains_unchanged_after_conflict(memory_repo, sample_event):
    """5. Original record remains unchanged after conflict."""
    memory_repo.save_if_absent(sample_event, "hash-original")

    mutated_event = copy.deepcopy(sample_event)
    mutated_event.campaign_id = "conflict-campaign"
    outcome = memory_repo.save_if_absent(mutated_event, "hash-different")

    assert outcome.status == IngestionResultStatus.CONFLICT
    stored = memory_repo.get_by_id(sample_event.event_id)
    assert stored.campaign_id == sample_event.campaign_id

def test_original_received_at_is_preserved(memory_repo, sample_event):
    """6. Original received_at is preserved."""
    outcome1 = memory_repo.save_if_absent(sample_event, "hash-1")
    t1 = outcome1.stored_event.received_at

    # Second submission with a different received_at
    newer_event = copy.deepcopy(sample_event)
    newer_event.received_at = datetime.now(timezone.utc)
    outcome2 = memory_repo.save_if_absent(newer_event, "hash-1")

    assert outcome2.status == IngestionResultStatus.DUPLICATE
    assert outcome2.stored_event.received_at == t1

def test_get_by_id_returns_correct_event(memory_repo, sample_event):
    """7. get_by_id returns the correct event."""
    assert memory_repo.get_by_id(sample_event.event_id) is None
    memory_repo.save_if_absent(sample_event, "hash-1")
    retrieved = memory_repo.get_by_id(sample_event.event_id)
    assert retrieved is not None
    assert retrieved.event_id == sample_event.event_id

def test_count_returns_correct_number(memory_repo, sample_event):
    """8. count returns the correct number."""
    assert memory_repo.count() == 0
    memory_repo.save_if_absent(sample_event, "hash-1")
    assert memory_repo.count() == 1

def test_is_healthy_returns_true(memory_repo):
    """9. is_healthy returns True for the functioning memory repository."""
    assert memory_repo.is_healthy() is True
    memory_repo.set_healthy(False)
    assert memory_repo.is_healthy() is False

def test_concurrent_identical_submissions(memory_repo, sample_event):
    """
    10. Concurrent identical submissions:
        - 10 threads submit the same event_id.
        - Exactly one CREATED.
        - Nine DUPLICATE.
        - Exactly one stored event.
        - Exactly one associated hash.
        - No corrupted or overwritten record.
    """
    results = []

    def submit():
        # Clone sample_event for each thread
        cloned = copy.deepcopy(sample_event)
        outcome = memory_repo.save_if_absent(cloned, "concurrent-hash-999")
        return outcome.status

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(submit) for _ in range(10)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    created_count = results.count(IngestionResultStatus.CREATED)
    duplicate_count = results.count(IngestionResultStatus.DUPLICATE)

    assert created_count == 1, f"Expected exactly 1 CREATED, got {created_count}"
    assert duplicate_count == 9, f"Expected exactly 9 DUPLICATE, got {duplicate_count}"
    assert memory_repo.count() == 1
    assert memory_repo._hashes[sample_event.event_id] == "concurrent-hash-999"

def test_mutating_returned_event_does_not_mutate_stored_data(memory_repo, sample_event):
    """11. Mutating a returned event must not mutate stored data."""
    outcome = memory_repo.save_if_absent(sample_event, "hash-1")
    returned_event = outcome.stored_event

    # Caller attempts to mutate returned Pydantic object
    returned_event.campaign_id = "mutated-by-caller"

    # Repository stored instance must remain pristine
    stored_event = memory_repo.get_by_id(sample_event.event_id)
    assert stored_event.campaign_id == sample_event.campaign_id

    # Caller attempts to mutate get_by_id returned object
    stored_event.campaign_id = "mutated-second-caller"
    fresh_lookup = memory_repo.get_by_id(sample_event.event_id)
    assert fresh_lookup.campaign_id == sample_event.campaign_id
