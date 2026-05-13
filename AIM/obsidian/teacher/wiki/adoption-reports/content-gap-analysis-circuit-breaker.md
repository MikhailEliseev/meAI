# Skill Adoption Report: Circuit Breaker

**Status:** ✅ SUCCESS
**Date:** 2026-05-13 21:03:09

## Skill Metadata

- **Name:** Circuit Breaker
- **Source:** https://github.com/High-Functioning-Solutions/hfs-location-client
- **Quality Score:** 85.0/100
- **Description:** Prevents cascading failures by stopping requests to failing services

## Adoption Details

### Files Created

- `/Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/src/aim/subagents/content_gap_analysis/_sync_circuit_breaker.py`

### Dependencies Added

- `CircuitOpenError`
- `hfs_location_client`

### Code Adaptation

✅ Code was successfully adapted to project structure

### Integration Report

# Adoption Report: Circuit Breaker

**Source:** https://github.com/High-Functioning-Solutions/hfs-location-client

**Quality Score:** 85.0/100


## Files Created

- `/Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/src/aim/subagents/content_gap_analysis/_sync_circuit_breaker.py`

## Dependencies Added

- `CircuitOpenError`
- `hfs_location_client`

## Integration Instructions

# Integration: Circuit Breaker

**Source:** https://github.com/High-Functioning-Solutions/hfs-location-client

**Description:** Prevents cascading failures by stopping requests to failing services


## 1. Install Dependencies

Add to `requirements.txt`:

```
CircuitOpenError>=1.0.0  # Circuit Breaker
hfs_location_client>=1.0.0  # Circuit Breaker
```

Install:

```bash
pip install CircuitOpenError hfs_location_client
```


## 2. Integration Steps

1. Add code to `/Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/src/aim/subagents/content_gap_analysis`

2. Adapt imports to project structure

3. Update configuration if needed

4. Add tests for new functionality


## 4. Usage

```python
# Example usage:
cuitState
from hfs_location_client.exceptions import CircuitOpenError

T = TypeVar("T")


class SyncCircuitBreaker:
    """Thread-safe synchronous circuit breaker."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time:
```


## Next Steps

1. Review adopted code
2. Install dependencies: `pip install CircuitOpenError hfs_location_client`
3. Run tests to verify integration
4. Update documentation
