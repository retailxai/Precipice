import json
import logging
import re
from typing import Dict, List, Optional
import threading

import anthropic
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from entities import Analysis, Article, Tweet
from circuit_breaker import get_circuit_breaker, API_CONFIGS, CircuitBreakerOpenException

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
        self.circuit_breaker = get_circuit_breaker("claude", API_CONFIGS["claude"])
        logger.info(f"ClaudeProcessor initialized with model: {model}")

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping Claude operations")
            return True
        return False

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
            # Use circuit breaker for API call
            response = self.circuit_breaker.call(
                self._make_claude_request,
                prompt=prompt,
                max_tokens=self.max_tokens["analysis"]
            )
            result = self._parse_response(response.content[0].text)
            
            # Extract sentiment and confidence from metrics if available
            sentiment = None
            confidence = None
            if isinstance(result, dict) and 'metrics' in result:
                metrics = result['metrics']
                sentiment = metrics.get('sentiment')
                confidence = metrics.get('confidence')
            
            # Create Analysis object with extracted values
            analysis_data = {
                'metrics': result.get('metrics', {}),
                'strategy': result.get('strategy', {}),
                'trends': result.get('trends', {}),
                'consumer_insights': result.get('consumer_insights', {}),
                'tech_observations': result.get('tech_observations', {}),
                'operations': result.get('operations', {}),
                'outlook': result.get('outlook', {}),
                'sentiment': sentiment,
                'confidence': confidence
            }
            
            logger.info(f"Analysis completed for {company}")
            return Analysis(**analysis_data)
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for Claude API: {e}")
            return self._fallback_analysis(transcript, company, "Claude API temporarily unavailable")
        except Exception as e:
            logger.error(f"Analysis failed for {company}: {e}")
            return self._fallback_analysis(transcript, company, str(e))
    
    def _fallback_analysis(self, transcript: str, company: str, error: str) -> Analysis:
        """Generate a fallback analysis when Claude API is unavailable."""
        # Simple sentiment analysis based on keywords
        positive_words = ['strong', 'growth', 'positive', 'improving', 'expanding', 'success', 'robust', 'excellent', 'outstanding']
        negative_words = ['decline', 'negative', 'weak', 'struggling', 'challenging', 'difficult', 'poor', 'disappointing']
        
        text_lower = transcript.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment (-1 to 1)
        if positive_count + negative_count == 0:
            sentiment = 0.0
        else:
            sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        
        # Calculate confidence (0 to 1)
        confidence = min(0.8, (positive_count + negative_count) / 10.0)
        
        # Determine outlook based on sentiment
        if sentiment > 0.2:
            outlook_forecast = "bullish"
        elif sentiment < -0.2:
            outlook_forecast = "bearish"
        else:
            outlook_forecast = "neutral"
        
        # Determine strategy based on sentiment
        if sentiment > 0.1:
            growth = "positive"
        elif sentiment < -0.1:
            growth = "negative"
        else:
            growth = "neutral"
        
        return Analysis(
            metrics={'sentiment': sentiment, 'confidence': confidence},
            strategy={'growth': growth, 'market_share': 'stable'},
            trends={'trend': 'stable', 'ecommerce': 'neutral', 'supply_chain': 'stable'},
            consumer_insights={'preference': 'mixed'},
            tech_observations={'automation': 'static'},
            operations={'efficiency': 'medium'},
            outlook={'forecast': outlook_forecast},
            sentiment=sentiment,
            confidence=confidence,
            error=error
        )

    def _make_claude_request(self, prompt: str, max_tokens: int):
        """Make a request to Claude API with retry logic."""
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=5),
            retry=(retry_if_exception_type(anthropic.APIConnectionError) | retry_if_exception_type(anthropic.APIError)),
        )
        def _retry_request():
            return self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        
        return _retry_request()

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
            response = self.circuit_breaker.call(
                self._make_claude_request,
                prompt=prompt,
                max_tokens=self.max_tokens["article"]
            )
            result = self._parse_response(response.content[0].text)
            logger.info(f"Article generated: {title_theme}")
            return Article(**result)
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for Claude API: {e}")
            return Article(headline="", summary="", body="", key_insights=[], error="Claude API temporarily unavailable")
        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            return Article(headline="", summary="", body="", key_insights=[], error=str(e))

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
            response = self.circuit_breaker.call(
                self._make_claude_request,
                prompt=prompt,
                max_tokens=self.max_tokens["twitter"]
            )
            tweets = self._parse_response(response.content[0].text, expect_list=True)
            result = [Tweet(text=tweet, order=i) for i, tweet in enumerate(tweets) if len(str(tweet)) <= 280]
            logger.info(f"Generated {len(result)} tweets")
            return result
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for Claude API: {e}")
            return []
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
