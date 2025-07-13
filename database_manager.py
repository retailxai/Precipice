import logging
from typing import Dict, List

import psycopg2
from psycopg2.pool import SimpleConnectionPool

from entities import Analysis, Article, Company, Transcript

logger = logging.getLogger("RetailXAI.DatabaseManager")


class DatabaseManager:
    """Manages PostgreSQL database interactions."""

    def __init__(self, config: Dict[str, str]):
        """Initialize DatabaseManager with connection pool.

        Args:
            config: Database configuration (host, name, user, password, etc.).
        """
        self.pool = SimpleConnectionPool(
            minconn=config["min_connections"],
            maxconn=config["max_connections"],
            host=config["host"],
            database=config["name"],
            user=config["user"],
            password=config["password"],
            connect_timeout=config["connect_timeout"],
        )
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS companies (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        youtube_channels TEXT[] DEFAULT '{}',
                        rss_feed TEXT,
                        keywords TEXT[] DEFAULT '{}'
                    );
                    CREATE TABLE IF NOT EXISTS transcripts (
                        id SERIAL PRIMARY KEY,
                        company_id INTEGER REFERENCES companies(id),
                        content TEXT NOT NULL,
                        source_id VARCHAR(255) NOT NULL,
                        title TEXT,
                        published_at TIMESTAMP NOT NULL,
                        source_type VARCHAR(50) NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS analyses (
                        id SERIAL PRIMARY KEY,
                        transcript_id INTEGER REFERENCES transcripts(id),
                        metrics JSONB,
                        strategy JSONB,
                        trends JSONB,
                        consumer_insights JSONB,
                        tech_observations JSONB,
                        operations JSONB,
                        outlook JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS articles (
                        id SERIAL PRIMARY KEY,
                        headline VARCHAR(255) NOT NULL,
                        summary TEXT,
                        body TEXT NOT NULL,
                        key_insights TEXT[] DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
            self.pool.putconn(conn)

    def insert_company(self, company: Company) -> int:
        """Insert a company into the database.

        Args:
            company: Company entity.

        Returns:
            Company ID.
        """
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO companies (name, youtube_channels, rss_feed, keywords)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (company.name, company.youtube_channels, company.rss_feed, company.keywords),
                )
                company_id = cursor.fetchone()[0]
                conn.commit()
            self.pool.putconn(conn)
        logger.info(f"Inserted company: {company.name}")
        return company_id

    def insert_transcript(self, transcript: Transcript) -> int:
        """Insert a transcript into the database.

        Args:
            transcript: Transcript entity.

        Returns:
            Transcript ID.
        """
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO companies (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (transcript.company,),
                )
                company_id = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO transcripts (company_id, content, source_id, title, published_at, source_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        company_id,
                        transcript.content,
                        transcript.source_id,
                        transcript.title,
                        transcript.published_at,
                        transcript.source_type,
                    ),
                )
                transcript_id = cursor.fetchone()[0]
                conn.commit()
            self.pool.putconn(conn)
        logger.info(f"Inserted transcript for {transcript.company}")
        return transcript_id

    def insert_analysis(self, analysis: Analysis, transcript_id: int) -> int:
        """Insert an analysis into the database.

        Args:
            analysis: Analysis entity.
            transcript_id: Associated transcript ID.

        Returns:
            Analysis ID.
        """
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO analyses (transcript_id, metrics, strategy, trends, consumer_insights, tech_observations, operations, outlook)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        transcript_id,
                        json.dumps(analysis.metrics),
                        json.dumps(analysis.strategy),
                        json.dumps(analysis.trends),
                        json.dumps(analysis.consumer_insights),
                        json.dumps(analysis.tech_observations),
                        json.dumps(analysis.operations),
                        json.dumps(analysis.outlook),
                    ),
                )
                analysis_id = cursor.fetchone()[0]
                conn.commit()
            self.pool.putconn(conn)
        logger.info("Inserted analysis")
        return analysis_id

    def insert_article(self, article: Article) -> int:
        """Insert an article into the database.

        Args:
            article: Article entity.

        Returns:
            Article ID.
        """
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO articles (headline, summary, body, key_insights)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (article.headline, article.summary, article.body, article.key_insights),
                )
                article_id = cursor.fetchone()[0]
                conn.commit()
            self.pool.putconn(conn)
        logger.info(f"Inserted article: {article.headline}")
        return article_id

    def close(self) -> None:
        """Close the database connection pool."""
        try:
            self.pool.closeall()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Failed to close database pool: {e}")
