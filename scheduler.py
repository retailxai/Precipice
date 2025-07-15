import logging
import signal
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime

import schedule
import yaml

from claude_processor import ClaudeProcessor
from content_manager import ContentManager
from database_manager import DatabaseManager
from entities import Company
from rss_collector import RSSCollector
from trending_collector import TrendingTopicsCollector
from youtube_collector import YouTubeCollector

logger = logging.getLogger("RetailXAI.Scheduler")


class RetailXAIScheduler:
    """Coordinates data fetching, processing, and publishing tasks."""

    def __init__(self, config_path: str = "config/config.yaml", schedule_path: str = "config/schedule.yaml"):
        """Initialize scheduler with configuration.

        Args:
            config_path: Path to main YAML configuration file.
            schedule_path: Path to scheduling YAML configuration file.
        """
        self.config = self._load_config(config_path)
        self.schedule_config = self._load_schedule_config(schedule_path)
        self.shutdown_event = threading.Event()
        self.running_jobs = set()
        self._setup_logging()
        self._setup_signal_handlers()
        self._init_components()

    def _load_config(self, config_path: str) -> dict:
        """Load main configuration from YAML file.

        Args:
            config_path: Path to YAML file.

        Returns:
            Configuration dictionary.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    def _load_schedule_config(self, schedule_path: str) -> dict:
        """Load schedule configuration from YAML file.

        Args:
            schedule_path: Path to schedule YAML file.

        Returns:
            Schedule configuration dictionary.
        """
        try:
            with open(schedule_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {"tasks": []}
        except Exception as e:
            logger.error(f"Failed to load schedule config: {e}")
            return {"tasks": []}

    def _setup_logging(self) -> None:
        """Set up logging with rotation."""
        logging.basicConfig(
            level=self.config["global"]["logging"]["level"],
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    self.config["global"]["logging"]["file"],
                    maxBytes=self.config["global"]["logging"]["max_bytes"],
                    backupCount=self.config["global"]["logging"]["backup_count"],
                ),
                logging.StreamHandler(),
            ],
        )

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        try:
            signal.signal(signal.SIGHUP, self._reload_config_handler)
        except AttributeError:
            pass

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        signal_names = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}
        logger.info(f"Received {signal_names.get(signum, f'signal {signum}')}, initiating shutdown")
        self.shutdown_event.set()
        if signum == signal.SIGINT:
            signal.signal(signal.SIGINT, self._force_exit_handler)

    def _force_exit_handler(self, signum, frame) -> None:
        """Handle forced exit on second SIGINT."""
        logger.warning("Received second SIGINT, forcing exit")
        sys.exit(1)

    def _reload_config_handler(self, signum, frame) -> None:
        """Reload configurations on SIGHUP."""
        logger.info("Received SIGHUP, reloading configurations")
        self.config = self._load_config("config/config.yaml")
        self.schedule_config = self._load_schedule_config("config/schedule.yaml")
        self._init_components()
        self.setup_schedule()

    def _init_components(self) -> None:
        """Initialize scheduler components."""
        companies = self._load_companies()
        self.db_manager = DatabaseManager(self.config["global"]["database"])
        self.youtube_collector = YouTubeCollector(
            self.config["global"]["api_keys"]["youtube"],
            companies,
            self.shutdown_event,
        )
        self.rss_collector = RSSCollector(
            self.config["sources"]["rss"]["feeds"] + self.config["sources"]["rss"]["static_feeds"],
            companies,
            self.shutdown_event,
        )
        self.trending_collector = TrendingTopicsCollector(
            self.config["sources"]["trending"]["reddit"],
            self.config["sources"]["trending"]["twitter"],
            companies,
            self.shutdown_event,
        )
        self.claude_processor = ClaudeProcessor(
            self.config["global"]["api_keys"]["claude"],
            self.config["global"]["claude_model"],
            self.config["prompts"],
            self.shutdown_event,
        )
        self.content_manager = ContentManager(
            self.db_manager.pool,
            self.config["destinations"]["substack"],
            self.config["global"]["api_keys"]["twitter"],
            self.shutdown_event,
        )

    def _load_companies(self) -> list[Company]:
        """Load companies from YAML file.

        Returns:
            List of Company entities.
        """
        try:
            with open(self.config["sources"]["youtube"]["channels"], "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return [
                    Company(
                        name=c["name"],
                        youtube_channels=c["youtube_channels"],
                        rss_feed=c["rss_feed"],
                        keywords=c["keywords"],
                    )
                    for c in data["companies"]
                ]
        except Exception as e:
            logger.error(f"Failed to load companies: {e}")
            return []

    @contextmanager
    def _job_context(self, job_name: str):
        """Context manager for tracking running jobs.

        Args:
            job_name: Name of the job.
        """
        self.running_jobs.add(job_name)
        try:
            yield
        finally:
            self.running_jobs.discard(job_name)

    def _scheduled_job_wrapper(self, job_func, job_name: str):
        """Wrap job functions to handle shutdown and errors.

        Args:
            job_func: Function to execute.
            job_name: Name of the job.

        Returns:
            Wrapped function.
        """
        def wrapper():
            if self.shutdown_event.is_set():
                logger.info(f"Skipping job {job_name} due to shutdown")
                return
            with self._job_context(job_name):
                try:
                    logger.info(f"Starting job: {job_name}")
                    job_func()
                    logger.info(f"Completed job: {job_name}")
                except Exception as e:
                    logger.error(f"Error in job {job_name}: {e}")
        return wrapper

    def daily_earnings_scan(self) -> None:
        """Run daily earnings scan and publish results."""
        if self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping earnings scan")
            return

        # Fetch data
        transcripts = self.youtube_collector.get_transcripts() + self.rss_collector.get_transcripts()
        analyses = []
        for transcript in transcripts:
            if self.shutdown_event.is_set():
                logger.info("Shutdown requested during transcript processing")
                return
            transcript_id = self.db_manager.insert_transcript(transcript)
            analysis = self.claude_processor.analyze_transcript(transcript.content, transcript.company)
            if not analysis.error:
                self.db_manager.insert_analysis(analysis, transcript_id)
                analyses.append(analysis)

        # Generate and publish content
        if len(analyses) >= 2:
            article = self.claude_processor.generate_article(analyses, "Weekly Retail & CPG Earnings Roundup")
            if not article.error:
                article_id = self.db_manager.insert_article(article)
                if self.content_manager.quality_check(article) >= 7:
                    substack_url = self.content_manager.publish_to_substack(article)
                    tweets = self.claude_processor.create_twitter_thread(article)
                    self.content_manager.post_to_twitter(tweets, substack_url)
                    logger.info(f"Published article: {article.headline}")

    def weekly_summary(self) -> None:
        """Run weekly summary of retail trends."""
        if self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping weekly summary")
            return
        # Placeholder for future implementation
        logger.info("Weekly summary task not implemented yet")

    def trending_topics_scan(self) -> None:
        """Scan for trending retail topics and add to processing queue."""
        if self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping trending topics scan")
            return

        # Fetch trending topics
        trending_transcripts = self.trending_collector.get_trending_topics()
        
        if not trending_transcripts:
            logger.info("No trending topics found")
            return

        analyses = []
        for transcript in trending_transcripts:
            if self.shutdown_event.is_set():
                logger.info("Shutdown requested during trending topics processing")
                return
                
            # Store transcript in database
            transcript_id = self.db_manager.insert_transcript(transcript)
            
            # Analyze trending topic
            analysis = self.claude_processor.analyze_transcript(transcript.content, transcript.company)
            if not analysis.error:
                self.db_manager.insert_analysis(analysis, transcript_id)
                analyses.append(analysis)

        # Generate content if we have enough interesting topics
        if len(analyses) >= 3:
            article = self.claude_processor.generate_article(
                analyses, 
                "Trending Retail Topics: What's Buzzing in the Industry"
            )
            if not article.error:
                article_id = self.db_manager.insert_article(article)
                # Quality check before publishing
                if self.content_manager.quality_check(article) >= 6:  # Lower threshold for trending topics
                    substack_url = self.content_manager.publish_to_substack(article)
                    tweets = self.claude_processor.create_twitter_thread(article)
                    self.content_manager.post_to_twitter(tweets, substack_url)
                    logger.info(f"Published trending topics article: {article.headline}")
                else:
                    logger.info("Trending topics article didn't meet quality threshold")
        else:
            logger.info(f"Only {len(analyses)} trending topics analyzed, need at least 3 for article")

    def quota_check(self) -> None:
        """Check and reset YouTube API quota usage."""
        if self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping quota check")
            return
        # Placeholder for future implementation
        logger.info("Quota check task not implemented yet")

    def setup_schedule(self) -> None:
        """Set up scheduled tasks from schedule.yaml."""
        schedule.clear()
        task_functions = {
            "daily_earnings_scan": self.daily_earnings_scan,
            "trending_topics_scan": self.trending_topics_scan,
            "weekly_summary": self.weekly_summary,
            "quota_check": self.quota_check,
        }
        for task in self.schedule_config.get("tasks", []):
            if not task.get("enabled", True):
                logger.info(f"Skipping disabled task: {task['name']}")
                continue
            job_func = task_functions.get(task["name"])
            if not job_func:
                logger.warning(f"Unknown task: {task['name']}")
                continue
            wrapped_job = self._scheduled_job_wrapper(job_func, task["name"])
            if task["type"] == "daily":
                schedule.every().day.at(task["time"]).do(wrapped_job)
                logger.info(f"Scheduled daily task: {task['name']} at {task['time']}")
            elif task["type"] == "weekly":
                getattr(schedule.every(), task["day"].lower()).at(task["time"]).do(wrapped_job)
                logger.info(f"Scheduled weekly task: {task['name']} on {task['day']} at {task['time']}")
            else:
                logger.warning(f"Invalid task type for {task['name']}: {task['type']}")

    def run(self) -> None:
        """Run the scheduler."""
        logger.info("RetailXAI Scheduler started")
        try:
            while not self.shutdown_event.is_set():
                schedule.run_pending()
                if self.shutdown_event.wait(timeout=5):
                    break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.shutdown_event.set()
        logger.info("Scheduler shutdown initiated")
        self._wait_for_jobs_completion()
        self.db_manager.close()
        logger.info("Scheduler shutdown complete")

    def _wait_for_jobs_completion(self, timeout: int = 30) -> None:
        """Wait for running jobs to complete.

        Args:
            timeout: Maximum wait time in seconds.
        """
        if not self.running_jobs:
            return
        logger.info(f"Waiting for {len(self.running_jobs)} jobs to complete")
        start_time = time.time()
        while self.running_jobs and (time.time() - start_time) < timeout:
            logger.info(f"Still waiting for jobs: {', '.join(self.running_jobs)}")
            time.sleep(2)
        if self.running_jobs:
            logger.warning(f"Timeout reached, jobs still running: {', '.join(self.running_jobs)}")
