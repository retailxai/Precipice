"""
Real Publishing Services for Substack, LinkedIn, and Twitter
"""
import httpx
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.models.database import PublishDestination

logger = logging.getLogger(__name__)

class BasePublisher:
    """Base class for all publishers"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def publish(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to the platform"""
        raise NotImplementedError
    
    async def test_connection(self) -> bool:
        """Test if credentials are valid"""
        raise NotImplementedError

class SubstackPublisher(BasePublisher):
    """Substack publishing service"""
    
    async def publish(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to Substack"""
        try:
            # Substack API endpoint for creating posts
            url = f"https://api.substack.com/v1/publications/{self.credentials.get('publication_id')}/posts"
            
            headers = {
                "Authorization": f"Bearer {self.credentials.get('api_key')}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "title": draft_data["title"],
                "subtitle": draft_data.get("summary", ""),
                "body": draft_data["body_html"] or draft_data["body_md"],
                "tags": draft_data.get("tags", []),
                "publish": True,  # Set to False for draft
                "send_notification": True
            }
            
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "external_url": result.get("url"),
                    "platform_id": result.get("id"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Substack API error: {response.status_code} - {response.text}",
                    "response": response.text
                }
                
        except Exception as e:
            logger.error(f"Substack publishing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_connection(self) -> bool:
        """Test Substack connection"""
        try:
            url = f"https://api.substack.com/v1/publications/{self.credentials.get('publication_id')}"
            headers = {"Authorization": f"Bearer {self.credentials.get('api_key')}"}
            
            response = await self.client.get(url, headers=headers)
            return response.status_code == 200
        except:
            return False

class LinkedInPublisher(BasePublisher):
    """LinkedIn publishing service"""
    
    async def publish(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to LinkedIn"""
        try:
            # LinkedIn API endpoint for creating posts
            url = "https://api.linkedin.com/v2/ugcPosts"
            
            headers = {
                "Authorization": f"Bearer {self.credentials.get('access_token')}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # LinkedIn UGC post format
            payload = {
                "author": f"urn:li:person:{self.credentials.get('person_id')}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": f"{draft_data['title']}\n\n{draft_data.get('summary', '')}"
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "external_url": f"https://www.linkedin.com/feed/update/{result.get('id')}",
                    "platform_id": result.get("id"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"LinkedIn API error: {response.status_code} - {response.text}",
                    "response": response.text
                }
                
        except Exception as e:
            logger.error(f"LinkedIn publishing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_connection(self) -> bool:
        """Test LinkedIn connection"""
        try:
            url = "https://api.linkedin.com/v2/me"
            headers = {"Authorization": f"Bearer {self.credentials.get('access_token')}"}
            
            response = await self.client.get(url, headers=headers)
            return response.status_code == 200
        except:
            return False

class TwitterPublisher(BasePublisher):
    """Twitter/X publishing service"""
    
    async def publish(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to Twitter"""
        try:
            # Twitter API v2 endpoint for creating tweets
            url = "https://api.twitter.com/2/tweets"
            
            headers = {
                "Authorization": f"Bearer {self.credentials.get('bearer_token')}",
                "Content-Type": "application/json"
            }
            
            # Twitter character limit handling
            text = draft_data["title"]
            if draft_data.get("summary"):
                text += f"\n\n{draft_data['summary']}"
            
            # Truncate if too long
            if len(text) > 280:
                text = text[:277] + "..."
            
            payload = {
                "text": text
            }
            
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                result = response.json()
                tweet_id = result["data"]["id"]
                return {
                    "success": True,
                    "external_url": f"https://twitter.com/user/status/{tweet_id}",
                    "platform_id": tweet_id,
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Twitter API error: {response.status_code} - {response.text}",
                    "response": response.text
                }
                
        except Exception as e:
            logger.error(f"Twitter publishing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_connection(self) -> bool:
        """Test Twitter connection"""
        try:
            url = "https://api.twitter.com/2/users/me"
            headers = {"Authorization": f"Bearer {self.credentials.get('bearer_token')}"}
            
            response = await self.client.get(url, headers=headers)
            return response.status_code == 200
        except:
            return False

class PublishingService:
    """Main publishing service that coordinates all publishers"""
    
    def __init__(self):
        self.publishers = {
            PublishDestination.SUBSTACK: SubstackPublisher,
            PublishDestination.LINKEDIN: LinkedInPublisher,
            PublishDestination.TWITTER: TwitterPublisher
        }
    
    async def publish_draft(self, draft_data: Dict[str, Any], destinations: list, credentials: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Publish draft to multiple destinations"""
        results = {}
        
        for destination in destinations:
            try:
                if destination not in credentials:
                    results[destination] = {
                        "success": False,
                        "error": f"No credentials found for {destination}"
                    }
                    continue
                
                publisher_class = self.publishers.get(destination)
                if not publisher_class:
                    results[destination] = {
                        "success": False,
                        "error": f"Publisher not implemented for {destination}"
                    }
                    continue
                
                publisher = publisher_class(credentials[destination])
                result = await publisher.publish(draft_data)
                results[destination] = result
                
            except Exception as e:
                logger.error(f"Error publishing to {destination}: {e}")
                results[destination] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def test_credentials(self, credentials: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """Test all credential sets"""
        results = {}
        
        for destination, creds in credentials.items():
            try:
                publisher_class = self.publishers.get(destination)
                if not publisher_class:
                    results[destination] = False
                    continue
                
                publisher = publisher_class(creds)
                results[destination] = await publisher.test_connection()
                
            except Exception as e:
                logger.error(f"Error testing {destination} credentials: {e}")
                results[destination] = False
        
        return results
