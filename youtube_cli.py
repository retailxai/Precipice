#!/usr/bin/env python3
"""
YouTube CLI Tool for RetailXAI
Transcribes YouTube videos and generates AI summaries for Substack publishing
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from youtube_transcription_service import YouTubeTranscriptionService, TranscriptionResult
from claude_processor import ClaudeProcessor
from publish_api import PublishingAPI

# Load environment variables
load_dotenv('config/.env')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RetailXAI.YouTubeCLI')


class YouTubeCLI:
    """CLI tool for YouTube video transcription and AI summary generation."""
    
    def __init__(self):
        """Initialize the CLI tool."""
        self.transcription_service = YouTubeTranscriptionService()
        self.claude_processor = self._setup_claude()
        self.publish_api = PublishingAPI()
        
    def _setup_claude(self) -> Optional[ClaudeProcessor]:
        """Set up Claude processor with prompts."""
        try:
            api_key = os.getenv('CLAUDE_API_KEY')
            if not api_key:
                logger.error("CLAUDE_API_KEY not found in environment")
                return None
                
            prompts = {
                "analysis": """
Analyze this YouTube video transcript for retail/earnings insights:

Company: {company}
Content: {content}

Provide analysis in JSON format with:
- metrics: sentiment, confidence, key_figures
- strategy: growth, market_share, competitive_position
- trends: ecommerce, supply_chain, consumer_behavior
- consumer_insights: preferences, spending_patterns
- tech_observations: automation, digital_transformation
- operations: efficiency, cost_management
- outlook: forecast, risks, opportunities
""",
                "article": """
Create a professional news article from this analysis:

Theme: {title_theme}
Analysis: {analyses_json}

Generate JSON with:
- headline: compelling news headline
- summary: 2-3 sentence executive summary
- body: full article content (500-800 words)
- key_insights: list of 3-5 key takeaways
""",
                "twitter": """
Create a Twitter thread from this article:

Headline: {headline}
Summary: {summary}
Key Insights: {key_insights}
Hashtags: {hashtags}

