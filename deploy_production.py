#!/usr/bin/env python3
"""
Production deployment script for RetailXAI.
This script validates the system and prepares it for production deployment.
"""

import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from environment_validator import EnvironmentValidator
from health_monitor import run_health_checks
from database_manager import DatabaseManager

logger = logging.getLogger("RetailXAI.Deploy")


class ProductionDeployer:
    """Handles production deployment validation and setup."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.db_manager = None
    
    def validate_environment(self) -> bool:
        """Validate environment variables and configuration."""
        logger.info("🔍 Validating environment...")
        
        validator = EnvironmentValidator()
        is_valid, errors = validator.validate_environment()
        
        if not is_valid:
            self.errors.extend(errors)
            logger.error("❌ Environment validation failed")
            return False
        
        logger.info("✅ Environment validation passed")
        return True
    
    def validate_database(self) -> bool:
        """Validate database connectivity and schema."""
        logger.info("🗄️ Validating database...")
        
        try:
            # This would need actual database config in real usage
            # For now, we'll just check if the environment variable exists
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                self.errors.append("DATABASE_URL environment variable not set")
                return False
            
            logger.info("✅ Database configuration found")
            return True
            
        except Exception as e:
            self.errors.append(f"Database validation failed: {e}")
            return False
    
    def validate_dependencies(self) -> bool:
        """Validate that all required dependencies are installed."""
        logger.info("📦 Validating dependencies...")
        
        required_packages = [
            "psycopg2-binary",
            "anthropic",
            "google-api-python-client",
            "youtube-transcript-api",
            "tweepy",
            "feedparser",
            "beautifulsoup4",
            "schedule",
            "python-dotenv",
            "httpx",
            "tenacity",
            "aiohttp",
            "praw",
            "textblob",
            "psutil"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.errors.append(f"Missing required packages: {', '.join(missing_packages)}")
            logger.error(f"❌ Missing packages: {missing_packages}")
            return False
        
        logger.info("✅ All dependencies are installed")
        return True
    
    def validate_file_permissions(self) -> bool:
        """Validate file permissions for security."""
        logger.info("🔒 Validating file permissions...")
        
        sensitive_files = [
            "config/.env",
            "logs/retailxai.log",
            "logs/youtube_quota_usage.json"
        ]
        
        validator = EnvironmentValidator()
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                if not validator.validate_file_permissions(file_path):
                    self.warnings.append(f"File {file_path} has overly permissive permissions")
        
        logger.info("✅ File permissions validated")
        return True
    
    def validate_configuration_files(self) -> bool:
        """Validate configuration files exist and are valid."""
        logger.info("⚙️ Validating configuration files...")
        
        required_configs = [
            "config/agents.yaml",
            "config/companies.yaml",
            "config/schedule.yaml"
        ]
        
        for config_file in required_configs:
            if not os.path.exists(config_file):
                self.errors.append(f"Required configuration file missing: {config_file}")
                return False
        
        logger.info("✅ Configuration files validated")
        return True
    
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        logger.info("🏥 Running health checks...")
        
        try:
            results = run_health_checks(self.db_manager)
            
            if not results['overall_healthy']:
                self.errors.append("Health checks failed")
                for check in results['checks']:
                    if not check['status']:
                        self.errors.append(f"Health check failed: {check['name']} - {check['message']}")
                return False
            
            logger.info("✅ All health checks passed")
            return True
            
        except Exception as e:
            self.errors.append(f"Health checks failed: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        logger.info("📁 Creating directories...")
        
        directories = [
            "logs",
            "drafts",
            "drafts/linkedin",
            "drafts/twitter"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        logger.info("✅ Directories created")
        return True
    
    def setup_logging(self) -> bool:
        """Set up production logging."""
        logger.info("📝 Setting up logging...")
        
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler("logs/retailxai.log"),
                    logging.StreamHandler()
                ]
            )
            
            logger.info("✅ Logging configured")
            return True
            
        except Exception as e:
            self.errors.append(f"Logging setup failed: {e}")
            return False
    
    def generate_systemd_service(self) -> bool:
        """Generate systemd service file for production."""
        logger.info("🔧 Generating systemd service...")
        
        try:
            service_content = f"""[Unit]
