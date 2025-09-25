import json
import logging
import os
import threading
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
import smtplib

import psycopg2
import tweepy

from entities import Article, Tweet

logger = logging.getLogger("RetailXAI.ContentManager")


class ContentManager:
    """Manages content publishing to Substack and Twitter."""

    def __init__(
        self,
        db_connection,
        substack_config: Dict[str, str],
        twitter_config: Dict[str, str],
        shutdown_event: Optional[threading.Event] = None,
    ):
        """Initialize ContentManager with database and publishing configs.

        Args:
            db_connection: PostgreSQL connection pool.
            substack_config: Substack configuration (draft directory, email).
            twitter_config: Twitter API credentials.
            shutdown_event: Event for graceful shutdown.
        """
        self.db = db_connection
        self.substack_config = substack_config
        self.twitter_api = self._setup_twitter(twitter_config)
        self.shutdown_event = shutdown_event
        os.makedirs(substack_config["draft_directory"], exist_ok=True)
        os.makedirs(twitter_config["draft_directory"], exist_ok=True)

    def _setup_twitter(self, config: Dict[str, str]) -> tweepy.API:
        """Set up Twitter API client.

        Args:
            config: Twitter API credentials.

        Returns:
            tweepy.API instance.
        """
        auth = tweepy.OAuthHandler(config["consumer_key"], config["consumer_secret"])
        auth.set_access_token(config["access_token"], config["access_token_secret"])
        return tweepy.API(auth)

    def quality_check(self, article: Article) -> int:
        """Evaluate article quality based on length, content, and uniqueness.

        Args:
            article: Article entity to evaluate.

        Returns:
            Quality score (1-10).
        """
        score = 5
        word_count = len(article.body.split())
        if 800 <= word_count <= 1500:
            score += 1
        if self._contains_specific_data(article.body):
            score += 1
        if self._check_readability(article.body):
            score += 1
        if not self._is_duplicate(article.headline):
            score += 1
        else:
            score -= 3
        return min(10, max(1, score))

    def publish_to_substack(self, article: Article) -> str:
        """Save Substack draft to file and optionally email it.

        Args:
            article: Article entity to publish.

        Returns:
            File path or email identifier.
        """
        if self._check_shutdown():
            logger.warning("Shutdown requested, cancelling Substack publish")
            return "shutdown-aborted"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"{self.substack_config['draft_directory']}/substack_draft_{timestamp}.html"
        json_filename = f"{self.substack_config['draft_directory']}/substack_draft_{timestamp}.json"

        # Save HTML draft
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(self._format_for_substack_file(article))
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(vars(article), f, indent=2, ensure_ascii=False)
        logger.info(f"Draft saved: HTML={html_filename}, JSON={json_filename}")

        if self.substack_config.get("email_drafts"):
            return self._email_draft_to_inbox(article, html_filename, json_filename, timestamp)
        return f"file://{os.path.abspath(html_filename).replace(os.sep, '/')}"

    def post_to_twitter(self, tweets: List[Tweet], article_url: str) -> List[str]:
        """Save Twitter thread to draft file.

        Args:
            tweets: List of Tweet entities.
            article_url: URL or file path of the associated article.

        Returns:
            List of draft file paths.
        """
        if self._check_shutdown():
            logger.warning("Shutdown requested, cancelling Twitter post")
            return []

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_filename = f"{self.substack_config['draft_directory']}/twitter_draft_{timestamp}.json"
        tweet_data = [
            {"order": tweet.order, "text": tweet.text + (f"\n\nRead more: {article_url}" if i == len(tweets) - 1 else "")}
            for i, tweet in enumerate(tweets)
        ]
        with open(draft_filename, "w", encoding="utf-8") as f:
            json.dump(tweet_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Twitter thread draft saved: {draft_filename}")
        return [f"file://{os.path.abspath(draft_filename).replace(os.sep, '/')}"]

    def _email_draft_to_inbox(self, article: Article, html_filename: str, json_filename: str, timestamp: str) -> str:
        """Email Substack draft to recipient.

        Args:
            article: Article entity.
            html_filename: Path to HTML draft.
            json_filename: Path to JSON draft.
            timestamp: Timestamp for email identifier.

        Returns:
            Email identifier or file path on failure.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.substack_config["email_user"]
            msg["To"] = self.substack_config["email_recipient"]
            msg["Subject"] = f"📝 Substack Draft: {article.headline}"

            plain_text = self._format_for_email_plain(article)
            html_content = self._format_for_email_html(article)

            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            for filename in [html_filename, json_filename]:
                with open(filename, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(filename)}")
                    msg.attach(part)

            # Use configurable SMTP settings for different email providers
            smtp_server = self.substack_config.get("smtp_server", "smtp.gmail.com")
            smtp_port = self.substack_config.get("smtp_port", 587)
            use_tls = self.substack_config.get("use_tls", True)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(self.substack_config["email_user"], self.substack_config["email_password"])
                server.send_message(msg)

            logger.info(f"Draft emailed to {self.substack_config['email_recipient']}")
            return f"emailed-to-{self.substack_config['email_recipient']}-{timestamp}"
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return f"file://{os.path.abspath(html_filename).replace(os.sep, '/')}"

    def _format_for_email_plain(self, article: Article) -> str:
        """Format article as plain text for email.

        Args:
            article: Article entity.

        Returns:
            Plain text content.
        """
        return f"""
SUBSTACK DRAFT READY
===================

Title: {article.headline}

Content:
{article.body}

---
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Word count: {len(article.body.split())} words
"""

    def _format_for_email_html(self, article: Article) -> str:
        """Format article as HTML for email.

        Args:
            article: Article entity.

        Returns:
            HTML content.
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Georgia, serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header, .footer {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .content {{ background: white; padding: 20px; border: 1px solid #e9ecef; border-radius: 8px; }}
        .title {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>📝 Substack Draft Ready</h2>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    <div class="content">
        <h1 class="title">{article.headline}</h1>
        <div>{article.body.replace(chr(10)+chr(10), '</p><p>').replace(chr(10), '<br>')}</div>
    </div>
    <div class="footer">
        <strong>Instructions:</strong>
        <ol>
            <li>Copy the content above (or use attached HTML file)</li>
            <li>Go to your Substack editor</li>
            <li>Paste and format as needed</li>
            <li>Publish when ready</li>
        </ol>
    </div>
</body>
</html>
"""

    def _format_for_substack_file(self, article: Article) -> str:
        """Format article as HTML for Substack draft.

        Args:
            article: Article entity.

        Returns:
            HTML content.
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{article.headline}</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>{article.headline}</h1>
    <div style="font-family: Georgia, serif; line-height: 1.6; max-width: 600px;">
        {article.body.replace(chr(10)+chr(10), '</p><p>').replace(chr(10), '<br>')}
    </div>
    <hr>
    <p><em>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em></p>
</body>
</html>
"""

    def _contains_specific_data(self, content: str) -> bool:
        """Check if content contains specific data indicators.

        Args:
            content: Article body.

        Returns:
            True if indicators are present, False otherwise.
        """
        indicators = [
            "%",
            "$",
            "revenue",
            "profit",
            "growth",
            "quarter",
            "earnings",
            "billion",
            "million",
            "increase",
            "decrease",
            "compared to",
        ]
        return any(indicator.lower() in content.lower() for indicator in indicators)

    def _check_readability(self, content: str) -> bool:
        """Check article readability based on sentence length.

        Args:
            content: Article body.

        Returns:
            True if readable, False otherwise.
        """
        sentences = content.split(".")
        if not sentences or len(sentences) < 2:
            return False
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        return 10 <= avg_sentence_length <= 25

    def _is_duplicate(self, headline: str) -> bool:
        """Check if headline is a duplicate in the database.

        Args:
            headline: Article headline.

        Returns:
            True if duplicate, False otherwise.
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM articles WHERE headline = %s", (headline,))
                return cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Database duplicate check failed: {e}")
            return False

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            return True
        return False
