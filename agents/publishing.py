import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp

from .base_agent import BaseAgent, AgentConfig, AgentResult
from entities import Article, Tweet

logger = logging.getLogger("RetailXAI.Publishing")


class LinkedInPublisher(BaseAgent):
    """Agent for publishing content to LinkedIn company pages."""

    def __init__(self, config: AgentConfig, shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.access_token = config.config.get('access_token')
        self.company_id = config.config.get('company_id')
        self.api_base = 'https://api.linkedin.com/v2'
        self.draft_mode = config.config.get('draft_mode', True)
        self.draft_directory = config.config.get('draft_directory', 'drafts/linkedin')

    def validate_config(self) -> bool:
        """Validate LinkedIn publisher configuration."""
        if not self.access_token:
            self.logger.error("LinkedIn access token not provided")
            return False
        if not self.company_id:
            self.logger.error("LinkedIn company ID not provided")
            return False
        return True

    async def execute(self) -> AgentResult:
        """Execute LinkedIn publishing."""
        if not self.validate_config():
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error="Invalid configuration"
            )

        try:
            # Get content from config (passed by scheduler)
            articles = self.config.config.get('articles', [])
            
            if not articles:
                return AgentResult(
                    agent_name=self.config.name,
                    success=True,
                    data=[],
                    error="No articles provided for LinkedIn publishing"
                )

            published_posts = []
            
            for article in articles:
                if self._check_shutdown():
                    break
                    
                post_result = await self._publish_article(article)
                published_posts.append(post_result)
                
            self.logger.info(f"Processed {len(published_posts)} LinkedIn posts")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=published_posts
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _publish_article(self, article: Article) -> Dict[str, Any]:
        """Publish an article to LinkedIn."""
        if self.draft_mode:
            return await self._create_draft(article)
        else:
            return await self._publish_to_linkedin(article)

    async def _create_draft(self, article: Article) -> Dict[str, Any]:
        """Create a LinkedIn draft file."""
        os.makedirs(self.draft_directory, exist_ok=True)
        
        # Format article for LinkedIn
        linkedin_post = self._format_for_linkedin(article)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_post_{timestamp}.json"
        filepath = os.path.join(self.draft_directory, filename)
        
        draft_data = {
            'article': {
                'headline': article.headline,
                'summary': article.summary,
                'body': article.body,
                'key_insights': article.key_insights
            },
            'linkedin_post': linkedin_post,
            'created_at': datetime.now().isoformat(),
            'status': 'draft'
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Created LinkedIn draft: {filepath}")
        return {
            'status': 'draft_created',
            'file_path': filepath,
            'post_content': linkedin_post
        }

    async def _publish_to_linkedin(self, article: Article) -> Dict[str, Any]:
        """Publish content directly to LinkedIn."""
        linkedin_post = self._format_for_linkedin(article)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        post_data = {
            'author': f'urn:li:organization:{self.company_id}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': linkedin_post
                    },
                    'shareMediaCategory': 'NONE'
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.api_base}/ugcPosts',
                    headers=headers,
                    json=post_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        self.logger.info("Successfully published to LinkedIn")
                        return {
                            'status': 'published',
                            'post_id': result.get('id'),
                            'post_content': linkedin_post
                        }
                    else:
                        error_text = await response.text()
                        self.logger.error(f"LinkedIn publish failed: {response.status} - {error_text}")
                        return {
                            'status': 'failed',
                            'error': f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            self.logger.error(f"Error publishing to LinkedIn: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _format_for_linkedin(self, article: Article) -> str:
        """Format article content for LinkedIn post."""
        # LinkedIn posts have a 3000 character limit
        post = f"📊 {article.headline}\n\n"
        post += f"{article.summary}\n\n"
        
        # Add key insights
        if article.key_insights:
            post += "🔍 Key Insights:\n"
            for insight in article.key_insights[:3]:  # Limit to top 3
                post += f"• {insight}\n"
            post += "\n"
        
        # Add hashtags
        post += "#RetailAI #CPG #BusinessInsights #DataAnalysis"
        
        # Truncate if too long
        if len(post) > 2900:
            post = post[:2900] + "..."
        
        return post


class SlackAgent(BaseAgent):
    """Agent for sending notifications and reports to Slack."""

    def __init__(self, config: AgentConfig, shutdown_event=None):
        super().__init__(config, shutdown_event)
        self.webhook_url = config.config.get('webhook_url')
        self.bot_token = config.config.get('bot_token')
        self.channel = config.config.get('channel', '#general')
        self.notification_types = config.config.get('notification_types', [
            'daily_summary', 'error_alerts', 'trend_alerts'
        ])

    def validate_config(self) -> bool:
        """Validate Slack agent configuration."""
        if not self.webhook_url and not self.bot_token:
            self.logger.error("Neither Slack webhook URL nor bot token provided")
            return False
        return True

    async def execute(self) -> AgentResult:
        """Execute Slack notifications."""
        if not self.validate_config():
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error="Invalid configuration"
            )

        try:
            # Get notification data from config
            notification_data = self.config.config.get('notification_data', {})
            notification_type = self.config.config.get('notification_type', 'daily_summary')
            
            if notification_type not in self.notification_types:
                return AgentResult(
                    agent_name=self.config.name,
                    success=True,
                    data=[],
                    error=f"Notification type '{notification_type}' not enabled"
                )

            message = await self._create_message(notification_type, notification_data)
            
            if self.webhook_url:
                result = await self._send_webhook_message(message)
            else:
                result = await self._send_bot_message(message)
                
            self.logger.info(f"Sent Slack notification: {notification_type}")
            return AgentResult(
                agent_name=self.config.name,
                success=True,
                data=result
            )
            
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                success=False,
                error=str(e)
            )

    async def _create_message(self, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack message based on notification type."""
        
        if notification_type == 'daily_summary':
            return await self._create_daily_summary(data)
        elif notification_type == 'error_alerts':
            return await self._create_error_alert(data)
        elif notification_type == 'trend_alerts':
            return await self._create_trend_alert(data)
        else:
            return {
                'text': f"Unknown notification type: {notification_type}",
                'channel': self.channel
            }

    async def _create_daily_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create daily summary message."""
        stats = data.get('stats', {})
        top_trends = data.get('top_trends', [])
        articles_generated = data.get('articles_generated', 0)
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 RetailXAI Daily Summary"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Transcripts Collected:*\n{stats.get('transcripts_collected', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Articles Generated:*\n{articles_generated}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Companies Analyzed:*\n{stats.get('companies_analyzed', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Data Sources:*\n{', '.join(stats.get('sources', []))}"
                    }
                ]
            }
        ]
        
        if top_trends:
            trend_text = "\n".join([f"• {trend}" for trend in top_trends[:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔥 Top Trends Today:*\n{trend_text}"
                }
            })
        
        return {
            'channel': self.channel,
            'blocks': blocks
        }

    async def _create_error_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create error alert message."""
        error_info = data.get('error', {})
        component = error_info.get('component', 'Unknown')
        error_message = error_info.get('message', 'Unknown error')
        timestamp = error_info.get('timestamp', datetime.now().isoformat())
        
        return {
            'channel': self.channel,
            'attachments': [
                {
                    'color': 'danger',
                    'title': '🚨 RetailXAI Error Alert',
                    'fields': [
                        {
                            'title': 'Component',
                            'value': component,
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': timestamp,
                            'short': True
                        },
                        {
                            'title': 'Error Message',
                            'value': error_message,
                            'short': False
                        }
                    ]
                }
            ]
        }

    async def _create_trend_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create trend alert message."""
        trend = data.get('trend', {})
        trend_name = trend.get('name', 'Unknown Trend')
        trend_score = trend.get('score', 0)
        companies = trend.get('companies', [])
        
        companies_text = ', '.join(companies[:5]) if companies else 'None'
        
        return {
            'channel': self.channel,
            'attachments': [
                {
                    'color': 'good',
                    'title': '📈 RetailXAI Trend Alert',
                    'fields': [
                        {
                            'title': 'Trend',
                            'value': trend_name,
                            'short': True
                        },
                        {
                            'title': 'Score',
                            'value': str(trend_score),
                            'short': True
                        },
                        {
                            'title': 'Companies Mentioned',
                            'value': companies_text,
                            'short': False
                        }
                    ]
                }
            ]
        }

    async def _send_webhook_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message using Slack webhook."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as response:
                    if response.status == 200:
                        return {'status': 'sent', 'method': 'webhook'}
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Slack webhook failed: {response.status} - {error_text}")
                        return {'status': 'failed', 'error': f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Error sending Slack webhook: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _send_bot_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message using Slack bot token."""
        headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://slack.com/api/chat.postMessage',
                    headers=headers,
                    json=message
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return {'status': 'sent', 'method': 'bot', 'ts': result.get('ts')}
                        else:
                            return {'status': 'failed', 'error': result.get('error')}
                    else:
                        error_text = await response.text()
                        return {'status': 'failed', 'error': f"HTTP {response.status}"}
        except Exception as e:
            self.logger.error(f"Error sending Slack bot message: {e}")
            return {'status': 'failed', 'error': str(e)}