import json
import logging
import time
from typing import Dict, List, Optional, Callable, Any

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError, InterfaceError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from entities import Analysis, Article, Company, Transcript

logger = logging.getLogger("RetailXAI.DatabaseManager")


class DatabaseManager:
    """Manages PostgreSQL database interactions with proper error handling and resilience."""

    def __init__(self, config: Dict[str, str]):
        """Initialize DatabaseManager with connection pool.

        Args:
            config: Database configuration (host, name, user, password, etc.).
        """
        self.config = config
        self.pool = None
        self._max_retries = 3
        self._retry_delay = 1
        self._init_connection_pool()
        self._init_schema()

    def _init_connection_pool(self) -> None:
        """Initialize connection pool with retry logic."""
        for attempt in range(self._max_retries):
            try:
                self.pool = SimpleConnectionPool(
                    minconn=self.config["min_connections"],
                    maxconn=self.config["max_connections"],
                    host=self.config["host"],
                    database=self.config["name"],
                    user=self.config["user"],
                    password=self.config["password"],
                    connect_timeout=self.config["connect_timeout"],
                )
                logger.info("Database connection pool initialized successfully")
                return
            except (OperationalError, InterfaceError) as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt == self._max_retries - 1:
                    logger.error("Failed to initialize database connection pool after all retries")
                    raise
                time.sleep(self._retry_delay * (2 ** attempt))

    def _safe_db_operation(self, operation_func: Callable, *args, **kwargs) -> Any:
        """Execute database operation with proper error handling and connection management.
        
        Args:
            operation_func: Function to execute with database connection.
            *args: Arguments to pass to operation function.
            **kwargs: Keyword arguments to pass to operation function.
            
        Returns:
            Result of the operation function.
            
        Raises:
            OperationalError: If database connection fails after all retries.
        """
        conn = None
        for attempt in range(self._max_retries):
            try:
                conn = self.pool.getconn()
                if conn is None:
                    raise OperationalError("Failed to get connection from pool")
                
                result = operation_func(conn, *args, **kwargs)
                conn.commit()
                return result
                
            except (OperationalError, InterfaceError) as e:
                logger.warning(f"Database operation attempt {attempt + 1} failed: {e}")
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                
                if attempt == self._max_retries - 1:
                    logger.error("Database operation failed after all retries")
                    raise
                    
                # Return connection to pool before retry
                if conn:
                    try:
                        self.pool.putconn(conn)
                    except Exception:
                        pass
                    conn = None
                    
                time.sleep(self._retry_delay * (2 ** attempt))
                
            except Exception as e:
                logger.error(f"Unexpected error in database operation: {e}")
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise
                
            finally:
                if conn:
                    try:
                        self.pool.putconn(conn)
                    except Exception as e:
                        logger.error(f"Failed to return connection to pool: {e}")

    def _check_connection_health(self) -> bool:
        """Check if database connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise.
        """
        try:
            conn = self.pool.getconn()
            if conn is None:
                return False
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            if 'conn' in locals() and conn:
                try:
                    self.pool.putconn(conn)
                except Exception:
                    pass

    def _init_schema(self) -> None:
        """Initialize database schema."""
        def _create_schema(conn):
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
                    CREATE TABLE IF NOT EXISTS agent_states (
                        id SERIAL PRIMARY KEY,
                        agent_name VARCHAR(255) NOT NULL,
                        state JSONB NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS health_checks (
                        id SERIAL PRIMARY KEY,
                        check_name VARCHAR(255) NOT NULL,
                        status BOOLEAN NOT NULL,
                        details JSONB,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        
        try:
            self._safe_db_operation(_create_schema)
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise

    def insert_company(self, company: Company) -> int:
        """Insert a company into the database.

        Args:
            company: Company entity.

        Returns:
            Company ID.
        """
        def _insert_company(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO companies (name, youtube_channels, rss_feed, keywords)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (company.name, company.youtube_channels, company.rss_feed, company.keywords),
                )
                return cursor.fetchone()[0]
        
        company_id = self._safe_db_operation(_insert_company)
        logger.info(f"Inserted company: {company.name}")
        return company_id

    def insert_transcript(self, transcript: Transcript) -> int:
        """Insert a transcript into the database.

        Args:
            transcript: Transcript entity.

        Returns:
            Transcript ID.
        """
        def _insert_transcript(conn):
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
                return cursor.fetchone()[0]
        
        transcript_id = self._safe_db_operation(_insert_transcript)
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
        def _insert_analysis(conn):
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
                return cursor.fetchone()[0]
        
        analysis_id = self._safe_db_operation(_insert_analysis)
        logger.info("Inserted analysis")
        return analysis_id

    def insert_article(self, article: Article) -> int:
        """Insert an article into the database.

        Args:
            article: Article entity.

        Returns:
            Article ID.
        """
        def _insert_article(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO articles (headline, summary, body, key_insights)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (article.headline, article.summary, article.body, article.key_insights),
                )
                return cursor.fetchone()[0]
        
        article_id = self._safe_db_operation(_insert_article)
        logger.info(f"Inserted article: {article.headline}")
        return article_id

    def save_agent_state(self, agent_name: str, state: Dict[str, Any]) -> None:
        """Save agent state to database.
        
        Args:
            agent_name: Name of the agent.
            state: State data to save.
        """
        def _save_agent_state(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO agent_states (agent_name, state)
                    VALUES (%s, %s)
                    """,
                    (agent_name, json.dumps(state))
                )
        
        try:
            self._safe_db_operation(_save_agent_state)
            logger.debug(f"Saved state for agent: {agent_name}")
        except Exception as e:
            logger.error(f"Failed to save agent state for {agent_name}: {e}")

    def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get the latest agent state from database.
        
        Args:
            agent_name: Name of the agent.
            
        Returns:
            Latest state data or None if not found.
        """
        def _get_agent_state(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT state FROM agent_states 
                    WHERE agent_name = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                    """,
                    (agent_name,)
                )
                result = cursor.fetchone()
                return json.loads(result[0]) if result else None
        
        try:
            return self._safe_db_operation(_get_agent_state)
        except Exception as e:
            logger.error(f"Failed to get agent state for {agent_name}: {e}")
            return None

    def save_health_check(self, check_name: str, status: bool, details: Optional[Dict[str, Any]] = None) -> None:
        """Save health check result to database.
        
        Args:
            check_name: Name of the health check.
            status: Whether the check passed.
            details: Additional details about the check.
        """
        def _save_health_check(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO health_checks (check_name, status, details)
                    VALUES (%s, %s, %s)
                    """,
                    (check_name, status, json.dumps(details) if details else None)
                )
        
        try:
            self._safe_db_operation(_save_health_check)
            logger.debug(f"Saved health check: {check_name} = {status}")
        except Exception as e:
            logger.error(f"Failed to save health check {check_name}: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status from database.
        
        Returns:
            Dictionary with health status information.
        """
        def _get_health_status(conn):
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT check_name, status, details, timestamp
                    FROM health_checks 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                    ORDER BY timestamp DESC
                    """
                )
                results = cursor.fetchall()
                return {
                    'checks': [
                        {
                            'name': row[0],
                            'status': row[1],
                            'details': json.loads(row[2]) if row[2] else None,
                            'timestamp': row[3].isoformat()
                        }
                        for row in results
                    ],
                    'overall_status': all(row[1] for row in results) if results else False
                }
        
        try:
            return self._safe_db_operation(_get_health_status)
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {'checks': [], 'overall_status': False}

    def is_healthy(self) -> bool:
        """Check if database is healthy.
        
        Returns:
            True if database is healthy, False otherwise.
        """
        return self._check_connection_health()

    def close(self) -> None:
        """Close the database connection pool."""
        try:
            if self.pool:
                self.pool.closeall()
                logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Failed to close database pool: {e}")
