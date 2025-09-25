# RetailXAI Outputs Manual

This guide shows where generated outputs live and how to export or publish them to Substack, X (Twitter), LinkedIn, and others.

## Output locations

- Articles (Markdown + JSON): `articles/`
  - Example: `articles/{headline}_{timestamp}.md`
  - Metadata JSON: `articles/{headline}_{timestamp}.json`
- Logs: `logs/retailxai.log`
- Static site (when exported): `frontend/out/`

## How to export articles

1) List latest articles
```bash
ls -1 articles | tail -20
```

2) View an article
```bash
less articles/Your_Headline_2025-09-13_004156.md | cat
```

3) Copy to clipboard (macOS)
```bash
pbcopy < articles/Your_Headline_2025-09-13_004156.md
```

## Publish to Substack

- Manual: paste Markdown into Substack editor.
- Automated (via email-to-Substack): set `SUBSTACK_EMAIL` and use `publish_api.py`.
```bash
python publish_api.py substack --file articles/Your_Headline_*.md --to "$SUBSTACK_EMAIL"
```

## Publish to X (Twitter)

- Set env vars in `.env`: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`.
- Use summary mode to keep under length.
```bash
python publish_api.py x --file articles/Your_Headline_*.md --mode summary
```

## Publish to LinkedIn

- Set `LINKEDIN_API_KEY` and auth details.
```bash
python publish_api.py linkedin --file articles/Your_Headline_*.md --mode article
```

## Generate and export static site

```bash
cd frontend
npm run build && npm run export
open out/index.html
```

## Where to configure companies and sources

- CLI helper:
```bash
python edit_companies_sources.py list-companies
python edit_companies_sources.py list-sources
python edit_companies_sources.py list-symbols
```
- Files: `config/companies.yaml`, `config/sources.json`, `config/config.yaml`

## Troubleshooting

- No articles: check logs `tail -f logs/retailxai.log`
- Health: `GET /api/health/summary`, `/api/health/detailed`, `/api/health/sla`
- Jobs: `GET /api/jobs` and `POST /api/jobs/{id}/retry`

# RetailXAI Agent Framework

This document describes the comprehensive agent framework added to RetailXAI, which extends data collection, processing, and publishing capabilities through a modular, scalable architecture.

## Overview

The RetailXAI agent framework consists of three main types of agents:

1. **Data Collection Agents** - Collect content from various sources
2. **Processing Agents** - Analyze and extract insights from collected data
3. **Publishing Agents** - Distribute content and notifications to various platforms

## Architecture

### Base Agent Class

All agents inherit from the `BaseAgent` class which provides:
- Configuration management
- Retry logic with exponential backoff
- Graceful shutdown handling
- Status tracking and monitoring
- Standardized result format

### Agent Manager

The `AgentManager` class orchestrates all agents and provides:
- Agent lifecycle management
- Pipeline execution
- Status monitoring
- Configuration loading
- Data flow coordination

## Available Agents

### Data Collection Agents

#### 1. LinkedIn Agent (`LinkedInAgent`)
- **Purpose**: Collects posts from company LinkedIn pages
- **Configuration**:
  ```yaml
  linkedin_collector:
    enabled: false
    config:
      api_key: ${LINKEDIN_API_KEY}
  ```
- **Dependencies**: LinkedIn API access
- **Output**: LinkedIn posts as Transcript entities

#### 2. News API Agent (`NewsAPIAgent`)
- **Purpose**: Collects news articles about companies
- **Configuration**:
  ```yaml
  news_api_collector:
    enabled: false
    config:
      api_key: ${NEWS_API_KEY}
  ```
- **Dependencies**: News API subscription
- **Output**: News articles as Transcript entities

#### 3. Reddit Agent (`RedditAgent`)
- **Purpose**: Collects Reddit posts mentioning companies
- **Configuration**:
  ```yaml
  reddit_collector:
    enabled: false
    config:
      client_id: ${REDDIT_CLIENT_ID}
      client_secret: ${REDDIT_CLIENT_SECRET}
      subreddits:
        - investing
        - stocks
        - business
  ```
- **Dependencies**: Reddit API credentials
- **Output**: Reddit posts as Transcript entities

#### 4. Earnings Agent (`EarningsAgent`)
- **Purpose**: Specialized collection of earnings calls and financial documents
- **Configuration**:
  ```yaml
  earnings_collector:
    enabled: true
    config:
      sec_api_key: ${SEC_API_KEY}  # Optional
  ```
- **Dependencies**: None (can work with public sources)
- **Output**: Earnings documents as Transcript entities

### Processing Agents

#### 1. Sentiment Agent (`SentimentAgent`)
- **Purpose**: Analyzes sentiment in collected content
- **Features**:
  - TextBlob-based sentiment analysis (default)
  - Optional Claude API integration for advanced analysis
  - Company-specific sentiment tracking
  - Key phrase extraction with sentiment scores
- **Configuration**:
  ```yaml
  sentiment_analyzer:
    enabled: true
    config:
      use_claude: false
      claude_api_key: ${CLAUDE_API_KEY}
  ```
- **Output**: Sentiment analysis results with polarity, confidence, and key phrases

#### 2. Competitor Agent (`CompetitorAgent`)
- **Purpose**: Analyzes competitive landscape and competitor mentions
- **Features**:
  - Competitor mention detection
  - Context extraction around mentions
  - Competitive positioning analysis
  - Competitive theme identification
- **Configuration**:
  ```yaml
  competitor_analyzer:
    enabled: true
    config:
      competitor_mapping:
        "Walmart": ["Target", "Amazon", "Costco"]
  ```
- **Output**: Competitor analysis with mentions, themes, and positioning

#### 3. Trend Agent (`TrendAgent`)
- **Purpose**: Identifies and analyzes market trends
- **Features**:
  - Predefined trend category tracking
  - Emerging trend detection
  - Cross-company trend aggregation
  - Trend scoring and ranking
- **Configuration**:
  ```yaml
  trend_analyzer:
    enabled: true
    config:
      trend_keywords:
        technology: [AI, automation, digital]
        sustainability: [green, ESG, carbon]
  ```
- **Output**: Trend analysis with category scores and emerging trends

### Publishing Agents

#### 1. LinkedIn Publisher (`LinkedInPublisher`)
- **Purpose**: Publishes content to LinkedIn company pages
- **Features**:
  - Draft mode for review before publishing
  - Article formatting for LinkedIn
  - Character limit handling
  - Hashtag integration
- **Configuration**:
  ```yaml
  linkedin_publisher:
    enabled: false
    config:
      access_token: ${LINKEDIN_ACCESS_TOKEN}
      company_id: ${LINKEDIN_COMPANY_ID}
      draft_mode: true
  ```
- **Output**: Published posts or draft files

#### 2. Slack Agent (`SlackAgent`)
- **Purpose**: Sends notifications and reports to Slack
- **Features**:
  - Multiple notification types (daily summary, alerts, trends)
  - Rich message formatting with blocks and attachments
  - Webhook and bot token support
  - Channel-specific routing
- **Configuration**:
  ```yaml
  slack_notifier:
    enabled: false
    config:
      webhook_url: ${SLACK_WEBHOOK_URL}
      channel: "#retailxai-notifications"
      notification_types:
        - daily_summary
        - error_alerts
        - trend_alerts
  ```
- **Output**: Slack message delivery status

## Configuration

### Agent Configuration File (`config/agents.yaml`)

The main configuration file defines:
- Which agents are enabled
- Agent-specific settings
- Retry and timeout policies
- Pipeline execution order
- Data flow parameters

### Environment Variables (`config/.env`)

New environment variables for agents:
```bash
# LinkedIn
LINKEDIN_API_KEY=your_linkedin_api_key
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_COMPANY_ID=your_company_id

