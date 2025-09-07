#!/usr/bin/env python3
"""
Setup production database schema.
This script should be run directly on the production server.
"""

import psycopg2
import json
import yaml
from datetime import datetime

def create_database_schema():
    """Create the proper database schema."""
    print("🔧 Creating database schema...")
    
    # Database connection
    conn = psycopg2.connect(
        host='localhost',
        database='retailxai',
        user='retailxbt_user',
        password='Seattle2311'
    )
    
    try:
        with conn.cursor() as cur:
            # Create companies table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    youtube_channels TEXT[],
                    rss_feed TEXT,
                    keywords TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Companies table created")
            
            # Create transcripts table
            cur.execute("""
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
            """)
            print("✅ Transcripts table created")
            
            # Create analyses table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id),
                    transcript_id INTEGER REFERENCES transcripts(id),
                    analysis_type VARCHAR(100),
                    analysis_data JSONB,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Analyses table created")
            
            # Create articles table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id),
                    analysis_id INTEGER REFERENCES analyses(id),
                    title TEXT,
                    content TEXT,
                    article_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Articles table created")
            
            # Create health_checks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id SERIAL PRIMARY KEY,
                    check_type VARCHAR(100),
                    status VARCHAR(50),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Health checks table created")
            
            # Create agent_states table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent_states (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(100),
                    is_running BOOLEAN DEFAULT FALSE,
                    last_execution TIMESTAMP,
                    status_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Agent states table created")
            
            conn.commit()
            print("✅ Database schema created successfully")
            
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
    finally:
        conn.close()

def populate_companies():
    """Populate companies table with test data."""
    print("🏢 Populating companies table...")
    
    companies_data = [
        {
            'name': 'Walmart',
            'youtube_channels': ['UCX0-FP8iPvFwIHLG2NNfNVg'],
            'rss_feed': 'https://corporate.walmart.com/newsroom/rss',
            'keywords': ['retail', 'grocery', 'earnings']
        },
        {
            'name': 'PepsiCo',
            'youtube_channels': ['UCk3f5LKLrHRr5lzh4mW_mqw'],
            'rss_feed': 'https://www.pepsico.com/news/rss',
            'keywords': ['CPG', 'beverage', 'earnings']
        }
    ]
    
    conn = psycopg2.connect(
        host='localhost',
        database='retailxai',
        user='retailxbt_user',
        password='Seattle2311'
    )
    
    try:
        with conn.cursor() as cur:
            for company in companies_data:
                cur.execute("""
                    INSERT INTO companies (name, youtube_channels, rss_feed, keywords) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING;
                """, (
                    company['name'],
                    company['youtube_channels'],
                    company['rss_feed'],
                    company['keywords']
                ))
                print(f"✅ Company {company['name']} added")
            
            conn.commit()
            print("✅ Companies populated successfully")
            
    except Exception as e:
        print(f"❌ Error populating companies: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_sample_data():
    """Add some sample data for testing."""
    print("📊 Adding sample data...")
    
    conn = psycopg2.connect(
        host='localhost',
        database='retailxai',
        user='retailxbt_user',
        password='Seattle2311'
    )
    
    try:
        with conn.cursor() as cur:
            # Get company IDs
            cur.execute("SELECT id, name FROM companies")
            companies = cur.fetchall()
            
            if not companies:
                print("❌ No companies found. Please populate companies first.")
                return
            
            # Add sample transcripts
            for company_id, company_name in companies:
                cur.execute("""
                    INSERT INTO transcripts (company_id, video_id, title, content, published_at, channel_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    company_id,
                    f"sample_video_{company_id}",
                    f"{company_name} Q4 2024 Earnings Call",
                    f"Sample transcript content for {company_name} earnings call. This is a demonstration of the RetailXAI system collecting and analyzing financial data.",
                    datetime.now(),
                    "sample_channel"
                ))
                print(f"✅ Sample transcript added for {company_name}")
            
            # Add sample health check
            cur.execute("""
                INSERT INTO health_checks (check_type, status, message)
                VALUES (%s, %s, %s)
            """, (
                "database",
                "healthy",
                "Database connection successful"
            ))
            print("✅ Sample health check added")
            
            conn.commit()
            print("✅ Sample data added successfully")
            
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main function to setup production database."""
    print("🚀 Setting up Production Database")
    print("=" * 40)
    
    try:
        # Create schema
        create_database_schema()
        
        # Populate companies
        populate_companies()
        
        # Add sample data
        add_sample_data()
        
        print("\n✅ Production database setup completed!")
        print("🔄 The staging site should now work properly.")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("Please check the database connection and try again.")

if __name__ == "__main__":
    main()
