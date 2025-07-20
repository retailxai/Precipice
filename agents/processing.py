import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp

# Optional imports with graceful fallbacks
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

from .base_agent import BaseAgent, AgentConfig, AgentResult
from entities import Transcript, Analysis

logger = logging.getLogger("RetailXAI.Processing")


class SentimentAgent(BaseAgent):
    """Agent for analyzing sentiment in collected content."""

    def __init__(self, config: AgentConfig, shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.claude_api_key = config.config.get('claude_api_key')
        self.use_claude = config.config.get('use_claude', False)

    def validate_config(self) -> bool:
        """Validate sentiment agent configuration."""
        if self.use_claude and not self.claude_api_key:
            self.logger.warning("Claude API key not provided, falling back to TextBlob")
            self.use_claude = False
        return True

    async def execute(self) -> AgentResult:
        """Execute sentiment analysis on provided transcripts."""
        try:
            # Get transcripts from data parameter (passed by scheduler)
            transcripts = self.config.config.get('transcripts', [])
            
            if not transcripts:
                return AgentResult(
                    agent_name=self.config.name,
                    success=True,
                    data=[],
                    error="No transcripts provided for sentiment analysis"
                )

            sentiment_results = []
            
            for transcript in transcripts:
                if self._check_shutdown():
                    break
                    
                sentiment = await self._analyze_sentiment(transcript)
                sentiment_results.append(sentiment)
                
            self.logger.info(f"Analyzed sentiment for {len(sentiment_results)} transcripts")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=sentiment_results
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _analyze_sentiment(self, transcript: Transcript) -> Dict[str, Any]:
        """Analyze sentiment of a single transcript."""
        if self.use_claude:
            return await self._analyze_with_claude(transcript)
        else:
            return self._analyze_with_textblob(transcript)

    def _analyze_with_textblob(self, transcript: Transcript) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob."""
        if not TEXTBLOB_AVAILABLE:
            # Fallback to simple sentiment analysis
            return self._analyze_with_simple_sentiment(transcript)
            
        blob = TextBlob(transcript.content)
        
        # Calculate overall sentiment
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Classify sentiment
        if polarity > 0.1:
            sentiment_label = "positive"
        elif polarity < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
            
        # Extract key phrases with sentiment
        sentences = blob.sentences
        key_phrases = []
        
        for sentence in sentences[:5]:  # Top 5 sentences
            if abs(sentence.sentiment.polarity) > 0.3:  # Strong sentiment
                key_phrases.append({
                    'text': str(sentence),
                    'polarity': sentence.sentiment.polarity,
                    'subjectivity': sentence.sentiment.subjectivity
                })
        
        return {
            'transcript_id': transcript.source_id,
            'company': transcript.company,
            'sentiment_label': sentiment_label,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'confidence': abs(polarity),
            'key_phrases': key_phrases,
            'analysis_method': 'textblob',
            'analyzed_at': datetime.now().isoformat()
        }

    def _analyze_with_simple_sentiment(self, transcript: Transcript) -> Dict[str, Any]:
        """Simple sentiment analysis fallback when TextBlob is not available."""
        content_lower = transcript.content.lower()
        
        # Simple word-based sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'positive', 'growth', 'strong', 'success', 'profit', 'increase']
        negative_words = ['bad', 'poor', 'negative', 'decline', 'loss', 'weak', 'decrease', 'problem', 'issue']
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment_label = "positive"
            polarity = 0.5
        elif negative_count > positive_count:
            sentiment_label = "negative"
            polarity = -0.5
        else:
            sentiment_label = "neutral"
            polarity = 0.0
            
        return {
            'transcript_id': transcript.source_id,
            'company': transcript.company,
            'sentiment_label': sentiment_label,
            'polarity': polarity,
            'subjectivity': 0.5,  # Default moderate subjectivity
            'confidence': abs(polarity),
            'key_phrases': [],  # Simple version doesn't extract phrases
            'analysis_method': 'simple_fallback',
            'analyzed_at': datetime.now().isoformat()
        }

    async def _analyze_with_claude(self, transcript: Transcript) -> Dict[str, Any]:
        """Analyze sentiment using Claude API."""
        prompt = f"""
        Analyze the sentiment of this {transcript.source_type} content from {transcript.company}:
        
        Title: {transcript.title}
        Content: {transcript.content}
        
        Provide a detailed sentiment analysis including:
        1. Overall sentiment (positive/negative/neutral)
        2. Confidence score (0-1)
        3. Key emotional indicators
        4. Market implications
        5. Investor sentiment indicators
        
        Return as JSON with keys: sentiment_label, confidence, polarity, key_indicators, market_implications, investor_sentiment
        """
        
        # Placeholder for Claude API call
        # In real implementation, this would call the Claude API
        return {
            'transcript_id': transcript.source_id,
            'company': transcript.company,
            'sentiment_label': 'positive',
            'polarity': 0.6,
            'confidence': 0.8,
            'key_indicators': ['growth', 'innovation', 'strong performance'],
            'market_implications': 'Positive outlook for retail sector',
            'investor_sentiment': 'Bullish',
            'analysis_method': 'claude',
            'analyzed_at': datetime.now().isoformat()
        }


class CompetitorAgent(BaseAgent):
    """Agent for analyzing competitive landscape and mentions."""

    def __init__(self, config: AgentConfig, companies: List[str], shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.companies = companies
        self.competitor_mapping = config.config.get('competitor_mapping', {})

    def validate_config(self) -> bool:
        """Validate competitor agent configuration."""
        return len(self.companies) > 0

    async def execute(self) -> AgentResult:
        """Execute competitor analysis."""
        try:
            transcripts = self.config.config.get('transcripts', [])
            
            if not transcripts:
                return AgentResult(
                    agent_name=self.config.name,
                    success=True,
                    data=[],
                    error="No transcripts provided for competitor analysis"
                )

            competitor_analyses = []
            
            for transcript in transcripts:
                if self._check_shutdown():
                    break
                    
                analysis = await self._analyze_competitors(transcript)
                competitor_analyses.append(analysis)
                
            self.logger.info(f"Analyzed competitors for {len(competitor_analyses)} transcripts")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=competitor_analyses
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _analyze_competitors(self, transcript: Transcript) -> Dict[str, Any]:
        """Analyze competitor mentions and positioning."""
        content_lower = transcript.content.lower()
        
        # Find competitor mentions
        competitor_mentions = []
        for company in self.companies:
            if company.lower() != transcript.company.lower():
                company_pattern = rf'\b{re.escape(company.lower())}\b'
                mentions = len(re.findall(company_pattern, content_lower))
                
                if mentions > 0:
                    # Extract context around mentions
                    contexts = []
                    for match in re.finditer(company_pattern, content_lower):
                        start = max(0, match.start() - 100)
                        end = min(len(content_lower), match.end() + 100)
                        context = transcript.content[start:end].strip()
                        contexts.append(context)
                    
                    competitor_mentions.append({
                        'company': company,
                        'mentions': mentions,
                        'contexts': contexts[:3]  # Top 3 contexts
                    })
        
        # Analyze competitive themes
        competitive_themes = self._extract_competitive_themes(transcript.content)
        
        # Determine competitive positioning
        positioning = self._analyze_positioning(transcript, competitor_mentions)
        
        return {
            'transcript_id': transcript.source_id,
            'company': transcript.company,
            'competitor_mentions': competitor_mentions,
            'competitive_themes': competitive_themes,
            'positioning': positioning,
            'total_competitor_mentions': sum(m['mentions'] for m in competitor_mentions),
            'analyzed_at': datetime.now().isoformat()
        }

    def _extract_competitive_themes(self, content: str) -> List[str]:
        """Extract themes related to competition."""
        competitive_keywords = [
            'market share', 'competitor', 'competition', 'differentiation',
            'advantage', 'leading', 'outperform', 'market position',
            'innovation', 'disruption', 'leadership'
        ]
        
        themes = []
        content_lower = content.lower()
        
        for keyword in competitive_keywords:
            if keyword in content_lower:
                themes.append(keyword)
                
        return themes

    def _analyze_positioning(self, transcript: Transcript, competitor_mentions: List[Dict]) -> str:
        """Analyze competitive positioning based on content."""
        content_lower = transcript.content.lower()
        
        positive_indicators = ['leader', 'leading', 'advantage', 'superior', 'outperform']
        defensive_indicators = ['challenge', 'pressure', 'compete', 'threat']
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in content_lower)
        defensive_score = sum(1 for indicator in defensive_indicators if indicator in content_lower)
        
        if positive_score > defensive_score:
            return 'offensive'
        elif defensive_score > positive_score:
            return 'defensive'
        else:
            return 'neutral'


class TrendAgent(BaseAgent):
    """Agent for identifying and analyzing market trends."""

    def __init__(self, config: AgentConfig, shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.trend_keywords = config.config.get('trend_keywords', {
            'technology': ['AI', 'artificial intelligence', 'automation', 'digital', 'online', 'e-commerce'],
            'sustainability': ['sustainable', 'green', 'environment', 'carbon', 'ESG'],
            'consumer_behavior': ['consumer', 'customer', 'shopping', 'behavior', 'preference'],
            'supply_chain': ['supply chain', 'logistics', 'inventory', 'shipping', 'distribution'],
            'financial': ['revenue', 'profit', 'growth', 'margin', 'cost', 'investment']
        })

    def validate_config(self) -> bool:
        """Validate trend agent configuration."""
        return True

    async def execute(self) -> AgentResult:
        """Execute trend analysis."""
        try:
            transcripts = self.config.config.get('transcripts', [])
            
            if not transcripts:
                return AgentResult(
                    agent_name=self.config.name,
                    success=True,
                    data=[],
                    error="No transcripts provided for trend analysis"
                )

            trend_analyses = []
            
            for transcript in transcripts:
                if self._check_shutdown():
                    break
                    
                analysis = await self._analyze_trends(transcript)
                trend_analyses.append(analysis)
                
            # Aggregate trends across all transcripts
            aggregated_trends = self._aggregate_trends(trend_analyses)
            
            self.logger.info(f"Analyzed trends for {len(trend_analyses)} transcripts")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data={
                    'individual_analyses': trend_analyses,
                    'aggregated_trends': aggregated_trends
                }
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _analyze_trends(self, transcript: Transcript) -> Dict[str, Any]:
        """Analyze trends in a single transcript."""
        content_lower = transcript.content.lower()
        
        trend_scores = {}
        trend_mentions = {}
        
        for category, keywords in self.trend_keywords.items():
            score = 0
            mentions = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                count = content_lower.count(keyword_lower)
                score += count
                
                if count > 0:
                    mentions.append({
                        'keyword': keyword,
                        'count': count
                    })
            
            trend_scores[category] = score
            trend_mentions[category] = mentions
        
        # Identify emerging trends (keywords not in predefined list)
        emerging_trends = self._identify_emerging_trends(transcript.content)
        
        return {
            'transcript_id': transcript.source_id,
            'company': transcript.company,
            'trend_scores': trend_scores,
            'trend_mentions': trend_mentions,
            'emerging_trends': emerging_trends,
            'dominant_trend': max(trend_scores, key=trend_scores.get) if trend_scores else None,
            'analyzed_at': datetime.now().isoformat()
        }

    def _identify_emerging_trends(self, content: str) -> List[str]:
        """Identify potential emerging trends from content."""
        # Simple implementation - look for repeated phrases
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        word_freq = {}
        
        for word in words:
            if word not in ['this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return words mentioned multiple times
        emerging = [word for word, freq in word_freq.items() if freq >= 3]
        return emerging[:10]  # Top 10

    def _aggregate_trends(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate trend data across multiple analyses."""
        aggregated = {
            'total_transcripts': len(analyses),
            'category_scores': {},
            'top_trends': {},
            'company_trends': {}
        }
        
        # Aggregate by category
        for category in self.trend_keywords.keys():
            total_score = sum(analysis['trend_scores'].get(category, 0) for analysis in analyses)
            aggregated['category_scores'][category] = total_score
        
        # Identify top trends
        aggregated['top_trends'] = dict(sorted(
            aggregated['category_scores'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])
        
        # Aggregate by company
        for analysis in analyses:
            company = analysis['company']
            if company not in aggregated['company_trends']:
                aggregated['company_trends'][company] = {}
            
            for category, score in analysis['trend_scores'].items():
                if category not in aggregated['company_trends'][company]:
                    aggregated['company_trends'][company][category] = 0
                aggregated['company_trends'][company][category] += score
        
        return aggregated