# News API
NEWS_API_KEY=your_news_api_key

# Reddit
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Slack
SLACK_WEBHOOK_URL=your_slack_webhook_url
SLACK_BOT_TOKEN=your_bot_token

# Optional
SEC_API_KEY=your_sec_api_key
```

## Usage

### Using the Agent Manager

```python
from agent_manager import AgentManager
import asyncio

# Initialize agent manager
agent_manager = AgentManager("config/agents.yaml")

# Execute individual agent
result = await agent_manager.execute_agent('sentiment_analyzer', {'transcripts': transcripts})

# Execute full pipeline
pipeline_result = await agent_manager.execute_full_pipeline()

# Get agent status
status = agent_manager.get_agent_status()

# Enable/disable agents
agent_manager.enable_agent('linkedin_collector')
agent_manager.disable_agent('reddit_collector')
```

### Creating Custom Agents

```python
from agents.base_agent import BaseAgent, AgentConfig, AgentResult

class CustomAgent(BaseAgent):
    def validate_config(self) -> bool:
        # Validate agent configuration
        return True
    
    async def execute(self) -> AgentResult:
        # Implement agent logic
        try:
            # Your agent code here
            data = self._process_data()
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=data
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )
```

## Pipeline Execution

The agent framework supports three execution modes:

### 1. Individual Agent Execution
Execute specific agents on demand:
```python
result = await agent_manager.execute_agent('earnings_collector')
```

### 2. Pipeline Stage Execution
Execute agents by category:
```python
# Data collection only
collection_results = await agent_manager.execute_data_collection_pipeline()

