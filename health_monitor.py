import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import threading
import json

from database_manager import DatabaseManager
from circuit_breaker import circuit_breaker_manager

logger = logging.getLogger("RetailXAI.HealthMonitor")


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    response_time_ms: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class HealthCheck:
    """Base class for health checks."""
    
    def __init__(self, name: str, timeout: int = 30):
        self.name = name
        self.timeout = timeout
    
    def check(self) -> HealthCheckResult:
        """Perform the health check.
        
        Returns:
            HealthCheckResult with check status.
        """
        start_time = time.time()
        try:
            result = self._perform_check()
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=result.get('status', False),
                message=result.get('message', ''),
                details=result.get('details'),
                response_time_ms=response_time
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Health check '{self.name}' failed with exception: {e}")
            return HealthCheckResult(
                name=self.name,
                status=False,
                message=f"Check failed with exception: {str(e)}",
                response_time_ms=response_time
            )
    
    def _perform_check(self) -> Dict[str, Any]:
        """Override this method to implement the actual check.
        
        Returns:
            Dictionary with 'status', 'message', and optional 'details'.
        """
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Health check for database connectivity."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__("database")
        self.db_manager = db_manager
    
    def _perform_check(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            # Test basic connectivity
            if not self.db_manager.is_healthy():
                return {
                    'status': False,
                    'message': 'Database connection failed',
                    'details': {'error': 'Connection pool unhealthy'}
                }
            
            # Test query performance
            start_time = time.time()
            health_status = self.db_manager.get_health_status()
            query_time = (time.time() - start_time) * 1000
            
            return {
                'status': True,
                'message': 'Database is healthy',
                'details': {
                    'query_time_ms': query_time,
                    'overall_status': health_status.get('overall_status', False),
                    'recent_checks': len(health_status.get('checks', []))
                }
            }
        except Exception as e:
            return {
                'status': False,
                'message': f'Database check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class MemoryHealthCheck(HealthCheck):
    """Health check for memory usage."""
    
    def __init__(self, max_memory_percent: float = 90.0):
        super().__init__("memory")
        self.max_memory_percent = max_memory_percent
    
    def _perform_check(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            status = memory_percent < self.max_memory_percent
            message = f"Memory usage: {memory_percent:.1f}%"
            
            if not status:
                message += f" (exceeds {self.max_memory_percent}% threshold)"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_percent': memory_percent,
                    'threshold_percent': self.max_memory_percent
                }
            }
        except Exception as e:
            return {
                'status': False,
                'message': f'Memory check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class DiskSpaceHealthCheck(HealthCheck):
    """Health check for disk space."""
    
    def __init__(self, min_free_gb: float = 1.0):
        super().__init__("disk_space")
        self.min_free_gb = min_free_gb
    
    def _perform_check(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            
            status = free_gb >= self.min_free_gb
            message = f"Free disk space: {free_gb:.1f} GB"
            
            if not status:
                message += f" (below {self.min_free_gb} GB threshold)"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': free_gb,
                    'threshold_gb': self.min_free_gb
                }
            }
        except Exception as e:
            return {
                'status': False,
                'message': f'Disk space check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class CircuitBreakerHealthCheck(HealthCheck):
    """Health check for circuit breaker states."""
    
    def __init__(self):
        super().__init__("circuit_breakers")
    
    def _perform_check(self) -> Dict[str, Any]:
        """Check circuit breaker states."""
        try:
            states = circuit_breaker_manager.get_all_states()
            open_breakers = []
            half_open_breakers = []
            
            for name, state in states.items():
                if state['state'] == 'open':
                    open_breakers.append(name)
                elif state['state'] == 'half_open':
                    half_open_breakers.append(name)
            
            status = len(open_breakers) == 0
            message = f"Circuit breakers: {len(states)} total"
            
            if open_breakers:
                message += f", {len(open_breakers)} open: {', '.join(open_breakers)}"
            if half_open_breakers:
                message += f", {len(half_open_breakers)} half-open: {', '.join(half_open_breakers)}"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'total_breakers': len(states),
                    'open_breakers': open_breakers,
                    'half_open_breakers': half_open_breakers,
                    'states': states
                }
            }
        except Exception as e:
            return {
                'status': False,
                'message': f'Circuit breaker check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class LogFileHealthCheck(HealthCheck):
    """Health check for log file size and rotation."""
    
    def __init__(self, log_file_path: str, max_size_mb: float = 100.0):
        super().__init__("log_files")
        self.log_file_path = log_file_path
        self.max_size_mb = max_size_mb
    
    def _perform_check(self) -> Dict[str, Any]:
        """Check log file size and rotation."""
        try:
            if not os.path.exists(self.log_file_path):
                return {
                    'status': True,
                    'message': 'Log file does not exist (normal for new installations)',
                    'details': {'file_exists': False}
                }
            
            file_size = os.path.getsize(self.log_file_path)
            file_size_mb = file_size / (1024**2)
            
            status = file_size_mb < self.max_size_mb
            message = f"Log file size: {file_size_mb:.1f} MB"
            
            if not status:
                message += f" (exceeds {self.max_size_mb} MB threshold)"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'file_path': self.log_file_path,
                    'size_mb': file_size_mb,
                    'threshold_mb': self.max_size_mb,
                    'file_exists': True
                }
            }
        except Exception as e:
            return {
                'status': False,
                'message': f'Log file check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class ProcessHealthCheck(HealthCheck):
    """Health check for process status."""
    
    def __init__(self):
        super().__init__("process")
    
    def _perform_check(self) -> Dict[str, Any]:
        """Check process status and resource usage."""
        try:
            process = psutil.Process()
            
            # Get process info
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024**2)
            
            # Check if process is responsive
            try:
                process.status()
                is_running = True
            except psutil.NoSuchProcess:
                is_running = False
            
            status = is_running and cpu_percent < 95.0  # Not overloaded
            message = f"Process running: {is_running}, CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f} MB"
            
            if not is_running:
                message = "Process is not running"
            elif cpu_percent >= 95.0:
                message += " (CPU overloaded)"
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'pid': process.pid,
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'is_running': is_running,
                    'create_time': process.create_time(),
                    'num_threads': process.num_threads()
                }
            }
        except Exception as e:
            return {
                'status': False,
                'message': f'Process check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager
        self.checks: List[HealthCheck] = []
        self.results: List[HealthCheckResult] = []
        self.lock = threading.Lock()
        self._setup_default_checks()
    
    def _setup_default_checks(self) -> None:
        """Set up default health checks."""
        if self.db_manager:
            self.checks.append(DatabaseHealthCheck(self.db_manager))
        
        self.checks.extend([
            MemoryHealthCheck(),
            DiskSpaceHealthCheck(),
            CircuitBreakerHealthCheck(),
            LogFileHealthCheck("logs/retailxai.log"),
            ProcessHealthCheck()
        ])
    
    def add_check(self, check: HealthCheck) -> None:
        """Add a custom health check.
        
        Args:
            check: Health check instance to add.
        """
        with self.lock:
            self.checks.append(check)
    
    def run_health_checks(self) -> List[HealthCheckResult]:
        """Run all health checks.
        
        Returns:
            List of health check results.
        """
        results = []
        
        for check in self.checks:
            try:
                result = check.check()
                results.append(result)
                
                # Log result
                if result.status:
                    logger.debug(f"Health check '{result.name}' passed: {result.message}")
                else:
                    logger.warning(f"Health check '{result.name}' failed: {result.message}")
                    
            except Exception as e:
                logger.error(f"Health check '{check.name}' raised exception: {e}")
                results.append(HealthCheckResult(
                    name=check.name,
                    status=False,
                    message=f"Check raised exception: {str(e)}"
                ))
        
        with self.lock:
            self.results = results
        
        # Save results to database if available
        if self.db_manager:
            self._save_health_results(results)
        
        return results
    
    def _save_health_results(self, results: List[HealthCheckResult]) -> None:
        """Save health check results to database."""
        try:
            for result in results:
                self.db_manager.save_health_check(
                    result.name,
                    result.status,
                    {
                        'message': result.message,
                        'details': result.details,
                        'response_time_ms': result.response_time_ms
                    }
                )
        except Exception as e:
            logger.error(f"Failed to save health check results: {e}")
    
    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall health status.
        
        Returns:
            Dictionary with overall health information.
        """
        with self.lock:
            if not self.results:
                return {
                    'overall_healthy': False,
                    'message': 'No health checks have been run',
                    'checks': [],
                    'summary': {
                        'total': 0,
                        'passed': 0,
                        'failed': 0
                    }
                }
            
            total_checks = len(self.results)
            passed_checks = sum(1 for r in self.results if r.status)
            failed_checks = total_checks - passed_checks
            
            overall_healthy = failed_checks == 0
            
            message = f"Health status: {passed_checks}/{total_checks} checks passed"
            if failed_checks > 0:
                failed_names = [r.name for r in self.results if not r.status]
                message += f" (failed: {', '.join(failed_names)})"
            
            return {
                'overall_healthy': overall_healthy,
                'message': message,
                'checks': [
                    {
                        'name': r.name,
                        'status': r.status,
                        'message': r.message,
                        'response_time_ms': r.response_time_ms,
                        'timestamp': r.timestamp.isoformat()
                    }
                    for r in self.results
                ],
                'summary': {
                    'total': total_checks,
                    'passed': passed_checks,
                    'failed': failed_checks
                }
            }
    
    def get_failed_checks(self) -> List[HealthCheckResult]:
        """Get list of failed health checks.
        
        Returns:
            List of failed health check results.
        """
        with self.lock:
            return [r for r in self.results if not r.status]
    
    def is_healthy(self) -> bool:
        """Check if system is overall healthy.
        
        Returns:
            True if all checks pass, False otherwise.
        """
        status = self.get_overall_status()
        return status['overall_healthy']
    
    def get_health_summary(self) -> str:
        """Get a human-readable health summary.
        
        Returns:
            Health summary string.
        """
        status = self.get_overall_status()
        
        summary = f"🏥 Health Status: {status['message']}\n"
        summary += f"📊 Summary: {status['summary']['passed']}/{status['summary']['total']} checks passed\n\n"
        
        for check in status['checks']:
            emoji = "✅" if check['status'] else "❌"
            response_time = f" ({check['response_time_ms']:.1f}ms)" if check['response_time_ms'] else ""
            summary += f"{emoji} {check['name']}: {check['message']}{response_time}\n"
        
        return summary


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor(db_manager: Optional[DatabaseManager] = None) -> HealthMonitor:
    """Get the global health monitor instance.
    
    Args:
        db_manager: Database manager instance.
        
    Returns:
        Health monitor instance.
    """
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor(db_manager)
    return _health_monitor


def run_health_checks(db_manager: Optional[DatabaseManager] = None) -> Dict[str, Any]:
    """Run health checks and return results.
    
    Args:
        db_manager: Database manager instance.
        
    Returns:
        Health check results.
    """
    monitor = get_health_monitor(db_manager)
    results = monitor.run_health_checks()
    return monitor.get_overall_status()


if __name__ == "__main__":
    # Run health checks when script is executed directly
    import sys
    from database_manager import DatabaseManager
    
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Try to initialize database manager
    db_manager = None
    try:
        # This would need actual database config in real usage
        # db_manager = DatabaseManager(config)
        pass
    except Exception as e:
        logger.warning(f"Could not initialize database manager: {e}")
    
    # Run health checks
    results = run_health_checks(db_manager)
    
    print("=== Health Check Results ===")
    print(f"Overall Healthy: {results['overall_healthy']}")
    print(f"Message: {results['message']}")
    print(f"Summary: {results['summary']}")
    
    for check in results['checks']:
        status_emoji = "✅" if check['status'] else "❌"
        print(f"{status_emoji} {check['name']}: {check['message']}")
    
    # Exit with error code if unhealthy
    if not results['overall_healthy']:
        sys.exit(1)
