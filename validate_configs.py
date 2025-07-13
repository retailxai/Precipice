import json
import logging
import os
from typing import Dict, Any
from jsonschema import validate, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("RetailXBT.ValidateConfigs")

ENTITIES_PATH = os.getenv("ENTITIES_CONFIG_PATH", "config/entities.json")
SOURCES_PATH = os.getenv("SOURCES_CONFIG_PATH", "config/sources.json")
DESTINATIONS_PATH = os.getenv("DESTINATIONS_CONFIG_PATH", "config/destinations.json")
ENTITIES_SCHEMA_PATH = os.getenv("ENTITIES_SCHEMA_PATH", "config/entities_schema.json")
SOURCES_SCHEMA_PATH = os.getenv("SOURCES_SCHEMA_PATH", "config/sources_schema.json")
DESTINATIONS_SCHEMA_PATH = os.getenv(
    "DESTINATIONS_SCHEMA_PATH", "config/destinations_schema.json"
)


def load_json(file_path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return {}


def validate_config(config: Dict[str, Any], schema: Dict[str, Any], config_name: str) -> bool:
    """Validate a config against its schema."""
    try:
        validate(instance=config, schema=schema)
        logger.info(f"Validation successful for {config_name}")
        return True
    except ValidationError as e:
        logger.error(f"Validation failed for {config_name}: {e}")
        return False


def main() -> None:
    """Validate all configuration files."""
    configs = [
        (ENTITIES_PATH, ENTITIES_SCHEMA_PATH, "entities"),
        (SOURCES_PATH, SOURCES_SCHEMA_PATH, "sources"),
        (DESTINATIONS_PATH, DESTINATIONS_SCHEMA_PATH, "destinations"),
    ]
    all_valid = True
    for config_path, schema_path, config_name in configs:
        config = load_json(config_path)
        schema = load_json(schema_path)
        if config and schema:
            if not validate_config(config, schema, config_name):
                all_valid = False
    if all_valid:
        logger.info("All configurations are valid")
    else:
        logger.error("One or more configurations are invalid")
        exit(1)


if __name__ == "__main__":
    main()
