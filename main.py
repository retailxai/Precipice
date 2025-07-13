import logging
import os
from pathlib import Path
import stat

from dotenv import load_dotenv

from scheduler import RetailXAIScheduler

logger = logging.getLogger("RetailXAI.Main")


def check_env_permissions(env_path: Path) -> None:
    """Check .env file permissions.

    Args:
        env_path: Path to .env file.
    """
    env_stat = env_path.stat()
    if env_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        logger.warning(f"Permissive .env permissions: {oct(env_stat.st_mode)}")


def main() -> None:
    """RetailXAI main entry point."""
    env_path = Path("config/.env")
    if not load_dotenv(env_path):
        logger.error(f"Failed to load .env file: {env_path}")
        raise FileNotFoundError(f".env file not found at {env_path}")

    check_env_permissions(env_path)
    scheduler = RetailXAIScheduler()
    scheduler.setup_schedule()
    scheduler.run()


if __name__ == "__main__":
    main()
