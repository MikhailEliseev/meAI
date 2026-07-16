"""Loop detection - prevent infinite delegation chains"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import structlog

logger = structlog.get_logger()


class LoopDetector:
    """Detect and prevent infinite loops in agent delegation"""

    def __init__(self, max_depth: int = 5, max_self_calls: int = 3):
        """Initialize Loop Detector

        Args:
            max_depth: Maximum delegation depth allowed
            max_self_calls: Maximum number of self-calls allowed
        """
        self.max_depth = max_depth
        self.max_self_calls = max_self_calls

        # Track delegation chains
        self.chains: dict[str, list[str]] = {}

        # Track self-calls per agent
        self.self_calls: dict[str, int] = defaultdict(int)

        # Track call timestamps for cleanup
        self.timestamps: dict[str, datetime] = {}

    def track_delegation(self, from_agent: str, to_agent: str) -> None:
        """Track delegation and check for loops

        Args:
            from_agent: Agent delegating the task
            to_agent: Agent receiving the task

        Raises:
            RuntimeError: If max depth exceeded, circular delegation, or too many self-calls
        """

        # Initialize chain if not exists
        if from_agent not in self.chains:
            self.chains[from_agent] = [from_agent]

        # Check for self-call (special case - don't check circular for self-calls)
        if from_agent == to_agent:
            self.self_calls[from_agent] += 1

            if self.self_calls[from_agent] > self.max_self_calls:
                logger.error(
                    "loop.self_call_exceeded",
                    agent=from_agent,
                    count=self.self_calls[from_agent],
                )
                raise RuntimeError(
                    f"Agent {from_agent} called itself {self.self_calls[from_agent]} times"
                )
            # For self-calls, don't update chain - just track count
            return

        # Build chain for to_agent
        chain = self.chains[from_agent] + [to_agent]

        # Check depth (use >= to catch at the limit)
        if len(chain) > self.max_depth:
            logger.error(
                "loop.depth_exceeded",
                chain=chain,
                depth=len(chain),
            )
            raise RuntimeError(
                f"Max delegation depth {self.max_depth} exceeded: {' -> '.join(chain)}"
            )

        # Check for circular delegation
        if to_agent in self.chains[from_agent]:
            logger.error(
                "loop.circular_detected",
                chain=chain,
            )
            raise RuntimeError(
                f"Circular delegation detected: {' -> '.join(chain)}"
            )

        # Update chain
        self.chains[to_agent] = chain
        self.timestamps[to_agent] = datetime.now(timezone.utc)

        logger.debug(
            "loop.delegation_tracked",
            from_agent=from_agent,
            to_agent=to_agent,
            depth=len(chain),
        )

    def reset_agent(self, agent_id: str) -> None:
        """Reset tracking for an agent

        Args:
            agent_id: Agent identifier
        """
        if agent_id in self.chains:
            del self.chains[agent_id]
        if agent_id in self.self_calls:
            del self.self_calls[agent_id]
        if agent_id in self.timestamps:
            del self.timestamps[agent_id]

        logger.debug("loop.agent_reset", agent=agent_id)

    def cleanup_old_chains(self, max_age: timedelta = timedelta(hours=1)) -> None:
        """Clean up old delegation chains

        Args:
            max_age: Maximum age of chains to keep
        """
        now = datetime.now(timezone.utc)
        to_remove = []

        for agent_id, timestamp in self.timestamps.items():
            if now - timestamp > max_age:
                to_remove.append(agent_id)

        for agent_id in to_remove:
            self.reset_agent(agent_id)

        if to_remove:
            logger.info("loop.cleanup", removed=len(to_remove))

    def get_chain(self, agent_id: str) -> list[str]:
        """Get delegation chain for agent

        Args:
            agent_id: Agent identifier

        Returns:
            List of agent IDs in the delegation chain
        """
        return self.chains.get(agent_id, [])

    def get_depth(self, agent_id: str) -> int:
        """Get current delegation depth for agent

        Args:
            agent_id: Agent identifier

        Returns:
            Current delegation depth
        """
        return len(self.chains.get(agent_id, []))
