import json
import logging
import re
from typing import Dict, List, Optional
import threading

import anthropic
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from entities import Analysis, Article, Tweet

logger = logging.getLogger("RetailXAI.ClaudeProcessor")


class ClaudeProcessor:
    """Processes transcripts using Anthropic Claude API."""

    def __init__(self, api_key: str, model: str, prompts: Dict[str, str], shutdown_event: Optional[threading.Event] = None):
        """Initialize ClaudeProcessor with API key, model, and prompts.

        Args:
            api_key: Anthropic API key.
            model: Claude model name.
            prompts: Dictionary of prompt templates.
            shutdown_event: Event for graceful shutdown.
        """
        if not re.match(r"^sk-ant-[a-zA-Z0-9\-_]{20,}$", api_key):
            logger.error("Invalid Claude API key")
            raise ValueError("Invalid Claude API key")
        self.client = anthropic.Anthropic(
            api_key=api_key,
            http_client=httpx.Client(timeout=30.0, follow_redirects=True),
        )
        self.model = model
        self.prompts = prompts
        self.shutdown_event = shutdown_event
        self.max_tokens = {"analysis": 1500, "article": 2000, "twitter": 800}
        logger.info(f"ClaudeProcessor initialized with model: {model}")

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping Claude operations")
            return True
        return False

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=(retry_if_exception_type(anthropic.APIConnectionError) | retry_if_exception_type(anthropic.APIError)),
    )
    def analyze_transcript(self, transcript: str, company: str) -> Analysis:
        """Analyze a transcript or press release.

        Args:
            transcript: Text content to analyze.
            company: Company name.

        Returns:
            Analysis entity.
        """
        if self._check_shutdown():
            return Analysis(metrics={}, strategy={}, trends={}, consumer_insights={}, tech_observations={}, operations={}, outlook={}, error="Shutdown requested")

        transcript = re.sub(r"[^\x20-\x7E\n]", "", transcript)[:4000]
        company = re.sub(r"[^\w\s]", "", company)
        prompt = self.prompts["analysis"].format(company=company, content=transcript)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens["analysis"],
                messages=[{"role": "user", "content": prompt}],
            )
            result = self._parse_response(response.content[0].text)
            logger.info(f"Analysis completed for {company}")
            return Analysis(**result)
        except Exception as e:
            logger.error(f"Analysis failed for {company}: {e}")
            return Analysis(metrics={}, strategy={}, trends={}, consumer_insights={}, tech_observations={}, operations={}, outlook={}, error=str(e))

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=(retry_if_exception_type(anthropic.APIConnectionError) | retry_if_exception_type(anthropic.APIError)),
    )
    def generate_article(self, analyses: List[Analysis], title_theme: str) -> Article:
        """Generate a news article from analyses.

        Args:
            analyses: List of Analysis entities.
            title_theme: Article theme.

        Returns:
            Article entity.
        """
        if self._check_shutdown():
            return Article(headline="", summary="", body="", key_insights=[], error="Shutdown requested")

        title_theme = re.sub(r"[^\w\s]", "", title_theme)
        analyses_json = json.dumps([vars(a) for a in analyses if not a.error], indent=2)
        prompt = self.prompts["article"].format(title_theme=title_theme, analyses_json=analyses_json)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens["article"],
                messages=[{"role": "user", "content": prompt}],
            )
            result = self._parse_response(response.content[0].text)
            logger.info(f"Article generated: {title_theme}")
            return Article(**result)
        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            return Article(headline="", summary="", body="", key_insights=[], error=str(e))

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=(retry_if_exception_type(anthropic.APIConnectionError) | retry_if_exception_type(anthropic.APIError)),
    )
    def create_twitter_thread(self, article: Article) -> List[Tweet]:
        """Create a Twitter thread from an article.

        Args:
            article: Article entity.

        Returns:
            List of Tweet entities.
        """
        if self._check_shutdown():
            return []

        headline = re.sub(r"[^\w\s]", "", article.headline)
        summary = re.sub(r"[^\w\s]", "", article.summary)
        key_insights = json.dumps(article.key_insights)
        hashtags = " ".join(f"#{tag}" for tag in ["RetailAI", "CPG", "EarningsAlert"])
        prompt = self.prompts["twitter"].format(headline=headline, summary=summary, key_insights=key_insights, hashtags=hashtags)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens["twitter"],
                messages=[{"role": "user", "content": prompt}],
            )
            tweets = self._parse_response(response.content[0].text, expect_list=True)
            result = [Tweet(text=tweet, order=i) for i, tweet in enumerate(tweets) if len(str(tweet)) <= 280]
            logger.info(f"Generated {len(result)} tweets")
            return result
        except Exception as e:
            logger.error(f"Twitter thread generation failed: {e}")
            return []

    def _parse_response(self, text: str, expect_list: bool = False) -> dict | list:
        """Parse Claude response as JSON.

        Args:
            text: Raw response text.
            expect_list: If True, expect a list; otherwise, expect a dict.

        Returns:
            Parsed JSON or empty dict/list on failure.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return [] if expect_list else {}