Description=RetailXAI Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User={os.getenv('USER', 'retailxai')}
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getenv('PATH')}
EnvironmentFile={os.path.join(os.getcwd(), 'config/.env')}
ExecStart={sys.executable} {os.path.join(os.getcwd(), 'main.py')}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
            
            with open("retailxai.service", "w") as f:
                f.write(service_content)
            
            logger.info("✅ Systemd service file generated: retailxai.service")
            return True
            
        except Exception as e:
            self.errors.append(f"Systemd service generation failed: {e}")
            return False
    
    def generate_docker_compose(self) -> bool:
        """Generate Docker Compose file for production."""
        logger.info("🐳 Generating Docker Compose file...")
        
        try:
            compose_content = """version: '3.8'

services:
  retailxai:
    build: .
    container_name: retailxai
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./drafts:/app/drafts
      - ./config:/app/config
    depends_on:
      - postgres
    networks:
      - retailxai-network

  postgres:
    image: postgres:15
    container_name: retailxai-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=retailxai
      - POSTGRES_USER=retailxai
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - retailxai-network

volumes:
  postgres_data:

networks:
  retailxai-network:
    driver: bridge
"""
            
            with open("docker-compose.yml", "w") as f:
                f.write(compose_content)
            
            logger.info("✅ Docker Compose file generated: docker-compose.yml")
            return True
            
        except Exception as e:
            self.errors.append(f"Docker Compose generation failed: {e}")
            return False
    
    def generate_dockerfile(self) -> bool:
        """Generate Dockerfile for production."""
        logger.info("🐳 Generating Dockerfile...")
        
        try:
            dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs drafts/linkedin drafts/twitter

# Set proper permissions
RUN chmod +x main.py

# Expose port (if needed for health checks)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "from health_monitor import run_health_checks; exit(0 if run_health_checks()['overall_healthy'] else 1)"

# Run the application
CMD ["python", "main.py"]
"""
            
            with open("Dockerfile", "w") as f:
                f.write(dockerfile_content)
            
            logger.info("✅ Dockerfile generated: Dockerfile")
            return True
            
        except Exception as e:
            self.errors.append(f"Dockerfile generation failed: {e}")
            return False
    
    def run_deployment(self) -> bool:
        """Run the complete deployment process."""
        logger.info("🚀 Starting production deployment...")
        
        steps = [
            ("Environment Validation", self.validate_environment),
            ("Dependencies Validation", self.validate_dependencies),
            ("Configuration Validation", self.validate_configuration_files),
            ("File Permissions Validation", self.validate_file_permissions),
            ("Database Validation", self.validate_database),
            ("Directory Creation", self.create_directories),
            ("Logging Setup", self.setup_logging),
            ("Health Checks", self.run_health_checks),
            ("Systemd Service Generation", self.generate_systemd_service),
            ("Docker Compose Generation", self.generate_docker_compose),
            ("Dockerfile Generation", self.generate_dockerfile)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Running: {step_name}")
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return False
            logger.info(f"✅ {step_name} completed")
        
        # Print summary
        self.print_summary()
        
        if self.errors:
            logger.error("❌ Deployment failed with errors")
            return False
        
        logger.info("🎉 Production deployment completed successfully!")
        return True
    
    def print_summary(self) -> None:
        """Print deployment summary."""
        print("\n" + "="*60)
        print("📋 DEPLOYMENT SUMMARY")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ No issues found!")
        
        print("\n📁 Generated Files:")
        generated_files = [
            "retailxai.service",
            "docker-compose.yml", 
            "Dockerfile"
        ]
        
        for file in generated_files:
            if os.path.exists(file):
                print(f"  • {file}")
        
        print("\n🔧 Next Steps:")
        print("  1. Review the generated configuration files")
        print("  2. Set up your database and environment variables")
        print("  3. For systemd: sudo cp retailxai.service /etc/systemd/system/")
        print("  4. For Docker: docker-compose up -d")
        print("  5. Monitor logs: tail -f logs/retailxai.log")
        
        print("="*60)


def main():
    """Main deployment function."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    deployer = ProductionDeployer()
    
    try:
        success = deployer.run_deployment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
