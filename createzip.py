import os
import zipfile
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("RetailXBT.CreateZip")

def run_black() -> bool:
    """Run Black to format Python files."""
    try:
        result = subprocess.run(
            ["black", ".", "--line-length=88", "--check"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Black check passed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Black check failed: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Black is not installed. Please install it with 'pip install black'")
        return False

def run_flake8() -> bool:
    """Run Flake8 to lint Python files."""
    try:
        result = subprocess.run(
            ["flake8", ".", "--max-line-length=88"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Flake8 check passed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Flake8 check failed: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Flake8 is not installed. Please install it with 'pip install flake8'")
        return False

def create_zip() -> None:
    """Create a ZIP file of the project."""
    zip_path = "retailxbt_project.zip"
    files_to_zip = [
        "schema.sql",
        "validate_configs.py",
        "manage_entities.py",
        "sync_configs.py",
        "fetch_data.py",
        "youtube_extractor.py",
        "press_release_monitor.py",
        "scheduler.py",
        "main.py",
        "config/entities.json",
        "config/sources.json",
        "config/destinations.json",
        "config/entities_schema.json",
        "config/sources_schema.json",
        "config/destinations_schema.json",
    ]
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_zip:
                if os.path.exists(file_path):
                    zipf.write(file_path, file_path)
                    logger.info(f"Added {file_path} to ZIP")
                else:
                    logger.warning(f"File not found, skipping: {file_path}")
        logger.info(f"Created ZIP file: {zip_path}")
    except Exception as e:
        logger.error(f"Failed to create ZIP file: {e}")
        raise

def main() -> None:
    """Run code quality checks and create ZIP file."""
    logger.info("Starting ZIP creation process")
    if not run_black():
        logger.error("Aborting due to Black formatting issues")
        raise SystemExit(1)
    if not run_flake8():
        logger.error("Aborting due to Flake8 linting issues")
        raise SystemExit(1)
    create_zip()
    logger.info("ZIP creation process completed successfully")

if __name__ == "__main__":
    main()
