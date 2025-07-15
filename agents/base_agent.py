import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("RetailXAI.BaseAgent")


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    enabled: bool = True
    interval_minutes: Optional[int] = None
    max_retries: int = 3
    timeout_seconds: int = 30
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseAgent(ABC):
    """Base class for all RetailXAI agents."""

    def __init__(self, config: AgentConfig, shutdown_event: Optional[threading.Event] = None):
        """Initialize the base agent.

        Args:
            config: Agent configuration.
            shutdown_event: Event for graceful shutdown.
        """
        self.config = config
        self.shutdown_event = shutdown_event
        self.logger = logging.getLogger(f"RetailXAI.{config.name}")
        self.is_running = False
        self.last_execution = None
        self.execution_count = 0
        self.error_count = 0

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            self.logger.info("Shutdown requested, stopping agent")
            return True
        return False

    @abstractmethod
    async def execute(self) -> AgentResult:
        """Execute the agent's main functionality.

        Returns:
            AgentResult with execution details.
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the agent's configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent.

        Returns:
            Dictionary with agent status information.
        """
        return {
            "name": self.config.name,
            "enabled": self.config.enabled,
            "is_running": self.is_running,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
        }

    async def run_with_retry(self) -> AgentResult:
        """Execute the agent with retry logic.

        Returns:
            AgentResult from the execution.
        """
        if not self.config.enabled:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error="Agent is disabled"
            )

        if self._check_shutdown():
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error="Shutdown requested"
            )

        start_time = time.time()
        self.is_running = True
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"Executing agent (attempt {attempt + 1}/{self.config.max_retries})")
                result = await self.execute()
                result.execution_time = time.time() - start_time
                
                if result.success:
                    self.execution_count += 1
                    self.last_execution = datetime.now()
                    self.logger.info(f"Agent executed successfully in {result.execution_time:.2f}s")
                else:
                    self.error_count += 1
                    self.logger.warning(f"Agent execution failed: {result.error}")
                
                self.is_running = False
                return result
                
            except Exception as e:
                self.logger.error(f"Agent execution failed (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    self.error_count += 1
                    self.is_running = False
                    return AgentResult(
                        agent_name=self.config.name,
                        success=False,
                        error=str(e),
                        execution_time=time.time() - start_time
                    )
                time.sleep(2 ** attempt)  # Exponential backoff

        self.is_running = False
        return AgentResult(
            agent_name=self.config.name,
            success=False,
            error="Max retries exceeded"
        )