Generate 3-5 tweets as a JSON array of strings, each under 280 characters.
"""
            }
            
            return ClaudeProcessor(
                api_key=api_key,
                model="claude-3-sonnet-20240229",
                prompts=prompts
            )
        except Exception as e:
            logger.error(f"Failed to setup Claude processor: {e}")
            return None
    
    def process_video(self, video_url: str, company: str = "Unknown", 
                     title_theme: str = "Retail Analysis", 
                     publish_to: Optional[str] = None,
                     output_dir: str = ".") -> Dict:
        """Process a YouTube video: transcribe, analyze, and optionally publish.
        
        Args:
            video_url: YouTube video URL
            company: Company name for analysis context
            title_theme: Theme for article generation
            publish_to: Optional publishing channel (substack, twitter, linkedin)
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "video_url": video_url,
            "company": company,
            "title_theme": title_theme,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "steps": {}
        }
        
        try:
            # Step 1: Transcribe video
            logger.info(f"Transcribing video: {video_url}")
            transcript_result = self.transcription_service.transcribe_video(video_url)
            
            if not transcript_result:
                results["error"] = "Transcription failed"
                return results
                
            results["steps"]["transcription"] = {
                "success": True,
                "method": transcript_result.method,
                "confidence": transcript_result.confidence,
                "duration": transcript_result.duration,
                "title": transcript_result.title
            }
            
            # Step 2: Analyze with AI
            if not self.claude_processor:
                results["error"] = "Claude processor not available"
                return results
                
            logger.info(f"Analyzing transcript for {company}")
            analysis = self.claude_processor.analyze_transcript(
                transcript_result.transcript, 
                company
            )
            
            results["steps"]["analysis"] = {
                "success": True,
                "sentiment": analysis.sentiment,
                "confidence": analysis.confidence,
                "error": analysis.error
            }
            
            # Step 3: Generate article
            logger.info("Generating article")
            article = self.claude_processor.generate_article([analysis], title_theme)
            
            results["steps"]["article"] = {
                "success": True,
                "headline": article.headline,
                "summary": article.summary,
                "key_insights_count": len(article.key_insights),
                "error": article.error
            }
            
            # Step 4: Save outputs
            self._save_outputs(transcript_result, analysis, article, results, output_dir)
            
            # Step 5: Publish if requested
            if publish_to:
                logger.info(f"Publishing to {publish_to}")
                publish_result = self._publish_article(article, publish_to)
                results["steps"]["publish"] = publish_result
            
            results["success"] = True
            results["outputs"] = {
                "transcript_file": f"{output_dir}/transcripts/{transcript_result.video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "analysis_file": f"{output_dir}/analyses/{transcript_result.video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "article_file": f"{output_dir}/articles/{transcript_result.video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            }
            
            logger.info("Video processing completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            results["error"] = str(e)
            return results
    
    def _save_outputs(self, transcript: TranscriptionResult, analysis, article, results: Dict, output_dir: str = "."):
        """Save all outputs to files."""
        try:
            # Create output directories
            Path(f"{output_dir}/transcripts").mkdir(parents=True, exist_ok=True)
            Path(f"{output_dir}/analyses").mkdir(parents=True, exist_ok=True)
            Path(f"{output_dir}/articles").mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = f"{transcript.video_id}_{timestamp}"
            
            # Save transcript
            transcript_file = f"{output_dir}/transcripts/{base_name}.txt"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"Title: {transcript.title}\n")
                f.write(f"Duration: {transcript.duration} seconds\n")
                f.write(f"Method: {transcript.method}\n")
                f.write(f"Confidence: {transcript.confidence}\n")
                f.write(f"Timestamp: {transcript.timestamp}\n")
                f.write("\n" + "="*50 + "\n")
                f.write("TRANSCRIPT:\n")
                f.write("="*50 + "\n")
                f.write(transcript.transcript)
            
            # Save analysis
            analysis_file = f"{output_dir}/analyses/{base_name}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "video_id": transcript.video_id,
                    "company": results["company"],
                    "timestamp": results["timestamp"],
                    "sentiment": analysis.sentiment,
                    "confidence": analysis.confidence,
                    "metrics": analysis.metrics,
                    "strategy": analysis.strategy,
                    "trends": analysis.trends,
                    "consumer_insights": analysis.consumer_insights,
                    "tech_observations": analysis.tech_observations,
                    "operations": analysis.operations,
                    "outlook": analysis.outlook,
                    "error": analysis.error
                }, indent=2)
            
            # Save article
            article_file = f"{output_dir}/articles/{base_name}.md"
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(f"# {article.headline}\n\n")
                f.write(f"**Summary:** {article.summary}\n\n")
                f.write(f"**Company:** {results['company']}\n")
                f.write(f"**Video:** {results['video_url']}\n")
                f.write(f"**Generated:** {results['timestamp']}\n\n")
                f.write("---\n\n")
                f.write(article.body)
                f.write("\n\n## Key Insights\n\n")
                for insight in article.key_insights:
                    f.write(f"- {insight}\n")
                f.write(f"\n\n---\n*Generated by RetailXAI YouTube CLI*")
            
            results["steps"]["save_outputs"] = {
                "success": True,
                "transcript_file": transcript_file,
                "analysis_file": analysis_file,
                "article_file": article_file
            }
            
        except Exception as e:
            logger.error(f"Failed to save outputs: {e}")
            results["steps"]["save_outputs"] = {
                "success": False,
                "error": str(e)
            }
    
    def _publish_article(self, article, channel: str) -> Dict:
        """Publish article to specified channel."""
        try:
            # Create article data structure
            article_data = {
                "headline": article.headline,
                "summary": article.summary,
                "body": article.body,
                "key_insights": article.key_insights
            }
            
            if channel == "substack":
                return self.publish_api.publish_to_substack(article_data, 0)
            elif channel == "twitter":
                return self.publish_api.publish_to_twitter(article.summary, 0)
            elif channel == "linkedin":
                return self.publish_api.publish_to_linkedin(article_data, 0)
            else:
                return {"success": False, "error": f"Unknown channel: {channel}"}
                
        except Exception as e:
            logger.error(f"Publishing failed: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="YouTube CLI Tool for RetailXAI - Transcribe and analyze YouTube videos"
    )
    
    parser.add_argument(
        "video_url",
        help="YouTube video URL to process"
    )
    
    parser.add_argument(
        "--company", "-c",
        default="Unknown",
        help="Company name for analysis context (default: Unknown)"
    )
    
    parser.add_argument(
        "--theme", "-t",
        default="Retail Analysis",
        help="Article theme/title (default: Retail Analysis)"
    )
    
    parser.add_argument(
        "--publish", "-p",
        choices=["substack", "twitter", "linkedin"],
        help="Publish to specified channel"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file for results (JSON format)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--output-dir", "-d",
        default=".",
        help="Output directory for generated files (default: current directory)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize CLI
    cli = YouTubeCLI()
    
    # Process video
    print(f"🎥 Processing YouTube video: {args.video_url}")
    print(f"🏢 Company: {args.company}")
    print(f"📝 Theme: {args.theme}")
    if args.publish:
        print(f"📤 Publishing to: {args.publish}")
    print()
    
    results = cli.process_video(
        video_url=args.video_url,
        company=args.company,
        title_theme=args.theme,
        publish_to=args.publish,
        output_dir=args.output_dir
    )
    
    # Display results
    if results["success"]:
        print("✅ Processing completed successfully!")
        print()
        
        if "outputs" in results:
            print("📁 Output files:")
            for output_type, file_path in results["outputs"].items():
                print(f"  {output_type}: {file_path}")
        
        if args.publish and "steps" in results and "publish" in results["steps"]:
            publish_result = results["steps"]["publish"]
            if publish_result["success"]:
                print(f"📤 Published to {args.publish}: {publish_result.get('message', 'Success')}")
            else:
                print(f"❌ Publishing failed: {publish_result.get('error', 'Unknown error')}")
        
        print()
        print("📊 Processing steps:")
        for step, step_result in results["steps"].items():
            status = "✅" if step_result.get("success", False) else "❌"
            print(f"  {status} {step}")
            
    else:
        print("❌ Processing failed!")
        if "error" in results:
            print(f"Error: {results['error']}")
        
        print()
        print("📊 Processing steps:")
        for step, step_result in results["steps"].items():
            status = "✅" if step_result.get("success", False) else "❌"
            print(f"  {status} {step}")
            if not step_result.get("success", False) and "error" in step_result:
                print(f"    Error: {step_result['error']}")
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
