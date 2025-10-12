"""
WebSocket service for streaming Reddit hot topics and trends

This module provides real-time streaming of trending Reddit content
including hot posts, trending topics, and popular discussions.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Optional
import requests
from collections import Counter, defaultdict
import re

from reddit.auth import RedditAuthenticator
from config import get_full_config

logger = logging.getLogger(__name__)


class RedditTrendsStreamer:
    """
    Streams Reddit hot topics and trends in real-time
    """
    
    def __init__(self, authenticator: RedditAuthenticator):
        self.authenticator = authenticator
        self.config = get_full_config()
        self.trending_cache = {}
        self.last_update = None
        self.update_interval = 300  # 5 minutes default
    
    def convert_utc_to_readable(self, utc_timestamp: Optional[float]) -> str:
        """
        Convert UTC timestamp to readable format
        
        Args:
            utc_timestamp: Unix timestamp from Reddit API
            
        Returns:
            Human-readable datetime string
        """
        if not utc_timestamp:
            return "Unknown"
        
        try:
            dt = datetime.fromtimestamp(utc_timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError, OSError):
            return "Invalid timestamp"
        
    async def get_hot_posts(self, subreddit: str = "all", limit: int = 25) -> List[Dict[str, Any]]:
        """
        Get hot posts from a specific subreddit or r/all
        
        Args:
            subreddit: Subreddit name or "all" for all of Reddit
            limit: Number of posts to fetch
            
        Returns:
            List of hot post data
        """
        logger.info(f"🔥 get_hot_posts() called: subreddit=r/{subreddit}, limit={limit}")
        try:
            headers = self.authenticator.get_auth_headers()
            oauth_url = self.authenticator.reddit_oauth_url
            
            # Fetch hot posts
            url = f"{oauth_url}/r/{subreddit}/hot"
            params = {"limit": limit}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                logger.info(f"✅ Successfully fetched {len(posts)} raw posts from r/{subreddit}")
                
                hot_posts = []
                for post in posts:
                    post_data = post.get("data", {})
                    hot_posts.append({
                        "id": post_data.get("id"),
                        "title": post_data.get("title"),
                        "subreddit": post_data.get("subreddit"),
                        "author": post_data.get("author"),
                        "score": post_data.get("score", 0),
                        "upvote_ratio": post_data.get("upvote_ratio", 0),
                        "num_comments": post_data.get("num_comments", 0),
                        "created_utc": self.convert_utc_to_readable(post_data.get("created_utc")),
                        "created_utc_raw": post_data.get("created_utc"),  # Keep raw timestamp for sorting/calculations
                        "url": post_data.get("url"),
                        "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                        "selftext": post_data.get("selftext", "")[:200] + "..." if len(post_data.get("selftext", "")) > 200 else post_data.get("selftext", ""),
                        "over_18": post_data.get("over_18", False),
                        "spoiler": post_data.get("spoiler", False),
                        "flair_text": post_data.get("link_flair_text"),
                        "domain": post_data.get("domain")
                    })
                
                logger.info(f"📊 get_hot_posts() completed: {len(hot_posts)} posts processed from r/{subreddit}")
                return hot_posts
            else:
                logger.error(f"❌ Failed to fetch hot posts from r/{subreddit}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"💥 Error in get_hot_posts() for r/{subreddit}: {e}")
            return []
    
    async def get_trending_subreddits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending subreddits
        
        Args:
            limit: Number of trending subreddits to fetch
            
        Returns:
            List of trending subreddit data
        """
        logger.info(f"📈 get_trending_subreddits() called: limit={limit}")
        try:
            headers = self.authenticator.get_auth_headers()
            oauth_url = self.authenticator.reddit_oauth_url
            
            # Fetch trending subreddits
            url = f"{oauth_url}/subreddits/popular"
            params = {"limit": limit}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                subreddits = data.get("data", {}).get("children", [])
                logger.info(f"✅ Successfully fetched {len(subreddits)} trending subreddits")
                
                trending_subs = []
                for sub in subreddits:
                    sub_data = sub.get("data", {})
                    trending_subs.append({
                        "name": sub_data.get("display_name"),
                        "title": sub_data.get("title"),
                        "description": sub_data.get("public_description", "")[:200] + "..." if len(sub_data.get("public_description", "")) > 200 else sub_data.get("public_description", ""),
                        "subscribers": sub_data.get("subscribers", 0),
                        "active_users": sub_data.get("accounts_active", 0),
                        "created_utc": self.convert_utc_to_readable(sub_data.get("created_utc")),
                        "created_utc_raw": sub_data.get("created_utc"),  # Keep raw timestamp for sorting/calculations
                        "over18": sub_data.get("over18", False),
                        "url": f"https://reddit.com/r/{sub_data.get('display_name')}"
                    })
                
                logger.info(f"📊 get_trending_subreddits() completed: {len(trending_subs)} subreddits processed")
                return trending_subs
                
            else:
                logger.error(f"❌ Failed to fetch trending subreddits: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"💥 Error in get_trending_subreddits(): {e}")
            return []
    
    def extract_trending_keywords(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract trending keywords from hot posts
        
        Args:
            posts: List of hot posts
            
        Returns:
            List of trending keywords with counts
        """
        logger.info(f"🔍 extract_trending_keywords() called: analyzing {len(posts)} posts")
        try:
            # Combine all text content
            all_text = []
            for post in posts:
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                all_text.append(f"{title} {selftext}")
            
            # Extract keywords (simple approach)
            word_counts = Counter()
            stop_words = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
                "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
                "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those",
                "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your",
                "his", "her", "its", "our", "their", "from", "up", "about", "into", "over", "after", "just",
                "like", "get", "go", "know", "think", "see", "make", "want", "come", "take", "use", "work",
                "say", "look", "good", "new", "first", "last", "long", "great", "little", "own", "other",
                "old", "right", "big", "high", "different", "small", "large", "next", "early", "young",
                "important", "few", "public", "bad", "same", "able", "reddit", "post", "comment", "thread"
            }
            
            for text in all_text:
                # Simple word extraction
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                for word in words:
                    if word not in stop_words and len(word) > 2:
                        word_counts[word] += 1
            
            # Get top keywords
            trending_keywords = []
            for word, count in word_counts.most_common(20):
                trending_keywords.append({
                    "keyword": word,
                    "count": count,
                    "trend_score": count / len(posts) if posts else 0
                })
            
            logger.info(f"📊 extract_trending_keywords() completed: {len(trending_keywords)} keywords extracted, top: {trending_keywords[0]['keyword'] if trending_keywords else 'None'}")
            return trending_keywords
            
        except Exception as e:
            logger.error(f"💥 Error in extract_trending_keywords(): {e}")
            return []
    
    async def get_subreddit_activity(self, subreddits: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get activity metrics for specific subreddits
        
        Args:
            subreddits: List of subreddit names
            
        Returns:
            Dictionary of subreddit activity data
        """
        logger.info(f"📊 get_subreddit_activity() called: analyzing {len(subreddits)} subreddits - {subreddits}")
        try:
            headers = self.authenticator.get_auth_headers()
            oauth_url = self.authenticator.reddit_oauth_url
            
            activity_data = {}
            
            for subreddit in subreddits:
                try:
                    logger.info(f"  🔍 Fetching activity data for r/{subreddit}")
                    # Get subreddit info
                    url = f"{oauth_url}/r/{subreddit}/about"
                    response = requests.get(url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        sub_data = data.get("data", {})
                        
                        # Get recent posts for activity calculation
                        posts_url = f"{oauth_url}/r/{subreddit}/new"
                        posts_params = {"limit": 10}
                        posts_response = requests.get(posts_url, headers=headers, params=posts_params, timeout=30)
                        
                        recent_posts = []
                        if posts_response.status_code == 200:
                            posts_data = posts_response.json()
                            recent_posts = posts_data.get("data", {}).get("children", [])
                        
                        activity_data[subreddit] = {
                            "name": sub_data.get("display_name"),
                            "subscribers": sub_data.get("subscribers", 0),
                            "active_users": sub_data.get("accounts_active", 0),
                            "activity_ratio": sub_data.get("accounts_active", 0) / max(sub_data.get("subscribers", 1), 1),
                            "recent_posts_count": len(recent_posts),
                            "avg_recent_score": sum(post.get("data", {}).get("score", 0) for post in recent_posts) / max(len(recent_posts), 1),
                            "created_utc": self.convert_utc_to_readable(sub_data.get("created_utc")),
                            "created_utc_raw": sub_data.get("created_utc"),  # Keep raw timestamp for sorting/calculations
                            "description": sub_data.get("public_description", "")[:100] + "..." if len(sub_data.get("public_description", "")) > 100 else sub_data.get("public_description", "")
                        }
                        logger.info(f"    ✅ r/{subreddit}: {sub_data.get('subscribers', 0)} subscribers, {sub_data.get('accounts_active', 0)} active users, {len(recent_posts)} recent posts")
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"    ⚠️  Error getting activity for r/{subreddit}: {e}")
                    continue
            
            logger.info(f"📊 get_subreddit_activity() completed: {len(activity_data)}/{len(subreddits)} subreddits processed successfully")
            return activity_data
            
        except Exception as e:
            logger.error(f"💥 Error in get_subreddit_activity(): {e}")
            return {}
    
    async def get_comprehensive_trends(self, target_subreddits: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive trending data from Reddit
        
        Args:
            target_subreddits: List of subreddit names to focus on, or None to use configured subreddits
        
        Returns:
            Dictionary containing all trending information
        """
        logger.info(f"🚀 get_comprehensive_trends() called: target_subreddits={target_subreddits}")
        try:
            # Use provided subreddits or get from config
            if target_subreddits is None:
                target_subreddits = self.config.get("default_subreddits", ["sneakers", "running", "deals"])
                logger.info(f"📋 Using configured DEFAULT_SUBREDDITS: {target_subreddits}")
            
            logger.info(f"🎯 Fetching comprehensive Reddit trends from: {target_subreddits}")
            
            # Get hot posts from configured subreddits instead of r/all
            all_hot_posts = []
            subreddit_post_counts = {}
            
            for subreddit in target_subreddits[:10]:  # Limit to avoid rate limits
                try:
                    logger.info(f"  📥 Processing r/{subreddit}...")
                    subreddit_posts = await self.get_hot_posts(subreddit, 10)
                    all_hot_posts.extend(subreddit_posts)
                    subreddit_post_counts[subreddit] = len(subreddit_posts)
                    logger.info(f"    ✅ Added {len(subreddit_posts)} posts from r/{subreddit}")
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.warning(f"    ⚠️  Error getting posts from r/{subreddit}: {e}")
                    subreddit_post_counts[subreddit] = 0
                    continue
            
            hot_posts = sorted(all_hot_posts, key=lambda x: x.get('score', 0), reverse=True)[:50]
            logger.info(f"🔥 Collected and sorted {len(hot_posts)} total hot posts (top 50 by score)")
            
            # Extract trending keywords from collected posts
            trending_keywords = self.extract_trending_keywords(hot_posts)
            
            # Get activity for the target subreddits
            logger.info(f"📊 Fetching activity data for {len(target_subreddits[:8])} subreddits...")
            subreddit_activity = await self.get_subreddit_activity(target_subreddits[:8])  # Limit to avoid rate limits
            
            # Compile trending data
            trends_data = {
                "timestamp": datetime.now().isoformat(),
                "target_subreddits": target_subreddits,
                "subreddit_post_counts": subreddit_post_counts,
                "hot_posts": hot_posts[:10],  # Top 10 hot posts across all target subreddits
                "trending_keywords": trending_keywords[:15],  # Top 15 keywords
                "subreddit_activity": subreddit_activity,
                "summary": {
                    "total_hot_posts": len(hot_posts),
                    "target_subreddits_count": len(target_subreddits),
                    "active_subreddits": len([s for s, count in subreddit_post_counts.items() if count > 0]),
                    "total_keywords": len(trending_keywords),
                    "monitored_subreddits": len(subreddit_activity),
                    "avg_hot_post_score": sum(post.get("score", 0) for post in hot_posts) / max(len(hot_posts), 1),
                    "top_trending_keyword": trending_keywords[0]["keyword"] if trending_keywords else "N/A"
                }
            }
            
            # Note: Caching is now handled in get_cached_or_fresh_trends() method
            logger.info(f"✅ get_comprehensive_trends() completed successfully!")
            logger.info(f"📊 Results: {len(hot_posts)} hot posts, {len(trending_keywords)} keywords, {len(subreddit_activity)} active subreddits")
            
            return trends_data
            
        except Exception as e:
            logger.error(f"💥 Error in get_comprehensive_trends(): {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "hot_posts": [],
                "trending_subreddits": [],
                "trending_keywords": [],
                "monitored_activity": {},
                "summary": {"error": "Failed to fetch trends"}
            }
    
    async def should_update_trends(self) -> bool:
        """
        Check if trends should be updated based on cache age
        
        Returns:
            True if update is needed
        """
        logger.info(f"⏰ should_update_trends() called")
        if not self.last_update:
            logger.info(f"  🆕 No previous update found, need fresh data")
            return True
        
        time_since_update = datetime.now() - self.last_update
        time_diff_seconds = time_since_update.total_seconds()
        needs_update = time_diff_seconds > self.update_interval
        
        logger.info(f"  📅 Last update: {self.last_update}")
        logger.info(f"  ⏱️  Time since update: {time_diff_seconds:.1f}s (interval: {self.update_interval}s)")
        logger.info(f"  🔄 Needs update: {needs_update}")
        
        return needs_update
    
    async def get_cached_or_fresh_trends(self, target_subreddits: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get trends from cache or fetch fresh data if needed
        
        Args:
            target_subreddits: List of subreddit names to focus on, or None to use configured subreddits
        
        Returns:
            Trending data dictionary
        """
        logger.info(f"💾 get_cached_or_fresh_trends() called: target_subreddits={target_subreddits}")
        
        # Create a cache key based on the target subreddits to avoid overwriting different trend sets
        cache_key = ",".join(sorted(target_subreddits)) if target_subreddits else "default"
        
        # Check if we have cached data for this specific subreddit combination
        if (cache_key in self.trending_cache and 
            self.last_update and 
            (datetime.now() - self.last_update).total_seconds() < self.update_interval):
            logger.info(f"✅ Using cached trends data for {cache_key} (still fresh)")
            cached_data = self.trending_cache[cache_key]
            logger.info(f"📊 Returning cached data with {len(cached_data.get('hot_posts', []))} hot posts")
            return cached_data
        else:
            logger.info(f"🔄 Cache expired or empty for {cache_key}, fetching fresh trends data")
            trends_data = await self.get_comprehensive_trends(target_subreddits)
            
            # Initialize cache as dict if it's not already
            if not isinstance(self.trending_cache, dict):
                self.trending_cache = {}
            
            # Store trends data with subreddit-specific key
            self.trending_cache[cache_key] = trends_data
            self.last_update = datetime.now()
            
            logger.info(f"💾 Cached trends data for key: {cache_key}")
            return trends_data
    
    async def get_aggregated_trends(self, subreddit_groups: List[List[str]]) -> Dict[str, Any]:
        """
        Get aggregated trends from multiple subreddit groups
        
        Args:
            subreddit_groups: List of subreddit lists to aggregate trends from
        
        Returns:
            Aggregated trending data dictionary
        """
        logger.info(f"🔄 get_aggregated_trends() called: {len(subreddit_groups)} groups")
        
        all_trends = []
        aggregated_hot_posts = []
        aggregated_subreddit_counts = {}
        aggregated_subreddit_activity = {}
        all_keywords_text = []
        
        # Fetch trends from each subreddit group
        for i, subreddit_group in enumerate(subreddit_groups):
            try:
                logger.info(f"  📥 Fetching trends for group {i+1}: {subreddit_group}")
                group_trends = await self.get_cached_or_fresh_trends(subreddit_group)
                all_trends.append(group_trends)
                
                # Aggregate hot posts
                group_hot_posts = group_trends.get('hot_posts', [])
                aggregated_hot_posts.extend(group_hot_posts)
                
                # Aggregate subreddit counts
                group_subreddit_counts = group_trends.get('subreddit_post_counts', {})
                for subreddit, count in group_subreddit_counts.items():
                    aggregated_subreddit_counts[subreddit] = aggregated_subreddit_counts.get(subreddit, 0) + count
                
                # Aggregate subreddit activity
                group_activity = group_trends.get('subreddit_activity', {})
                aggregated_subreddit_activity.update(group_activity)
                
                # Collect text for keyword aggregation
                for post in group_hot_posts:
                    all_keywords_text.append(f"{post.get('title', '')} {post.get('selftext', '')}")
                    
            except Exception as e:
                logger.warning(f"  ⚠️  Error fetching trends for group {i+1}: {e}")
                continue
        
        # Sort aggregated hot posts by score and limit
        aggregated_hot_posts = sorted(aggregated_hot_posts, key=lambda x: x.get('score', 0), reverse=True)[:50]
        
        # Extract trending keywords from all aggregated posts
        trending_keywords = self.extract_trending_keywords(aggregated_hot_posts)
        
        # Create aggregated response
        aggregated_trends = {
            "timestamp": datetime.now().isoformat(),
            "aggregated_from_groups": len(subreddit_groups),
            "all_target_subreddits": list(set([sub for group in subreddit_groups for sub in group])),
            "subreddit_post_counts": aggregated_subreddit_counts,
            "hot_posts": aggregated_hot_posts[:20],  # Top 20 hot posts across all groups
            "trending_keywords": trending_keywords[:20],  # Top 20 keywords
            "subreddit_activity": aggregated_subreddit_activity,
            "summary": {
                "total_hot_posts": len(aggregated_hot_posts),
                "total_subreddits": len(set([sub for group in subreddit_groups for sub in group])),
                "active_subreddits": len([s for s, count in aggregated_subreddit_counts.items() if count > 0]),
                "total_keywords": len(trending_keywords),
                "monitored_subreddits": len(aggregated_subreddit_activity),
                "avg_hot_post_score": sum(post.get("score", 0) for post in aggregated_hot_posts) / max(len(aggregated_hot_posts), 1),
                "top_trending_keyword": trending_keywords[0]["keyword"] if trending_keywords else "N/A",
                "groups_processed": len(all_trends)
            }
        }
        
        logger.info(f"✅ get_aggregated_trends() completed: {len(aggregated_hot_posts)} posts, {len(trending_keywords)} keywords from {len(subreddit_groups)} groups")
        return aggregated_trends