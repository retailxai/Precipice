import pytest
from unittest.mock import patch, MagicMock

from entities import Company, Transcript
from youtube_collector import YouTubeCollector
from rss_collector import RSSCollector


@pytest.fixture
def youtube_collector():
    """Fixture for YouTubeCollector."""
    return YouTubeCollector(
        api_key="test_key",
        companies=[
            Company(name="TestCo", youtube_channels=["UC123"], rss_feed=None, keywords=["test"]),
        ],
    )


@pytest.fixture
def rss_collector():
    """Fixture for RSSCollector."""
    return RSSCollector(
        feeds=["http://example.com/rss"],
        companies=[
            Company(name="TestCo", youtube_channels=[], rss_feed=None, keywords=["test"]),
        ],
    )


@patch("googleapiclient.discovery.build")
def test_youtube_collector_search(mock_build, youtube_collector):
    """Test YouTubeCollector search functionality."""
    mock_youtube = MagicMock()
    mock_youtube.search().list().execute.return_value = {
        "items": [
            {
                "id": {"videoId": "vid123"},
                "snippet": {
                    "title": "Test Earnings",
                    "publishedAt": "2023-10-01T00:00:00Z",
                    "channelId": "UC123",
                    "channelTitle": "TestCo",
                },
            }
        ]
    }
    mock_build.return_value = mock_youtube
    videos = youtube_collector._search_youtube("TestCo test", max_results=1)
    assert len(videos) == 1
    assert videos[0]["videoId"] == "vid123"


@patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
def test_youtube_collector_transcript(mock_get_transcript, youtube_collector):
    """Test YouTubeCollector transcript fetching."""
    mock_get_transcript.return_value = [{"text": "Revenue up 10%"}]
    transcript = youtube_collector._get_transcript("vid123", "TestCo")
    assert transcript is not None
    assert transcript.company == "TestCo"
    assert "Revenue" in transcript.content


@patch("feedparser.parse")
def test_rss_collector_feed(mock_parse, rss_collector):
    """Test RSSCollector feed parsing."""
    mock_parse.return_value = {
        "entries": [
            {
                "title": "TestCo Earnings",
                "link": "http://example.com/news",
                "published": "Sun, 01 Oct 2023 00:00:00 +0000",
                "published_parsed": time.struct_time((2023, 10, 1, 0, 0, 0, 6, 274, 0)),
            }
        ]
    }
    with patch.object(rss_collector, "_extract_full_content", return_value="Sales up 5%"):
        transcripts = rss_collector.get_transcripts()
        assert len(transcripts) == 1
        assert transcripts[0].company == "TestCo"
        assert "Sales" in transcripts[0].content
