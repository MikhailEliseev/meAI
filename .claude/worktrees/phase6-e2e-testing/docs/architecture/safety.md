# Safety Mechanisms Architecture

> Loop detection, timeouts, context monitoring

## Safety Components

### 1. Loop Detector
**Purpose:** Prevent infinite delegation chains

**How it works:**
- Tracks delegation depth
- Max depth: 5 levels
- Detects circular calls
- Prevents self-delegation

**Example:**
```
operator → seo-agent → content-agent → ... (max 5 levels)
```

### 2. Timeout Manager
**Purpose:** Prevent operations from running forever

**How it works:**
- Default timeout: 5 minutes
- Custom timeouts per operation
- Graceful cancellation
- Active operation tracking

### 3. Context Monitor
**Purpose:** Enforce 40% rule for context usage

**How it works:**
- Tracks token usage
- Warning at 40% (80,000 tokens)
- Critical at 80% (160,000 tokens)
- Recommends compaction

### 4. Shutdown Handler
**Purpose:** Graceful cleanup on exit

**How it works:**
- Catches SIGINT/SIGTERM
- Runs cleanup callbacks
- Saves state
- Closes connections

## Safety Flow

```
Operation Start
    ↓
Check Loop Depth → Reject if > 5
    ↓
Check Context → Compact if > 40%
    ↓
Start Timeout Timer
    ↓
Execute Operation
    ↓
Cancel Timeout
    ↓
Update Metrics
```

## Configuration

```python
# Loop detection
loop_detector = LoopDetector(max_depth=5)

# Timeouts
timeout_manager = TimeoutManager(default_timeout=300)

# Context monitoring
context_monitor = ContextMonitor(
    max_tokens=200000,
    warning_threshold=0.4
)
```

## See Also

- [Safety API](../api/safety.md)
- [Orchestrator API](../api/orchestrator.md)
