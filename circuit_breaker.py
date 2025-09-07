import logging
import time
import threading
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger("RetailXAI.CircuitBreaker")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    timeout: int = 30
    expected_exception: type = Exception


class CircuitBreaker:
    """Circuit breaker implementation for API calls."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker.
            config: Configuration for the circuit breaker.
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.lock = threading.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute.
            *args: Arguments for the function.
            **kwargs: Keyword arguments for the function.
            
        Returns:
            Result of the function call.
            
        Raises:
            CircuitBreakerOpenException: If circuit is open.
            Exception: If the function call fails.
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN state")
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Last failure: {self.last_failure_time}"
                    )
        
        try:
            # Execute the function with timeout
            result = self._execute_with_timeout(func, *args, **kwargs)
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise
        except Exception as e:
            # Unexpected exception - count as failure
            self._on_failure()
            raise

    def _execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Function call timed out after {self.config.timeout} seconds")
        
        # Set up timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.config.timeout)
        
        try:
            return func(*args, **kwargs)
        finally:
            # Restore original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful function call."""
        with self.lock:
            self.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to CLOSED state")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed function call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state opens the circuit
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' moved to OPEN state (failure in half-open)")
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' moved to OPEN state (failure threshold reached)")

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state.
        
        Returns:
            Dictionary with state information.
        """
        with self.lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
                "last_success_time": self.last_success_time,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout
                }
            }

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.last_success_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def is_available(self) -> bool:
        """Check if circuit breaker allows calls.
        
        Returns:
            True if calls are allowed, False otherwise.
        """
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                return self._should_attempt_reset()
            else:  # HALF_OPEN
                return True


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.Lock()

    def get_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker.
        
        Args:
            name: Name of the circuit breaker.
            config: Configuration for the circuit breaker.
            
        Returns:
            Circuit breaker instance.
        """
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers.
        
        Returns:
            Dictionary mapping breaker names to their states.
        """
        with self.lock:
            return {name: breaker.get_state() for name, breaker in self.breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()

    def reset_breaker(self, name: str) -> None:
        """Reset a specific circuit breaker.
        
        Args:
            name: Name of the circuit breaker to reset.
        """
        with self.lock:
            if name in self.breakers:
                self.breakers[name].reset()


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get a circuit breaker by name.
    
    Args:
        name: Name of the circuit breaker.
        config: Configuration for the circuit breaker.
        
    Returns:
        Circuit breaker instance.
    """
    return circuit_breaker_manager.get_breaker(name, config)


def with_circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator to add circuit breaker protection to a function.
    
    Args:
        name: Name of the circuit breaker.
        config: Configuration for the circuit breaker.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            breaker = get_circuit_breaker(name, config)
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Predefined circuit breaker configurations
API_CONFIGS = {
    "claude": CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=120,
        success_threshold=2,
        timeout=60,
        expected_exception=Exception
    ),
    "youtube": CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=300,  # 5 minutes
        success_threshold=3,
        timeout=30,
        expected_exception=Exception
    ),
    "news_api": CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=60,
        success_threshold=2,
        timeout=15,
        expected_exception=Exception
    ),
    "reddit": CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=180,
        success_threshold=2,
        timeout=20,
        expected_exception=Exception
    ),
    "linkedin": CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=300,
        success_threshold=2,
        timeout=30,
        expected_exception=Exception
    ),
    "slack": CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        success_threshold=2,
        timeout=10,
        expected_exception=Exception
    )
}