# Processing only
processing_results = await agent_manager.execute_processing_pipeline(transcripts)

# Publishing only
publishing_results = await agent_manager.execute_publishing_pipeline(articles, summary)
```

### 3. Full Pipeline Execution
Execute complete end-to-end pipeline:
```python
pipeline_result = await agent_manager.execute_full_pipeline()
```

## Testing

Run the test script to verify agent functionality:

```bash
python test_agents.py
```

The test script will:
- Test individual agent functionality
- Verify agent manager operations
- Test pipeline execution
- Demonstrate publishing capabilities

## Monitoring and Status

### Agent Status
Each agent provides status information:
- Enabled/disabled state
- Execution count
- Error count
- Last execution time
- Current running state

### Execution History
The agent manager maintains execution history:
- Success/failure status
- Execution time
- Error messages
- Timestamp

### Example Monitoring
```python
# Get all agent status
status = agent_manager.get_agent_status()

# Get specific agent status
linkedin_status = agent_manager.get_agent_status('linkedin_collector')

# Get execution history
history = agent_manager.get_execution_history('sentiment_analyzer', limit=10)
```

## Integration with Existing System

The agent framework integrates seamlessly with the existing RetailXAI system:

1. **Scheduler Integration**: The main scheduler can trigger agent pipelines
2. **Database Integration**: Agents can store/retrieve data using existing database connections
3. **Configuration Integration**: Agents use the same configuration system
4. **Logging Integration**: All agents use the existing logging framework

### Updating Scheduler

To integrate agents with the existing scheduler, modify `scheduler.py`:

```python
from agent_manager import AgentManager

class RetailXAIScheduler:
    def __init__(self):
        # Existing initialization
        self.agent_manager = AgentManager()
    
    def daily_earnings_scan(self):
        # Replace existing logic with agent pipeline
        asyncio.run(self.agent_manager.execute_full_pipeline())
```

## Performance and Scalability

### Parallel Execution
- Data collection agents run in parallel
- Processing agents run in parallel after data collection
- Publishing agents run in parallel after processing

### Resource Management
- Configurable timeouts for each agent
- Retry logic with exponential backoff
- Graceful shutdown handling
- Memory-efficient data processing

### Monitoring
- Execution time tracking
- Error rate monitoring
- Status reporting
- Historical performance data

## Future Enhancements

Potential areas for expansion:

1. **Additional Data Sources**:
   - Instagram Business API
   - TikTok Business API
   - Discord monitoring
   - Telegram channels

2. **Advanced Processing**:
   - Image analysis agents
   - Video transcript analysis
   - Real-time stream processing
   - Machine learning model integration

3. **Enhanced Publishing**:
   - Multi-platform scheduling
   - A/B testing capabilities
   - Content personalization
   - Performance analytics

4. **Operational Features**:
   - Health check endpoints
   - Metrics collection
   - Auto-scaling capabilities
   - Configuration hot-reloading

## Troubleshooting

### Common Issues

1. **Agent Not Starting**:
   - Check configuration file syntax
   - Verify environment variables
   - Check API credentials

2. **API Rate Limits**:
   - Implement appropriate delays
   - Use multiple API keys if available
   - Implement caching strategies

3. **Memory Issues**:
   - Process data in batches
   - Implement data cleanup
   - Monitor memory usage

4. **Network Timeouts**:
   - Increase timeout settings
   - Implement retry logic
   - Check network connectivity

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check agent status:
```python
status = agent_manager.get_agent_status()
print(status)
```

Review execution history:
```python
history = agent_manager.get_execution_history()
for result in history:
    if not result.success:
        print(f"Error in {result.agent_name}: {result.error}")
```

This comprehensive agent framework significantly extends RetailXAI's capabilities while maintaining the existing architecture and design principles.