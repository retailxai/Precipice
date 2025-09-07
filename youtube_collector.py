import datetime
import json
import logging
import os
from typing import List, Optional
import threading

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi

from entities import Company, Transcript
from circuit_breaker import get_circuit_breaker, API_CONFIGS, CircuitBreakerOpenException

logger = logging.getLogger("RetailXAI.YouTubeCollector")


class YouTubeCollector:
    """Collects video transcripts from YouTube for specified companies."""

    def __init__(self, api_key: str, companies: List[Company], shutdown_event: Optional[threading.Event] = None):
        """Initialize YouTubeCollector with API key and companies.

        Args:
            api_key: YouTube API key.
            companies: List of Company entities.
            shutdown_event: Event for graceful shutdown.
        """
        self.youtube = build("youtube", "v3", developerKey=api_key)
        self.companies = companies
        self.shutdown_event = shutdown_event
        self.quota_file = "logs/youtube_quota_usage.json"
        self.circuit_breaker = get_circuit_breaker("youtube", API_CONFIGS["youtube"])
        self._load_quota_usage()

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping YouTube operations")
            return True
        return False

    def _load_quota_usage(self) -> dict:
        """Load YouTube API quota usage from file."""
        if not os.path.exists(self.quota_file):
            return {}
        try:
            with open(self.quota_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load quota usage: {e}")
            return {}

    def _save_quota_usage(self, usage_data: dict) -> None:
        """Save YouTube API quota usage to file."""
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
        try:
            with open(self.quota_file, "w", encoding="utf-8") as f:
                json.dump(usage_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save quota usage: {e}")

    def _increment_quota_usage(self, count: int = 1) -> None:
        """Increment API quota usage for today."""
        usage_data = self._load_quota_usage()
        today = datetime.date.today().isoformat()
        usage_data[today] = usage_data.get(today, 0) + count
        self._save_quota_usage(usage_data)

    def get_transcripts(self) -> List[Transcript]:
        """Fetch transcripts for earnings calls from company channels and keywords.

        Returns:
            List of Transcript entities.
        """
        if self._check_shutdown():
            return []

        transcripts = []
        for company in self.companies:
            if self._check_shutdown():
                break

            # Search by company name and keywords
            for keyword in company.keywords:
                query = f"{company.name} {keyword}"
                videos = self._search_youtube(query)
                for video in videos:
                    transcript = self._get_transcript(video["videoId"], company.name)
                    if transcript:
                        transcripts.append(transcript)

            # Search by YouTube channels
            for channel_id in company.youtube_channels:
                videos = self._get_videos_for_channel(channel_id)
                for video in videos:
                    transcript = self._get_transcript(video["videoId"], company.name)
                    if transcript:
                        transcripts.append(transcript)

        logger.info(f"Collected {len(transcripts)} transcripts")
        return transcripts

    def _search_youtube(self, query: str, max_results: int = 5) -> List[dict]:
        """Search YouTube for videos matching the query.

        Args:
            query: Search query.
            max_results: Maximum number of results.

        Returns:
            List of video metadata dictionaries.
        """
        if self._check_shutdown():
            return []

        try:
            self._increment_quota_usage()
            response = self.circuit_breaker.call(
                self._execute_youtube_search,
                query=query,
                max_results=max_results
            )
            videos = [
                {
                    "videoId": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "publishedAt": item["snippet"]["publishedAt"],
                    "channelId": item["snippet"]["channelId"],
                    "channelTitle": item["snippet"]["channelTitle"],
                }
                for item in response.get("items", [])
            ]
            logger.debug(f"Found {len(videos)} videos for query: {query}")
            return videos
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for YouTube API: {e}")
            return []
        except HttpError as e:
            logger.error(f"YouTube API error during search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during YouTube search: {e}")
            return []

    def _execute_youtube_search(self, query: str, max_results: int) -> dict:
        """Execute YouTube search API call."""
        return (
            self.youtube.search()
            .list(
                q=query,
                part="id,snippet",
                maxResults=max_results,
                type="video",
                order="date",
            )
            .execute()
        )

    def _get_videos_for_channel(self, channel_id: str, max_results: int = 5) -> List[dict]:
        """Get recent videos for a YouTube channel.

        Args:
            channel_id: YouTube channel ID.
            max_results: Maximum number of results.

        Returns:
            List of video metadata dictionaries.
        """
        if self._check_shutdown():
            return []

        try:
            self._increment_quota_usage()
            response = self.circuit_breaker.call(
                self._execute_channel_search,
                channel_id=channel_id,
                max_results=max_results
            )
            videos = [
                {
                    "videoId": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "publishedAt": item["snippet"]["publishedAt"],
                    "channelId": item["snippet"]["channelId"],
                    "channelTitle": item["snippet"]["channelTitle"],
                }
                for item in response.get("items", [])
            ]
            logger.debug(f"Found {len(videos)} videos for channel: {channel_id}")
            return videos
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for YouTube API: {e}")
            return []
        except HttpError as e:
            logger.error(f"YouTube API error for channel {channel_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error for channel {channel_id}: {e}")
            return []

    def _execute_channel_search(self, channel_id: str, max_results: int) -> dict:
        """Execute YouTube channel search API call."""
        return (
            self.youtube.search()
            .list(
                channelId=channel_id,
                part="id,snippet",
                maxResults=max_results,
                order="date",
                type="video",
            )
            .execute()
        )

    def _get_transcript(self, video_id: str, company: str) -> Optional[Transcript]:
        """Fetch and validate transcript for a video.

        Args:
            video_id: YouTube video ID.
            company: Company name.

        Returns:
            Transcript entity or None if invalid.
        """
        if self._check_shutdown():
            return None

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            content = " ".join(entry["text"] for entry in transcript)
            if self._is_relevant_content(content):
                return Transcript(
                    content=content,
                    company=company,
                    source_id=video_id,
                    title="YouTube Video",
                    published_at=datetime.datetime.now(),
                    source_type="youtube",
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for video {video_id}: {e}")
            return None

    def _is_relevant_content(self, content: str) -> bool:
        """Check if transcript content is relevant to retail/earnings.

        Args:
            content: Transcript text.

        Returns:
            True if content is relevant, False otherwise.
        """
        keywords = [
            "earnings",
            "revenue",
            "sales",
            "profit",
            "growth",
            "market share",
            "consumer",
            "retail",
            "food",
            "grocery",
        ]
        return any(keyword.lower() in content.lower() for keyword in keywords)
