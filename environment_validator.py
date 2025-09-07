import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("RetailXAI.EnvironmentValidator")


@dataclass
class EnvVar:
    """Represents an environment variable requirement."""
    name: str
    required: bool = True
    pattern: Optional[str] = None
    description: str = ""
    default_value: Optional[str] = None


class EnvironmentValidator:
    """Validates environment variables and configuration at startup."""
    
    def __init__(self):
        self.required_vars = [
            EnvVar(
                name="CLAUDE_API_KEY",
                pattern=r"^sk-ant-[a-zA-Z0-9\-_]{20,}$",
                description="Anthropic Claude API key for AI processing"
            ),
            EnvVar(
                name="YOUTUBE_API_KEY",
                pattern=r"^[A-Za-z0-9_-]{39}$",
                description="YouTube Data API v3 key for video collection"
            ),
            EnvVar(
                name="DATABASE_URL",
                pattern=r"^postgresql://.*",
                description="PostgreSQL database connection URL"
            ),
            EnvVar(
                name="NEWS_API_KEY",
                required=False,
                pattern=r"^[a-f0-9]{32}$",
                description="News API key for news collection (optional)"
            ),
            EnvVar(
                name="LINKEDIN_API_KEY",
                required=False,
                description="LinkedIn API key for social media collection (optional)"
            ),
            EnvVar(
                name="REDDIT_CLIENT_ID",
                required=False,
                description="Reddit API client ID (optional)"
            ),
            EnvVar(
                name="REDDIT_CLIENT_SECRET",
                required=False,
                description="Reddit API client secret (optional)"
            ),
            EnvVar(
                name="SLACK_WEBHOOK_URL",
                required=False,
                pattern=r"^https://hooks\.slack\.com/services/.*",
                description="Slack webhook URL for notifications (optional)"
            ),
            EnvVar(
                name="SLACK_BOT_TOKEN",
                required=False,
                pattern=r"^xoxb-.*",
                description="Slack bot token for notifications (optional)"
            ),
            EnvVar(
                name="TWITTER_CONSUMER_KEY",
                required=False,
                description="Twitter API consumer key (optional)"
            ),
            EnvVar(
                name="TWITTER_CONSUMER_SECRET",
                required=False,
                description="Twitter API consumer secret (optional)"
            ),
            EnvVar(
                name="TWITTER_ACCESS_TOKEN",
                required=False,
                description="Twitter API access token (optional)"
            ),
            EnvVar(
                name="TWITTER_ACCESS_TOKEN_SECRET",
                required=False,
                description="Twitter API access token secret (optional)"
            )
        ]
        
        self.optional_vars = [
            EnvVar(
                name="LOG_LEVEL",
                required=False,
                pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
                description="Logging level",
                default_value="INFO"
            ),
            EnvVar(
                name="MAX_WORKERS",
                required=False,
                pattern=r"^\d+$",
                description="Maximum number of worker threads",
                default_value="4"
            ),
            EnvVar(
                name="DATABASE_POOL_SIZE",
                required=False,
                pattern=r"^\d+$",
                description="Database connection pool size",
                default_value="5"
            ),
            EnvVar(
                name="API_TIMEOUT",
                required=False,
                pattern=r"^\d+$",
                description="API request timeout in seconds",
                default_value="30"
            )
        ]

    def validate_environment(self) -> Tuple[bool, List[str]]:
        """Validate all environment variables.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        warnings = []
        
        # Check required variables
        for var in self.required_vars:
            value = os.getenv(var.name)
            
            if not value:
                if var.required:
                    errors.append(f"Required environment variable {var.name} is not set: {var.description}")
                else:
                    warnings.append(f"Optional environment variable {var.name} is not set: {var.description}")
            else:
                # Validate pattern if provided
                if var.pattern and not re.match(var.pattern, value):
                    errors.append(f"Environment variable {var.name} has invalid format. Expected pattern: {var.pattern}")
        
        # Check optional variables
        for var in self.optional_vars:
            value = os.getenv(var.name)
            
            if value and var.pattern and not re.match(var.pattern, value):
                errors.append(f"Environment variable {var.name} has invalid format. Expected pattern: {var.pattern}")
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
        
        # Log errors
        for error in errors:
            logger.error(error)
        
        return len(errors) == 0, errors

    def get_config(self) -> Dict[str, str]:
        """Get validated configuration dictionary.
        
        Returns:
            Dictionary with environment variables and their values.
        """
        config = {}
        
        # Add required variables
        for var in self.required_vars:
            value = os.getenv(var.name)
            if value:
                config[var.name] = value
            elif var.default_value:
                config[var.name] = var.default_value
        
        # Add optional variables
        for var in self.optional_vars:
            value = os.getenv(var.name)
            if value:
                config[var.name] = value
            elif var.default_value:
                config[var.name] = var.default_value
        
        return config

    def validate_file_permissions(self, file_path: str) -> bool:
        """Validate file permissions for sensitive files.
        
        Args:
            file_path: Path to file to check.
            
        Returns:
            True if permissions are secure, False otherwise.
        """
        if not os.path.exists(file_path):
            return True
        
        try:
            stat_info = os.stat(file_path)
            mode = stat_info.st_mode
            
            # Check if file is readable by group or others
            if mode & 0o044:  # Group or other read permission
                logger.warning(f"File {file_path} has overly permissive permissions: {oct(mode)}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to check permissions for {file_path}: {e}")
            return False

    def validate_database_connection(self, database_url: str) -> bool:
        """Validate database connection.
        
        Args:
            database_url: Database connection URL.
            
        Returns:
            True if connection is valid, False otherwise.
        """
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            parsed = urlparse(database_url)
            
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
                
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate API keys by making test requests.
        
        Returns:
            Dictionary mapping API names to validation results.
        """
        results = {}
        
        # Validate Claude API key
        claude_key = os.getenv("CLAUDE_API_KEY")
        if claude_key:
            results["claude"] = self._validate_claude_key(claude_key)
        
        # Validate YouTube API key
        youtube_key = os.getenv("YOUTUBE_API_KEY")
        if youtube_key:
            results["youtube"] = self._validate_youtube_key(youtube_key)
        
        # Validate News API key
        news_key = os.getenv("NEWS_API_KEY")
        if news_key:
            results["news"] = self._validate_news_key(news_key)
        
        return results

    def _validate_claude_key(self, api_key: str) -> bool:
        """Validate Claude API key."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            # Make a simple test request
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.error(f"Claude API key validation failed: {e}")
            return False

    def _validate_youtube_key(self, api_key: str) -> bool:
        """Validate YouTube API key."""
        try:
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", developerKey=api_key)
            # Make a simple test request
            request = youtube.search().list(part="id", q="test", maxResults=1)
            request.execute()
            return True
        except Exception as e:
            logger.error(f"YouTube API key validation failed: {e}")
            return False

    def _validate_news_key(self, api_key: str) -> bool:
        """Validate News API key."""
        try:
            import requests
            response = requests.get(
                "https://newsapi.org/v2/sources",
                params={"apiKey": api_key},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"News API key validation failed: {e}")
            return False

    def get_validation_report(self) -> Dict[str, any]:
        """Get comprehensive validation report.
        
        Returns:
            Dictionary with validation results and recommendations.
        """
        is_valid, errors = self.validate_environment()
        config = self.get_config()
        api_results = self.validate_api_keys()
        
        # Check database connection if URL is provided
        db_valid = False
        if "DATABASE_URL" in config:
            db_valid = self.validate_database_connection(config["DATABASE_URL"])
        
        return {
            "overall_valid": is_valid and db_valid,
            "environment_valid": is_valid,
            "database_valid": db_valid,
            "api_validations": api_results,
            "errors": errors,
            "config": config,
            "recommendations": self._get_recommendations(errors, api_results, db_valid)
        }

    def _get_recommendations(self, errors: List[str], api_results: Dict[str, bool], db_valid: bool) -> List[str]:
        """Get recommendations based on validation results."""
        recommendations = []
        
        if errors:
            recommendations.append("Fix environment variable issues before starting the application")
        
        if not db_valid:
            recommendations.append("Ensure database is running and accessible")
        
        failed_apis = [api for api, valid in api_results.items() if not valid]
        if failed_apis:
            recommendations.append(f"Check API keys for: {', '.join(failed_apis)}")
        
        if not any(api_results.values()):
            recommendations.append("At least one API key should be valid for the application to function")
        
        return recommendations


def validate_startup() -> bool:
    """Validate environment at startup.
    
    Returns:
        True if validation passes, False otherwise.
    """
    validator = EnvironmentValidator()
    is_valid, errors = validator.validate_environment()
    
    if not is_valid:
        logger.error("Environment validation failed. Please fix the following issues:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("Environment validation passed")
    return True


if __name__ == "__main__":
    # Run validation when script is executed directly
    validator = EnvironmentValidator()
    report = validator.get_validation_report()
    
    print("=== Environment Validation Report ===")
    print(f"Overall Valid: {report['overall_valid']}")
    print(f"Environment Valid: {report['environment_valid']}")
    print(f"Database Valid: {report['database_valid']}")
    print(f"API Validations: {report['api_validations']}")
    
    if report['errors']:
        print("\nErrors:")
        for error in report['errors']:
            print(f"  - {error}")
    
    if report['recommendations']:
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
