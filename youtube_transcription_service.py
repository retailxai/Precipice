#!/usr/bin/env python3
"""
YouTube Transcription Service
Uses multiple transcription methods to extract audio from YouTube videos
and convert it to text for analysis.
"""

import os
import logging
import tempfile
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import yt_dlp
import requests
from youtube_transcript_api import YouTubeTranscriptApi

# Optional Whisper import
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

logger = logging.getLogger("RetailXAI.YouTubeTranscription")


@dataclass
class TranscriptionResult:
    """Result of video transcription."""
    video_id: str
    title: str
    transcript: str
    duration: float
    language: str
    confidence: float
    method: str
    timestamp: datetime


class YouTubeTranscriptionService:
    """Service for transcribing YouTube videos using multiple methods."""
    
    def __init__(self, whisper_model: str = "base", temp_dir: str = "/tmp"):
        """Initialize the transcription service.
        
        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            temp_dir: Directory for temporary files
        """
        self.whisper_model = whisper_model
        self.temp_dir = temp_dir
        self.whisper_model_instance = None
        self._init_whisper()
    
    def _init_whisper(self):
        """Initialize Whisper model."""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available - skipping Whisper initialization")
            self.whisper_model_instance = None
            return
            
        try:
            self.whisper_model_instance = whisper.load_model(self.whisper_model)
            logger.info(f"Whisper model '{self.whisper_model}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model_instance = None
    
    def transcribe_video(self, video_url: str) -> Optional[TranscriptionResult]:
        """Transcribe a YouTube video using multiple methods.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            TranscriptionResult or None if all methods fail
        """
        video_id = self._extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            return None
        
        # Try multiple transcription methods in order of preference
        methods = [
            self._transcribe_with_youtube_api,
            self._transcribe_with_whisper,
            self._transcribe_with_yt_dlp
        ]
        
        for method in methods:
            try:
                result = method(video_url, video_id)
                if result and result.transcript.strip():
                    logger.info(f"Successfully transcribed video {video_id} using {result.method}")
                    return result
            except Exception as e:
                logger.warning(f"Transcription method {method.__name__} failed: {e}")
                continue
        
        logger.error(f"All transcription methods failed for video {video_id}")
        return None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        try:
            if "youtube.com/watch?v=" in url:
                return url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                return url.split("youtu.be/")[1].split("?")[0]
            return None
        except Exception:
            return None
    
    def _transcribe_with_youtube_api(self, video_url: str, video_id: str) -> Optional[TranscriptionResult]:
        """Try to get transcript using YouTube's official API."""
        try:
            # Get video info first
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
            
            # Try to get transcript
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try different languages
            for transcript in transcript_list:
                try:
                    transcript_data = transcript.fetch()
                    transcript_text = " ".join([item['text'] for item in transcript_data])
                    
                    return TranscriptionResult(
                        video_id=video_id,
                        title=title,
                        transcript=transcript_text,
                        duration=duration,
                        language=transcript.language,
                        confidence=0.9,  # High confidence for official transcripts
                        method="youtube_api",
                        timestamp=datetime.now()
                    )
                except Exception:
                    continue
            
            return None
        except Exception as e:
            logger.debug(f"YouTube API transcription failed: {e}")
            return None
    
    def _transcribe_with_whisper(self, video_url: str, video_id: str) -> Optional[TranscriptionResult]:
        """Transcribe using Whisper AI."""
        if not self.whisper_model_instance:
            return None
        
        try:
            # Download audio using yt-dlp
            temp_file = os.path.join(self.temp_dir, f"{video_id}.wav")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_file,
                'extractaudio': True,
                'audioformat': 'wav',
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
            
            # Transcribe with Whisper
            result = self.whisper_model_instance.transcribe(temp_file)
            transcript = result["text"]
            confidence = result.get("segments", [{}])[0].get("no_speech_prob", 0.1)
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return TranscriptionResult(
                video_id=video_id,
                title=title,
                transcript=transcript,
                duration=duration,
                language="en",
                confidence=1.0 - confidence,  # Convert no_speech_prob to confidence
                method="whisper",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.debug(f"Whisper transcription failed: {e}")
            return None
    
    def _transcribe_with_yt_dlp(self, video_url: str, video_id: str) -> Optional[TranscriptionResult]:
        """Fallback transcription using yt-dlp's built-in subtitle extraction."""
        try:
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                
                # Check for available subtitles
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})
                
                # Try to find English subtitles
                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in subtitles:
                        subtitle_url = subtitles[lang][0]['url']
                        break
                    elif lang in automatic_captions:
                        subtitle_url = automatic_captions[lang][0]['url']
                        break
                else:
                    return None
                
                # Download and parse subtitles
                response = requests.get(subtitle_url)
                subtitle_text = response.text
                
                # Simple parsing of VTT/SRT format
                lines = subtitle_text.split('\n')
                transcript_lines = []
                for line in lines:
                    if line.strip() and not line.startswith('WEBVTT') and not '-->' in line:
                        transcript_lines.append(line.strip())
                
                transcript = " ".join(transcript_lines)
                
                return TranscriptionResult(
                    video_id=video_id,
                    title=title,
                    transcript=transcript,
                    duration=duration,
                    language="en",
                    confidence=0.7,  # Medium confidence for auto-generated
                    method="yt_dlp",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.debug(f"yt-dlp transcription failed: {e}")
            return None
    
    def transcribe_multiple_videos(self, video_urls: List[str]) -> List[TranscriptionResult]:
        """Transcribe multiple videos.
        
        Args:
            video_urls: List of YouTube video URLs
            
        Returns:
            List of successful transcription results
        """
        results = []
        for url in video_urls:
            result = self.transcribe_video(url)
            if result:
                results.append(result)
        return results


def test_transcription_service():
    """Test the transcription service with sample videos."""
    service = YouTubeTranscriptionService()
    
    # Test with a sample video (replace with actual video URLs)
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll for testing
    ]
    
    for url in test_urls:
        print(f"Testing transcription for: {url}")
        result = service.transcribe_video(url)
        if result:
            print(f"Success! Method: {result.method}, Confidence: {result.confidence}")
            print(f"Transcript preview: {result.transcript[:200]}...")
        else:
            print("Transcription failed")


if __name__ == "__main__":
    test_transcription_service()

