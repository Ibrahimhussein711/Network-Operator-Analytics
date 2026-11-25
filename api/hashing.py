import hashlib
import json
from models.envelope import CommonEventEnvelope

def compute_canonical_payload_hash(event: CommonEventEnvelope) -> str:
    """
    Computes a deterministic SHA-256 hash over the canonical JSON representation
    of a validated CommonEventEnvelope.

    Invariants:
    1. Excludes 'received_at' so network retry timing does not alter the hash.
    2. Uses model_dump(mode="json") to serialize enums, UUIDs, and ISO-8601 timestamps
       into standard JSON primitives.
    3. Preserves explicit null values (exclude_none=False).
    4. Enforces sorted keys (sort_keys=True) and minimal compact separators (",", ":")
       so formatting/whitespace and key order differences do not affect the digest.
    5. Leaves the input event instance completely unmutated.
    6. Returns a 64-character lowercase hexadecimal SHA-256 digest string.
    """
    data = event.model_dump(
        mode="json",
        exclude={"received_at"}
    )
    canonical_bytes = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()
