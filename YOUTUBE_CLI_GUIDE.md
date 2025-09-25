# YouTube CLI Tool Guide

## Overview
The YouTube CLI tool (`youtube_cli.py`) allows you to transcribe YouTube videos, generate AI-powered summaries, and publish directly to Substack, Twitter, or LinkedIn.

## Prerequisites
1. **Environment Setup**: Ensure your `.env` file contains:
   ```
   CLAUDE_API_KEY=your_claude_api_key_here
   TWITTER_CONSUMER_KEY=your_twitter_key
   TWITTER_CONSUMER_SECRET=your_twitter_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_secret
   DAILY_REPORT_SENDER=your_email@gmail.com
   DAILY_REPORT_PASSWORD=your_app_password
   DRAFT_EMAIL_RECIPIENT=recipient@example.com
   ```

2. **Dependencies**: Install required packages:
   ```bash
   pip install youtube-transcript-api yt-dlp whisper anthropic tweepy python-dotenv
   ```

## Usage

### Basic Usage
```bash
python youtube_cli.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### With Company Context
```bash
python youtube_cli.py "https://www.youtube.com/watch?v=VIDEO_ID" --company "Tesla" --theme "Q3 Earnings Analysis"
```

### With Publishing
```bash
# Publish to Substack
youtube-ai "https://www.youtube.com/watch?v=VIDEO_ID" --company "Tesla" --publish substack

# Publish to Twitter
youtube-ai "https://www.youtube.com/watch?v=VIDEO_ID" --company "Tesla" --publish twitter

# Publish to LinkedIn
youtube-ai "https://www.youtube.com/watch?v=VIDEO_ID" --company "Tesla" --publish linkedin
```

### With Custom Output Directory
```bash
# Output to specific directory
youtube-ai "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "/home/retailxai/precipice"

# Output to current directory (default)
youtube-ai "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Save Results
```bash
python youtube_cli.py "https://www.youtube.com/watch?v=VIDEO_ID" --output results.json
```

### Verbose Logging
```bash
python youtube_cli.py "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `video_url` | - | YouTube video URL (required) | - |
| `--company` | `-c` | Company name for analysis context | "Unknown" |
| `--theme` | `-t` | Article theme/title | "Retail Analysis" |
| `--publish` | `-p` | Publish to channel (substack/twitter/linkedin) | None |
| `--output` | `-o` | Save results to JSON file | None |
| `--verbose` | `-v` | Enable verbose logging | False |
| `--output-dir` | `-d` | Output directory for generated files | Current directory |

## Output Files

The tool creates three types of output files:

### 1. Transcripts (`transcripts/`)
- **Format**: `.txt`
- **Content**: Video title, duration, transcription method, confidence, full transcript
- **Example**: `transcripts/dQw4w9WgXcQ_20250113_143022.txt`

### 2. Analysis (`analyses/`)
- **Format**: `.json`
- **Content**: AI analysis with sentiment, metrics, strategy, trends, insights
- **Example**: `analyses/dQw4w9WgXcQ_20250113_143022.json`

### 3. Articles (`articles/`)
- **Format**: `.md` (Markdown)
- **Content**: Professional news article with headline, summary, body, key insights
- **Example**: `articles/dQw4w9WgXcQ_20250113_143022.md`

## Publishing Channels

### Substack
- Sends formatted HTML content via email
- Includes headline, body, key insights
- Professional newsletter format

### Twitter
- Truncates content to 280 characters
- Posts as single tweet
- Includes relevant hashtags

### LinkedIn
- Sends formatted content via email
- Includes headline, summary, key insights
- Professional business format

## Example Workflow

1. **Find a YouTube video** (earnings call, interview, etc.)
2. **Run the CLI**:
   ```bash
   python youtube_cli.py "https://www.youtube.com/watch?v=abc123" \
     --company "Walmart" \
     --theme "Q4 Earnings Deep Dive" \
     --publish substack \
     --verbose
   ```
3. **Check outputs**:
   - `articles/` - Your Substack-ready article
   - `transcripts/` - Full video transcript
   - `analyses/` - AI analysis data
4. **Review and publish** - The article is automatically sent to your Substack email

## Troubleshooting

### Common Issues

1. **"CLAUDE_API_KEY not found"**
   - Add your Claude API key to `.env` file
   - Ensure the file is in the `config/` directory

2. **"Transcription failed"**
   - Video may not have captions
   - Try a different video
   - Check if video is publicly available

3. **"Publishing failed"**
   - Check your API credentials in `.env`
   - Verify email settings for Substack/LinkedIn
   - Check Twitter API permissions

4. **"Whisper model not loaded"**
   - Install Whisper: `pip install openai-whisper`
   - Ensure sufficient disk space for models

### Debug Mode
Use `--verbose` flag to see detailed processing steps and error messages.

## Integration with RetailXAI

The CLI integrates with the main RetailXAI system:
- Uses the same Claude processor for consistency
- Follows the same analysis framework
- Outputs compatible with the main dashboard
- Can be scheduled via cron for automated processing

## Tips for Best Results

1. **Choose relevant videos**: Earnings calls, investor presentations, CEO interviews
2. **Use descriptive themes**: "Q3 Earnings Analysis", "Supply Chain Update"
3. **Provide company context**: Helps AI generate more relevant insights
4. **Review before publishing**: Always check the generated content
5. **Use verbose mode**: Helps debug any issues

## Examples

### Tesla Earnings Call
```bash
python youtube_cli.py "https://www.youtube.com/watch?v=tesla_earnings" \
  --company "Tesla" \
  --theme "Q3 2024 Earnings Analysis" \
  --publish substack
```

### Walmart Investor Day
```bash
python youtube_cli.py "https://www.youtube.com/watch?v=walmart_investor" \
  --company "Walmart" \
  --theme "Investor Day Key Takeaways" \
  --publish twitter
```

### Costco CEO Interview
```bash
python youtube_cli.py "https://www.youtube.com/watch?v=costco_interview" \
  --company "Costco" \
  --theme "CEO Interview Insights" \
  --publish linkedin
```
