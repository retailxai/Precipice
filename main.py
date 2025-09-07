import logging
import os
import sys
from pathlib import Path
import stat

from dotenv import load_dotenv

from scheduler import RetailXAIScheduler
from environment_validator import validate_startup, EnvironmentValidator

logger = logging.getLogger("RetailXAI.Main")


def check_env_permissions(env_path: Path) -> None:
    """Check .env file permissions.

    Args:
        env_path: Path to .env file.
    """
    env_stat = env_path.stat()
    if env_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        logger.warning(f"Permissive .env permissions: {oct(env_stat.st_mode)}")


def setup_exception_handling() -> None:
    """Set up global exception handling."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("Received keyboard interrupt, shutting down gracefully")
            sys.exit(0)
        
        logger.critical(
            f"Unhandled exception: {exc_type.__name__}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # In production, you might want to send alerts here
        # send_alert_to_monitoring_system(exc_type, exc_value, exc_traceback)
        
        sys.exit(1)
    
    sys.excepthook = handle_exception


def main() -> None:
    """RetailXAI main entry point."""
    # Set up global exception handling
    setup_exception_handling()
    
    # Load environment variables
    env_path = Path("config/.env")
    if not load_dotenv(env_path):
        logger.error(f"Failed to load .env file: {env_path}")
        raise FileNotFoundError(f".env file not found at {env_path}")

    # Check file permissions
    check_env_permissions(env_path)
    
    # Validate environment
    if not validate_startup():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)
    
    # Get comprehensive validation report
    validator = EnvironmentValidator()
    report = validator.get_validation_report()
    
    if not report['overall_valid']:
        logger.error("System validation failed. Please check the following:")
        for error in report['errors']:
            logger.error(f"  - {error}")
        for rec in report['recommendations']:
            logger.warning(f"  - {rec}")
        sys.exit(1)
    
    logger.info("Starting RetailXAI Scheduler")
    
    try:
        scheduler = RetailXAIScheduler()
        scheduler.setup_schedule()
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down gracefully")
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
