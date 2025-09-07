#!/usr/bin/env python3
"""
Fix production database schema to match staging site expectations.
This script connects to the production server and updates the database schema.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yaml

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_config():
    """Load configuration files."""
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    with open('config/companies.yaml', 'r') as f:
        companies_config = yaml.safe_load(f)
    
    return config, companies_config

def create_database_schema():
    """Create the proper database schema on production server."""
    print("🔧 Creating database schema on production server...")
    
    # SQL commands to create the proper schema
    schema_commands = [
        # Create companies table
        """
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            youtube_channels TEXT[],
            rss_feed TEXT,
            keywords TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create transcripts table
        """
        CREATE TABLE IF NOT EXISTS transcripts (
            id SERIAL PRIMARY KEY,
            company_id INTEGER REFERENCES companies(id),
            video_id VARCHAR(255),
            title TEXT,
            content TEXT,
            published_at TIMESTAMP,
            channel_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create analyses table
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id SERIAL PRIMARY KEY,
            company_id INTEGER REFERENCES companies(id),
            transcript_id INTEGER REFERENCES transcripts(id),
            analysis_type VARCHAR(100),
            analysis_data JSONB,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create articles table
        """
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            company_id INTEGER REFERENCES companies(id),
            analysis_id INTEGER REFERENCES analyses(id),
            title TEXT,
            content TEXT,
            article_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create health_checks table
        """
        CREATE TABLE IF NOT EXISTS health_checks (
            id SERIAL PRIMARY KEY,
            check_type VARCHAR(100),
            status VARCHAR(50),
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create agent_states table
        """
        CREATE TABLE IF NOT EXISTS agent_states (
            id SERIAL PRIMARY KEY,
            agent_name VARCHAR(100),
            is_running BOOLEAN DEFAULT FALSE,
            last_execution TIMESTAMP,
            status_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    
    # Execute schema commands via SSH
    for i, command in enumerate(schema_commands, 1):
        print(f"  📝 Executing schema command {i}/{len(schema_commands)}...")
        
        # Create a temporary SQL file
        sql_file = f"temp_schema_{i}.sql"
        with open(sql_file, 'w') as f:
            f.write(command)
        
        # Execute via SSH
        try:
            import subprocess
            result = subprocess.run([
                'ssh', 'root@143.198.14.56', 
                f'cd /home/retailxai/precipice && psql -U retailxbt_user -d retailxai -f - < {sql_file}'
            ], input=command, text=True, capture_output=True, timeout=30)
            
            if result.returncode == 0:
                print(f"    ✅ Schema command {i} executed successfully")
            else:
                print(f"    ⚠️  Schema command {i} warning: {result.stderr}")
                
        except Exception as e:
            print(f"    ❌ Schema command {i} failed: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(sql_file):
                os.remove(sql_file)
    
    print("✅ Database schema creation completed")

def populate_companies(companies_config):
    """Populate companies table with test data."""
    print("🏢 Populating companies table...")
    
    for company_data in companies_config['companies']:
        print(f"  📝 Adding company: {company_data['name']}")
        
        # Create SQL insert command
        insert_sql = f"""
        INSERT INTO companies (name, youtube_channels, rss_feed, keywords) 
        VALUES ('{company_data['name']}', 
                ARRAY{company_data.get('youtube_channels', [])}, 
                '{company_data.get('rss_feed', '')}', 
                ARRAY{company_data.get('keywords', [])})
        ON CONFLICT (name) DO NOTHING;
        """
        
        try:
            import subprocess
            result = subprocess.run([
                'ssh', 'root@143.198.14.56', 
                'cd /home/retailxai/precipice && psql -U retailxbt_user -d retailxai -c',
                insert_sql
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"    ✅ Company {company_data['name']} added successfully")
            else:
                print(f"    ⚠️  Company {company_data['name']} warning: {result.stderr}")
                
        except Exception as e:
            print(f"    ❌ Company {company_data['name']} failed: {e}")

def test_database_connection():
    """Test if the database is working properly."""
    print("🔍 Testing database connection...")
    
    try:
        response = requests.get('http://143.198.14.56:5000/api/companies', timeout=10)
        if response.status_code == 200:
            companies = response.json()
            print(f"✅ Database connection working - found {len(companies)} companies")
            return True
        else:
            print(f"❌ Database connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Main function to fix production database."""
    print("🚀 Fixing Production Database Schema")
    print("=" * 50)
    
    # Load configuration
    config, companies_config = load_config()
    
    # Create database schema
    create_database_schema()
    
    # Populate companies
    populate_companies(companies_config)
    
    # Test connection
    if test_database_connection():
        print("\n✅ Database fix completed successfully!")
        print("🔄 You can now run the historical data test:")
        print("   python3 test_historical_data_server.py")
    else:
        print("\n❌ Database fix failed. Please check the production server manually.")
        print("🔧 Manual steps:")
        print("1. SSH to production server: ssh root@143.198.14.56")
        print("2. Check database: psql -U retailxbt_user -d retailxai")
        print("3. Verify tables: \\dt")

if __name__ == "__main__":
    main()
