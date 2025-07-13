from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Company:
    """Represents a company with data source details."""
    name: str
    youtube_channels: List[str]
    rss_feed: Optional[str]
    keywords: List[str]


@dataclass
class Transcript:
    """Represents a transcript from a video or press release."""
    content: str
    company: str
    source_id: str
    title: str
    published_at: datetime
    source_type: str  # 'youtube' or 'rss'


@dataclass
class Analysis:
    """Represents an analysis result from Claude."""
    metrics: Dict
    strategy: Dict
    trends: Dict
    consumer_insights: Dict
    tech_observations: Dict
    operations: Dict
    outlook: Dict
    error: Optional[str] = None


@dataclass
class Article:
    """Represents a generated news article."""
    headline: str
    summary: str
    body: str
    key_insights: List[str]
    error: Optional[str] = None


@dataclass
class Tweet:
    """Represents a single tweet in a thread."""
    text: str
    order: int
