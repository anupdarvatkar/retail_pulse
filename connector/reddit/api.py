"""
FastAPI application for Reddit trends analysis

This module provides REST API endpoints to fetch trends from Reddit
using the Reddit authentication system.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from collections import Counter
import logging
import requests
import asyncio
from datetime import datetime, timezone

# Import our authentication system
from reddit.auth import RedditAuthenticator
from reddit.trends_streamer import RedditTrendsStreamer
from config import create_reddit_authenticator, get_full_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_unix_timestamp(unix_timestamp):
    """
    Convert Unix timestamp to readable datetime format
    
    Args:
        unix_timestamp: Unix timestamp (seconds since epoch) or None
        
    Returns:
        ISO formatted datetime string or None if input is None/invalid
    """
    if unix_timestamp is None:
        return None
    
    try:
        # Convert Unix timestamp to datetime object
        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
        # Return ISO format string
        return dt.isoformat()
    except (ValueError, TypeError, OSError):
        # Return original value if conversion fails
        return unix_timestamp


# Create FastAPI app
app = FastAPI(
    title="Reddit Trends API",
    description="API to fetch trends and brand information from Reddit with monitoring capabilities",
    version="2.0.0"
)



# Dependency to get the Reddit authenticator
def get_reddit_authenticator() -> RedditAuthenticator:
    """
    Dependency to create and return a RedditAuthenticator instance
    """
    logger.info("🔧 get_reddit_authenticator() called - creating RedditAuthenticator instance")
    try:
        authenticator = create_reddit_authenticator()
        logger.info("✅ RedditAuthenticator instance created successfully")
        return authenticator
    except Exception as e:
        logger.error(f"💥 Failed to create Reddit authenticator: {e}")
        raise HTTPException(status_code=500, detail=f"Reddit authentication setup failed: {str(e)}")

# Dependency to get the trends streamer
def get_trends_streamer() -> RedditTrendsStreamer:
    """
    Dependency to create and return a RedditTrendsStreamer instance
    """
    logger.info("🔧 get_trends_streamer() called - creating RedditTrendsStreamer instance")
    try:
        authenticator = create_reddit_authenticator()
        streamer = RedditTrendsStreamer(authenticator)
        logger.info("✅ RedditTrendsStreamer instance created successfully")
        return streamer
    except Exception as e:
        logger.error(f"💥 Failed to create trends streamer: {e}")
        raise HTTPException(status_code=500, detail=f"Trends streamer setup failed: {str(e)}")


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    logger.info("🏠 root() called - GET / endpoint")
    config = get_full_config()
    brands = config.get('brands', [])
    default_subreddits = config.get('default_subreddits', [])
    
    return {
        "message": "Reddit Comment Fetcher API with Brand-Focused Monitoring",
        "version": "2.0.0",
        "configured_brands": brands,
        "default_subreddits": default_subreddits,
        "endpoints": {
            "/trends": "Get current Reddit trends and hot topics from DEFAULT_SUBREDDITS only",
            "/trends/brands": "Get trends and hot topics specifically for configured brands",
            "/comments/{post_id}": "Get all comments for a specific Reddit post ID",
            "/comments/batch": "Get all comments for multiple Reddit post IDs (POST with list of IDs)",
            "/comments/trending": "Get comments for trending posts automatically from get_reddit_trends",
            "/health": "Health check",
            "/config": "Get current configuration info"
        },
        "examples": {
            "get_brand_trends": f"GET /trends/brands?limit=25",
            "get_post_comments": "GET /comments/abc123 (where abc123 is a Reddit post ID)",
            "get_batch_comments": "POST /comments/batch with body: [\"post_id1\", \"post_id2\", \"post_id3\"]",
            "get_trending_comments": "GET /comments/trending?limit_posts=5&subreddits=sneakers,running"
        }
    }
    logger.info(f"✅ root() completed - returning API info for {len(brands)} brands")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    logger.info("❤️ health_check() called - GET /health endpoint")
    try:
        # Test Reddit authentication
        authenticator = create_reddit_authenticator()
        auth_status = authenticator.test_authentication()
        
        result = {
            "status": "healthy" if auth_status else "degraded",
            "timestamp": datetime.now().isoformat(),
            "reddit_auth": "connected" if auth_status else "failed",
            "message": "Reddit authentication working" if auth_status else "Reddit authentication failed"
        }
        logger.info(f"✅ health_check() completed - status: {result['status']}, auth: {result['reddit_auth']}")
        return result
    except Exception as e:
        logger.error(f"💥 health_check() failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/config")
async def get_config_info():
    """
    Get current configuration information (without sensitive data)
    """
    logger.info("⚙️ get_config_info() called - GET /config endpoint")
    try:
        config = get_full_config()
        server_config = config.get("server", {})
        
        # Return safe config info (no sensitive data)
        safe_config = {
            "brands": config.get("brands", []),
            "default_subreddits": config.get("default_subreddits", []),
            "brand_monitoring": {
                "total_brands": len(config.get("brands", [])),
                "total_subreddits": len(config.get("default_subreddits", [])),
                "max_posts_per_brand": config.get("max_posts_per_brand"),
                "sync_interval_hours": config.get("sync_interval_hours")
            },
            "reddit_api": {
                "base_url": config.get("reddit_base_url"),
                "oauth_url": config.get("reddit_oauth_url"),
                "token_url": config.get("reddit_token_url"),
                "rate_limit_requests": config.get("rate_limit_requests"),
                "rate_limit_period": config.get("rate_limit_period"),
                "user_agent": config.get("user_agent"),
                "has_client_id": bool(config.get("client_id")),
                "has_credentials": bool(config.get("username") and config.get("password"))
            },
            "server": {
                "host": server_config.get("host"),
                "port": server_config.get("port"),
                "reload": server_config.get("reload"),
                "log_level": server_config.get("log_level"),
                "workers": server_config.get("workers")
            }
        }
        
        logger.info(f"✅ get_config_info() completed - returning config for {len(safe_config.get('brands', []))} brands")
        return safe_config
        
    except Exception as e:
        logger.error(f"💥 get_config_info() failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@app.get("/trends")
async def get_reddit_trends(
    subreddits: Optional[str] = Query(default=None, description="Comma-separated subreddit names (default: uses DEFAULT_SUBREDDITS config)"),
    streamer: RedditTrendsStreamer = Depends(get_trends_streamer)
):
    """
    Get current Reddit trends and hot topics from configured DEFAULT_SUBREDDITS
    
    Args:
        subreddits: Comma-separated subreddit names, or None to use DEFAULT_SUBREDDITS from config
    
    Returns:
        JSON response with comprehensive trending data from configured subreddits only
    """
    logger.info(f"📈 get_reddit_trends() called - GET /trends endpoint")
    logger.info(f"📋 Parameters: subreddits={subreddits}")
    try:
        # Get configuration
        config = get_full_config()
        
        # Use provided subreddits or default ones from config
        if subreddits:
            target_subreddits = [s.strip() for s in subreddits.split(',') if s.strip()]
        else:
            target_subreddits = config.get('default_subreddits', ['sneakers', 'running', 'deals'])
        
        logger.info(f"🎯 Target subreddits resolved: {target_subreddits}")
        
        # Always get comprehensive trends from all subreddits - no conditional aggregation
        trends_data = await streamer.get_cached_or_fresh_trends(target_subreddits)
        
        logger.info(f"✅ get_reddit_trends() completed - returning trends for {len(target_subreddits)} subreddits")
        return JSONResponse(content=trends_data)
        
    except Exception as e:
        logger.error(f"💥 get_reddit_trends() failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trends fetch failed: {str(e)}")


@app.get("/trends/brands")
async def get_brand_trends(
    limit: int = Query(default=25, ge=10, le=100, description="Number of posts per subreddit to analyze"),
    subreddits: Optional[str] = Query(default=None, description="Comma-separated subreddit names (default: uses config)"),
    streamer: RedditTrendsStreamer = Depends(get_trends_streamer)
):
    """
    Get trends and hot topics related to configured brands across relevant subreddits
    
    Args:
        limit: Number of posts per subreddit to analyze (10-100)
        subreddits: Comma-separated subreddit names, or None to use default config
        
    Returns:
        JSON response with brand-related trends and hot topics
    """
    logger.info(f"🏷️📈 get_brand_trends() called - GET /trends/brands endpoint")
    logger.info(f"📋 Parameters: limit={limit}, subreddits={subreddits}")
    try:
        # Get configuration
        config = get_full_config()
        brands = config.get('brands', [])
        
        if not brands:
            raise HTTPException(status_code=400, detail="No brands configured in environment")
        
        # Use provided subreddits or default ones
        if subreddits:
            target_subreddits = [s.strip() for s in subreddits.split(',') if s.strip()]
        else:
            target_subreddits = config.get('default_subreddits', ['sneakers', 'running', 'deals'])
        
        logger.info(f"🎯 Target brands: {brands}, subreddits: {target_subreddits}, limit: {limit}")
        
        # Process all subreddits and collect comprehensive brand trends
        brand_trends = {}
        all_brand_mentions = []
        all_brand_posts = []
        
        for subreddit in target_subreddits:
            try:
                # Get hot posts from this subreddit
                hot_posts = await streamer.get_hot_posts(subreddit, limit)
                
                # Filter posts that mention our brands
                brand_related_posts = []
                subreddit_brand_mentions = {brand: 0 for brand in brands}
                
                for post in hot_posts:
                    post_text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
                    
                    # Check if any brand is mentioned
                    mentioned_brands = []
                    for brand in brands:
                        if brand.lower() in post_text:
                            mentioned_brands.append(brand)
                            subreddit_brand_mentions[brand] += 1
                    
                    if mentioned_brands:
                        post['mentioned_brands'] = mentioned_brands
                        brand_related_posts.append(post)
                        all_brand_mentions.extend(mentioned_brands)
                
                # Store results for this subreddit
                if brand_related_posts:
                    brand_trends[subreddit] = {
                        "total_brand_posts": len(brand_related_posts),
                        "brand_mentions": subreddit_brand_mentions,
                        "hot_posts": brand_related_posts  # Include all posts for comprehensive results
                    }
                    all_brand_posts.extend(brand_related_posts)
                    
            except Exception as e:
                logger.warning(f"Error getting brand trends from r/{subreddit}: {e}")
                continue
        
        # Calculate overall brand popularity
        brand_popularity = Counter(all_brand_mentions)
        
        # Get trending keywords from brand-related posts
        trending_keywords = {}
        if all_brand_posts:
            trending_keywords = streamer.extract_trending_keywords(all_brand_posts)
        
        # Prepare response
        response_data = {
            "brands": brands,
            "target_subreddits": target_subreddits,
            "limit_per_subreddit": limit,
            "total_brand_mentions": len(all_brand_mentions),
            "brand_popularity": dict(brand_popularity.most_common()),
            "most_popular_brand": brand_popularity.most_common(1)[0][0] if brand_popularity else None,
            "subreddit_trends": brand_trends,
            "trending_keywords": trending_keywords,
            "summary": {
                "subreddits_with_brand_content": len(brand_trends),
                "total_brand_posts": sum(data["total_brand_posts"] for data in brand_trends.values()),
                "brands_mentioned": len(brand_popularity),
                "total_subreddits_processed": len(target_subreddits)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ get_brand_trends() completed - {len(all_brand_mentions)} brand mentions across {len(brand_trends)} subreddits")
        return JSONResponse(content=response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"💥 get_brand_trends() failed: {e}")
        raise HTTPException(status_code=500, detail=f"Brand trends fetch failed: {str(e)}")


@app.get("/comments/{post_id}")
async def get_post_comments(
    post_id: str,
    authenticator: RedditAuthenticator = Depends(get_reddit_authenticator)
):
    """
    Get all comments for a specific Reddit post ID
    
    Args:
        post_id: The Reddit post ID (without the 't3_' prefix)
        authenticator: Reddit authenticator dependency
    
    Returns:
        JSON response containing all comments for the post
    """
    logger.info(f"💬 get_post_comments() called - GET /comments/{post_id} endpoint")
    
    try:
        # Get authenticated headers
        headers = authenticator.get_auth_headers()
        
        # Fetch comments for the post
        comments_url = f"{authenticator.reddit_oauth_url}/comments/{post_id}"
        logger.info(f"🔗 Fetching comments from: {comments_url}")
        
        comments_response = requests.get(
            comments_url,
            headers=headers,
            timeout=30
        )
        
        if comments_response.status_code != 200:
            logger.error(f"❌ Failed to fetch comments for post {post_id}: {comments_response.status_code}")
            logger.error(f"Response: {comments_response.text}")
            raise HTTPException(
                status_code=comments_response.status_code,
                detail=f"Failed to fetch comments for post {post_id}: {comments_response.text}"
            )

        comments_data = comments_response.json()
        
        # Extract post information (first element of the response)
        post_info = None
        if len(comments_data) > 0 and comments_data[0].get("data", {}).get("children"):
            post_data = comments_data[0]["data"]["children"][0]["data"]
            post_info = {
                "id": post_data.get("id"),
                "title": post_data.get("title"),
                "author": post_data.get("author"),
                "subreddit": post_data.get("subreddit"),
                "score": post_data.get("score", 0),
                "ups": post_data.get("ups", 0),
                "downs": post_data.get("downs", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
                "num_comments": post_data.get("num_comments", 0),
                "created_utc": format_unix_timestamp(post_data.get("created_utc")),
                "url": post_data.get("url"),
                "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                "gilded": post_data.get("gilded", 0),
                "all_awardings": post_data.get("all_awardings", []),
                "total_awards_received": post_data.get("total_awards_received", 0),
                "treatment_tags": post_data.get("treatment_tags", []),
                "locked": post_data.get("locked", False),
                "archived": post_data.get("archived", False),
                "stickied": post_data.get("stickied", False),
                "distinguished": post_data.get("distinguished"),
                "edited": post_data.get("edited", False)
            }
        
        # Extract comments (second element of the response)
        all_comments = []
        if len(comments_data) > 1:
            comments_listing = comments_data[1].get("data", {}).get("children", [])
            
            def extract_comments(comment_items, depth=0):
                """Recursively extract comments and replies"""
                comments = []
                for comment_item in comment_items:
                    comment_data = comment_item.get("data", {})
                    
                    # Skip if it's not a comment (could be "more" object)
                    if comment_item.get("kind") != "t1":
                        continue
                    
                    if comment_data.get("body"):  # Only include comments with content
                        comment_info = {
                            "id": comment_data.get("id"),
                            "body": comment_data.get("body"),
                            "body_html": comment_data.get("body_html"),
                            "author": comment_data.get("author"),
                            "score": comment_data.get("score", 0),
                            "ups": comment_data.get("ups", 0),
                            "downs": comment_data.get("downs", 0),
                            "upvote_ratio": comment_data.get("upvote_ratio"),
                            "created_utc": format_unix_timestamp(comment_data.get("created_utc")),
                            "depth": depth,
                            "permalink": f"https://reddit.com{comment_data.get('permalink', '')}",
                            "parent_id": comment_data.get("parent_id"),
                            "link_id": comment_data.get("link_id"),
                            "is_submitter": comment_data.get("is_submitter", False),
                            "distinguished": comment_data.get("distinguished"),
                            "stickied": comment_data.get("stickied", False),
                            "gilded": comment_data.get("gilded", 0),
                            "all_awardings": comment_data.get("all_awardings", []),
                            "total_awards_received": comment_data.get("total_awards_received", 0),
                            "treatment_tags": comment_data.get("treatment_tags", []),
                            "controversiality": comment_data.get("controversiality", 0),
                            "locked": comment_data.get("locked", False),
                            "archived": comment_data.get("archived", False),
                            "edited": comment_data.get("edited", False),
                            "replies": []
                        }
                        
                        # Process replies if they exist
                        replies_data = comment_data.get("replies")
                        if replies_data and isinstance(replies_data, dict):
                            reply_children = replies_data.get("data", {}).get("children", [])
                            comment_info["replies"] = extract_comments(reply_children, depth + 1)
                        
                        comments.append(comment_info)
                
                return comments
            
            all_comments = extract_comments(comments_listing)

        # Count total comments recursively
        def count_comments(comments):
            count = len(comments)
            for comment in comments:
                count += count_comments(comment.get("replies", []))
            return count

        total_comments = count_comments(all_comments)
        
        response_data = {
            "post_id": post_id,
            "post_info": post_info,
            "comments": all_comments,
            "stats": {
                "total_comments": total_comments,
                "top_level_comments": len(all_comments),
                "has_post_info": post_info is not None
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ get_post_comments() completed - fetched {total_comments} comments for post {post_id}")
        return JSONResponse(content=response_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"💥 get_post_comments() failed for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Comments fetch failed: {str(e)}")


@app.post("/comments/batch")
async def get_batch_comments(
    post_ids: List[str],
    authenticator: RedditAuthenticator = Depends(get_reddit_authenticator)
):
    """
    Get all comments for multiple Reddit post IDs (from trending topics)
    
    Args:
        post_ids: List of Reddit post IDs (without the 't3_' prefix)
        authenticator: Reddit authenticator dependency
    
    Returns:
        JSON response containing all comments for each post
    """
    logger.info(f"💬📦 get_batch_comments() called - POST /comments/batch endpoint")
    logger.info(f"📋 Fetching comments for {len(post_ids)} posts: {post_ids}")
    
    if not post_ids:
        raise HTTPException(status_code=400, detail="post_ids list cannot be empty")
    
    if len(post_ids) > 20:  # Limit to prevent abuse
        raise HTTPException(status_code=400, detail="Maximum 20 post IDs allowed per request")
    
    try:
        # Get authenticated headers
        headers = authenticator.get_auth_headers()
        
        all_posts_data = []
        failed_posts = []
        total_comments_across_all = 0
        
        for i, post_id in enumerate(post_ids):
            try:
                logger.info(f"🔗 [{i+1}/{len(post_ids)}] Fetching comments for post: {post_id}")
                
                # Fetch comments for this post
                comments_url = f"{authenticator.reddit_oauth_url}/comments/{post_id}"
                
                comments_response = requests.get(
                    comments_url,
                    headers=headers,
                    timeout=30
                )
                
                if comments_response.status_code != 200:
                    logger.warning(f"⚠️ Failed to fetch comments for post {post_id}: {comments_response.status_code}")
                    failed_posts.append({
                        "post_id": post_id,
                        "error": f"HTTP {comments_response.status_code}: {comments_response.text[:200]}"
                    })
                    continue

                comments_data = comments_response.json()
                
                # Extract post information (first element of the response)
                post_info = None
                if len(comments_data) > 0 and comments_data[0].get("data", {}).get("children"):
                    post_data = comments_data[0]["data"]["children"][0]["data"]
                    post_info = {
                        "id": post_data.get("id"),
                        "title": post_data.get("title"),
                        "author": post_data.get("author"),
                        "subreddit": post_data.get("subreddit"),
                        "score": post_data.get("score", 0),
                        "ups": post_data.get("ups", 0),
                        "downs": post_data.get("downs", 0),
                        "upvote_ratio": post_data.get("upvote_ratio", 0),
                        "num_comments": post_data.get("num_comments", 0),
                        "created_utc": format_unix_timestamp(post_data.get("created_utc")),
                        "url": post_data.get("url"),
                        "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                        "gilded": post_data.get("gilded", 0),
                        "all_awardings": post_data.get("all_awardings", []),
                        "total_awards_received": post_data.get("total_awards_received", 0),
                        "treatment_tags": post_data.get("treatment_tags", []),
                        "locked": post_data.get("locked", False),
                        "archived": post_data.get("archived", False),
                        "stickied": post_data.get("stickied", False),
                        "distinguished": post_data.get("distinguished"),
                        "edited": post_data.get("edited", False)
                    }
                
                # Extract comments (second element of the response)
                all_comments = []
                if len(comments_data) > 1:
                    comments_listing = comments_data[1].get("data", {}).get("children", [])
                    
                    def extract_comments(comment_items, depth=0):
                        """Recursively extract comments and replies"""
                        comments = []
                        for comment_item in comment_items:
                            comment_data = comment_item.get("data", {})
                            
                            # Skip if it's not a comment (could be "more" object)
                            if comment_item.get("kind") != "t1":
                                continue
                            
                            if comment_data.get("body"):  # Only include comments with content
                                comment_info = {
                                    "id": comment_data.get("id"),
                                    "body": comment_data.get("body"),
                                    "body_html": comment_data.get("body_html"),
                                    "author": comment_data.get("author"),
                                    "score": comment_data.get("score", 0),
                                    "ups": comment_data.get("ups", 0),
                                    "downs": comment_data.get("downs", 0),
                                    "upvote_ratio": comment_data.get("upvote_ratio"),
                                    "created_utc": format_unix_timestamp(comment_data.get("created_utc")),
                                    "depth": depth,
                                    "permalink": f"https://reddit.com{comment_data.get('permalink', '')}",
                                    "parent_id": comment_data.get("parent_id"),
                                    "link_id": comment_data.get("link_id"),
                                    "is_submitter": comment_data.get("is_submitter", False),
                                    "distinguished": comment_data.get("distinguished"),
                                    "stickied": comment_data.get("stickied", False),
                                    "gilded": comment_data.get("gilded", 0),
                                    "all_awardings": comment_data.get("all_awardings", []),
                                    "total_awards_received": comment_data.get("total_awards_received", 0),
                                    "treatment_tags": comment_data.get("treatment_tags", []),
                                    "controversiality": comment_data.get("controversiality", 0),
                                    "locked": comment_data.get("locked", False),
                                    "archived": comment_data.get("archived", False),
                                    "edited": comment_data.get("edited", False),
                                    "replies": []
                                }
                                
                                # Process replies if they exist
                                replies_data = comment_data.get("replies")
                                if replies_data and isinstance(replies_data, dict):
                                    reply_children = replies_data.get("data", {}).get("children", [])
                                    comment_info["replies"] = extract_comments(reply_children, depth + 1)
                                
                                comments.append(comment_info)
                        
                        return comments
                    
                    all_comments = extract_comments(comments_listing)
                
                # Count total comments recursively
                def count_comments(comments):
                    count = len(comments)
                    for comment in comments:
                        count += count_comments(comment.get("replies", []))
                    return count

                total_comments = count_comments(all_comments)
                total_comments_across_all += total_comments
                
                post_data_result = {
                    "post_id": post_id,
                    "post_info": post_info,
                    "comments": all_comments,
                    "stats": {
                        "total_comments": total_comments,
                        "top_level_comments": len(all_comments),
                        "has_post_info": post_info is not None
                    }
                }
                
                all_posts_data.append(post_data_result)
                logger.info(f"✅ [{i+1}/{len(post_ids)}] Fetched {total_comments} comments for post {post_id}")
                
                # Small delay to respect rate limits
                if i < len(post_ids) - 1:  # Don't delay after the last request
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"💥 Error fetching comments for post {post_id}: {e}")
                failed_posts.append({
                    "post_id": post_id,
                    "error": str(e)
                })
                continue
        
        # Prepare batch response
        response_data = {
            "requested_post_ids": post_ids,
            "successful_posts": len(all_posts_data),
            "failed_posts": len(failed_posts),
            "posts_data": all_posts_data,
            "failed_requests": failed_posts,
            "batch_stats": {
                "total_posts_requested": len(post_ids),
                "total_posts_processed": len(all_posts_data),
                "total_comments_fetched": total_comments_across_all,
                "success_rate": (len(all_posts_data) / len(post_ids)) * 100 if post_ids else 0,
                "avg_comments_per_post": total_comments_across_all / max(len(all_posts_data), 1)
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ get_batch_comments() completed - processed {len(all_posts_data)}/{len(post_ids)} posts, {total_comments_across_all} total comments")
        return JSONResponse(content=response_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"💥 get_batch_comments() failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch comments fetch failed: {str(e)}")


@app.get("/comments/brands/batch")
async def get_brand_comments_batch(
    limit: int = Query(default=25, ge=10, le=100, description="Number of posts per subreddit to analyze"),
    subreddits: Optional[str] = Query(default=None, description="Comma-separated subreddit names (default: uses config)"),
    max_posts: int = Query(default=10, ge=1, le=20, description="Maximum number of brand posts to get comments for"),
    streamer: RedditTrendsStreamer = Depends(get_trends_streamer),
    authenticator: RedditAuthenticator = Depends(get_reddit_authenticator)
):
    """
    Get all comments for brand posts from /trends/brands endpoint
    
    This endpoint automatically:
    1. Calls /trends/brands to get brand-related posts
    2. Extracts all post IDs from the brand trends
    3. Calls /comments/batch internally to get comments for all brand posts
    
    Args:
        limit: Number of posts per subreddit to analyze (10-100)
        subreddits: Comma-separated subreddit names (default: uses config)
        max_posts: Maximum number of brand posts to get comments for (1-20)
        streamer: Reddit trends streamer dependency
        authenticator: Reddit authenticator dependency
    
    Returns:
        JSON response with all comments for brand-related posts
    """
    logger.info(f"🏷️💬📦 get_brand_comments_batch() called - GET /comments/brands/batch endpoint")
    logger.info(f"📋 Parameters: limit={limit}, subreddits={subreddits}, max_posts={max_posts}")
    
    try:
        # Step 1: Get brand trends to extract post IDs
        logger.info("🔍 Step 1: Getting brand trends to extract post IDs...")
        config = get_full_config()
        brands = config.get('brands', [])
        
        if not brands:
            raise HTTPException(status_code=400, detail="No brands configured in environment")
        
        # Use provided subreddits or default ones
        if subreddits:
            target_subreddits = [s.strip() for s in subreddits.split(',') if s.strip()]
        else:
            target_subreddits = config.get('default_subreddits', ['sneakers', 'running', 'deals'])
        
        logger.info(f"🎯 Target brands: {brands}, subreddits: {target_subreddits}, limit: {limit}")
        
        # Get brand trends (reuse logic from get_brand_trends)
        brand_trends = {}
        all_brand_mentions = []
        all_brand_posts = []
        brand_post_ids = []
        
        for subreddit in target_subreddits:
            try:
                # Get hot posts from this subreddit
                hot_posts = await streamer.get_hot_posts(subreddit, limit)
                
                # Filter posts that mention our brands
                brand_related_posts = []
                subreddit_brand_mentions = {brand: 0 for brand in brands}
                
                for post in hot_posts:
                    post_text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
                    
                    # Check if any brand is mentioned
                    mentioned_brands = []
                    for brand in brands:
                        if brand.lower() in post_text:
                            mentioned_brands.append(brand)
                            subreddit_brand_mentions[brand] += 1
                    
                    if mentioned_brands:
                        post['mentioned_brands'] = mentioned_brands
                        brand_related_posts.append(post)
                        all_brand_mentions.extend(mentioned_brands)
                        
                        # Extract post ID for comments fetching
                        post_id = post.get('id')
                        if post_id and post_id not in brand_post_ids:
                            brand_post_ids.append(post_id)
                
                # Store results for this subreddit
                if brand_related_posts:
                    brand_trends[subreddit] = {
                        "total_brand_posts": len(brand_related_posts),
                        "brand_mentions": subreddit_brand_mentions,
                        "hot_posts": brand_related_posts
                    }
                    all_brand_posts.extend(brand_related_posts)
                    
            except Exception as e:
                logger.warning(f"Error getting brand trends from r/{subreddit}: {e}")
                continue
        
        if not brand_post_ids:
            raise HTTPException(status_code=404, detail="No brand-related posts found")
        
        # Step 2: Sort brand posts by comment count and select top max_posts
        logger.info(f"📊 Step 2: Found {len(brand_post_ids)} brand post IDs, sorting by comment count...")
        
        # Create list of (post_id, comment_count) tuples from all_brand_posts
        posts_with_comment_counts = []
        for post in all_brand_posts:
            post_id = post.get('id')
            comment_count = post.get('num_comments', 0)
            if post_id:
                posts_with_comment_counts.append((post_id, comment_count, post))
        
        # Sort by comment count (descending) to get posts with most comments first
        posts_with_comment_counts.sort(key=lambda x: x[1], reverse=True)
        
        # Select the top max_posts with highest comment counts
        selected_post_ids = [post_data[0] for post_data in posts_with_comment_counts[:max_posts]]
        selected_comment_counts = [post_data[1] for post_data in posts_with_comment_counts[:max_posts]]
        
        logger.info(f"📊 Selected {len(selected_post_ids)} posts with highest comment counts: {list(zip(selected_post_ids, selected_comment_counts))}")
        logger.info(f"🆔 Top brand posts by engagement: {selected_post_ids}")
        
        # Step 2: Fetch comments for all brand post IDs using batch logic
        logger.info("💬 Step 3: Fetching comments for all brand posts...")
        headers = authenticator.get_auth_headers()
        
        all_posts_data = []
        failed_posts = []
        total_comments_across_all = 0
        
        for i, post_id in enumerate(selected_post_ids):
            try:
                logger.info(f"🔗 [{i+1}/{len(selected_post_ids)}] Fetching comments for brand post: {post_id}")
                
                # Fetch comments for this post
                comments_url = f"{authenticator.reddit_oauth_url}/comments/{post_id}"
                
                comments_response = requests.get(
                    comments_url,
                    headers=headers,
                    timeout=30
                )
                
                if comments_response.status_code != 200:
                    logger.warning(f"⚠️ Failed to fetch comments for post {post_id}: {comments_response.status_code}")
                    failed_posts.append({
                        "post_id": post_id,
                        "error": f"HTTP {comments_response.status_code}: {comments_response.text[:200]}"
                    })
                    continue

                comments_data = comments_response.json()
                
                # Find the original brand post data for context
                original_brand_post = None
                for post in all_brand_posts:
                    if post.get('id') == post_id:
                        original_brand_post = post
                        break
                
                # Extract post information (first element of the response)
                post_info = None
                if len(comments_data) > 0 and comments_data[0].get("data", {}).get("children"):
                    post_data = comments_data[0]["data"]["children"][0]["data"]
                    post_info = {
                        "id": post_data.get("id"),
                        "title": post_data.get("title"),
                        "author": post_data.get("author"),
                        "subreddit": post_data.get("subreddit"),
                        "score": post_data.get("score", 0),
                        "ups": post_data.get("ups", 0),
                        "downs": post_data.get("downs", 0),
                        "upvote_ratio": post_data.get("upvote_ratio", 0),
                        "num_comments": post_data.get("num_comments", 0),
                        "created_utc": format_unix_timestamp(post_data.get("created_utc")),
                        "url": post_data.get("url"),
                        "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                        "gilded": post_data.get("gilded", 0),
                        "all_awardings": post_data.get("all_awardings", []),
                        "total_awards_received": post_data.get("total_awards_received", 0),
                        "treatment_tags": post_data.get("treatment_tags", []),
                        "locked": post_data.get("locked", False),
                        "archived": post_data.get("archived", False),
                        "stickied": post_data.get("stickied", False),
                        "distinguished": post_data.get("distinguished"),
                        "edited": post_data.get("edited", False),
                        # Add brand context from original post
                        "mentioned_brands": original_brand_post.get('mentioned_brands', []) if original_brand_post else [],
                        "brand_rank": i + 1
                    }
                
                # Extract comments (second element of the response) - reuse existing logic
                all_comments = []
                if len(comments_data) > 1:
                    comments_listing = comments_data[1].get("data", {}).get("children", [])
                    
                    def extract_comments(comment_items, depth=0):
                        """Recursively extract comments and replies"""
                        comments = []
                        for comment_item in comment_items:
                            comment_data = comment_item.get("data", {})
                            
                            # Skip if it's not a comment (could be "more" object)
                            if comment_item.get("kind") != "t1":
                                continue
                            
                            if comment_data.get("body"):  # Only include comments with content
                                comment_info = {
                                    "id": comment_data.get("id"),
                                    "body": comment_data.get("body"),
                                    "body_html": comment_data.get("body_html"),
                                    "author": comment_data.get("author"),
                                    "score": comment_data.get("score", 0),
                                    "ups": comment_data.get("ups", 0),
                                    "downs": comment_data.get("downs", 0),
                                    "upvote_ratio": comment_data.get("upvote_ratio"),
                                    "created_utc": format_unix_timestamp(comment_data.get("created_utc")),
                                    "depth": depth,
                                    "permalink": f"https://reddit.com{comment_data.get('permalink', '')}",
                                    "parent_id": comment_data.get("parent_id"),
                                    "link_id": comment_data.get("link_id"),
                                    "is_submitter": comment_data.get("is_submitter", False),
                                    "distinguished": comment_data.get("distinguished"),
                                    "stickied": comment_data.get("stickied", False),
                                    "gilded": comment_data.get("gilded", 0),
                                    "all_awardings": comment_data.get("all_awardings", []),
                                    "total_awards_received": comment_data.get("total_awards_received", 0),
                                    "treatment_tags": comment_data.get("treatment_tags", []),
                                    "controversiality": comment_data.get("controversiality", 0),
                                    "locked": comment_data.get("locked", False),
                                    "archived": comment_data.get("archived", False),
                                    "edited": comment_data.get("edited", False),
                                    "replies": []
                                }
                                
                                # Process replies if they exist
                                replies_data = comment_data.get("replies")
                                if replies_data and isinstance(replies_data, dict):
                                    reply_children = replies_data.get("data", {}).get("children", [])
                                    comment_info["replies"] = extract_comments(reply_children, depth + 1)
                                
                                comments.append(comment_info)
                        
                        return comments
                    
                    all_comments = extract_comments(comments_listing)
                
                # Count total comments recursively
                def count_comments(comments):
                    count = len(comments)
                    for comment in comments:
                        count += count_comments(comment.get("replies", []))
                    return count

                total_comments = count_comments(all_comments)
                total_comments_across_all += total_comments
                
                post_data_result = {
                    "post_id": post_id,
                    "brand_rank": i + 1,
                    "post_info": post_info,
                    "comments": all_comments,
                    "stats": {
                        "total_comments": total_comments,
                        "top_level_comments": len(all_comments),
                        "has_post_info": post_info is not None
                    }
                }
                
                all_posts_data.append(post_data_result)
                logger.info(f"✅ [{i+1}/{len(selected_post_ids)}] Fetched {total_comments} comments for brand post {post_id}")
                
                # Small delay to respect rate limits
                if i < len(selected_post_ids) - 1:  # Don't delay after the last request
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"💥 Error fetching comments for brand post {post_id}: {e}")
                failed_posts.append({
                    "post_id": post_id,
                    "error": str(e)
                })
                continue
        
        # Calculate brand popularity for summary
        brand_popularity = Counter(all_brand_mentions)
        
        # Prepare comprehensive response
        response_data = {
            "brand_trends_summary": {
                "brands": brands,
                "target_subreddits": target_subreddits,
                "brand_popularity": dict(brand_popularity.most_common()),
                "most_popular_brand": brand_popularity.most_common(1)[0][0] if brand_popularity else None,
                "total_brand_posts_found": len(brand_post_ids),
                "selected_for_comments": len(selected_post_ids),
                "selection_criteria": "Top posts by comment count (highest engagement)",
                "selected_posts_comment_counts": dict(zip(selected_post_ids, selected_comment_counts)) if 'selected_comment_counts' in locals() else {}
            },
            "comments_data": {
                "requested_post_ids": selected_post_ids,
                "successful_posts": len(all_posts_data),
                "failed_posts": len(failed_posts),
                "posts_data": all_posts_data,
                "failed_requests": failed_posts
            },
            "batch_stats": {
                "total_brand_mentions": len(all_brand_mentions),
                "total_posts_requested": len(selected_post_ids),
                "total_posts_processed": len(all_posts_data),
                "total_comments_fetched": total_comments_across_all,
                "success_rate": (len(all_posts_data) / len(selected_post_ids)) * 100 if selected_post_ids else 0,
                "avg_comments_per_post": total_comments_across_all / max(len(all_posts_data), 1),
                "subreddits_with_brand_content": len(brand_trends)
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ get_brand_comments_batch() completed - processed {len(all_posts_data)}/{len(selected_post_ids)} top brand posts (by comment count), {total_comments_across_all} total comments")
        return JSONResponse(content=response_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"💥 get_brand_comments_batch() failed: {e}")
        raise HTTPException(status_code=500, detail=f"Brand comments batch fetch failed: {str(e)}")


@app.get("/comments/trending")
async def get_trending_comments(
    subreddits: Optional[str] = Query(default=None, description="Comma-separated subreddit names (default: uses DEFAULT_SUBREDDITS config)"),
    limit_posts: int = Query(default=5, ge=1, le=10, description="Number of trending posts to get comments for (1-10)"),
    streamer: RedditTrendsStreamer = Depends(get_trends_streamer),
    authenticator: RedditAuthenticator = Depends(get_reddit_authenticator)
):
    """
    Get comments for trending posts from get_reddit_trends
    
    This endpoint first fetches trending topics using get_reddit_trends, 
    then automatically fetches comments for the top trending posts.
    
    Args:
        subreddits: Comma-separated subreddit names (default: uses DEFAULT_SUBREDDITS config)
        limit_posts: Number of top trending posts to get comments for (1-10)
        streamer: Reddit trends streamer dependency
        authenticator: Reddit authenticator dependency
    
    Returns:
        JSON response with trending posts and all their comments
    """
    logger.info(f"📈💬 get_trending_comments() called - GET /comments/trending endpoint")
    logger.info(f"📋 Parameters: subreddits={subreddits}, limit_posts={limit_posts}")
    
    try:
        # Step 1: Get trending topics
        logger.info("🔍 Step 1: Fetching trending topics...")
        config = get_full_config()
        
        # Use provided subreddits or default ones from config
        if subreddits:
            target_subreddits = [s.strip() for s in subreddits.split(',') if s.strip()]
        else:
            target_subreddits = config.get('default_subreddits', ['sneakers', 'running', 'deals'])
        
        # Get comprehensive trends
        trends_data = await streamer.get_cached_or_fresh_trends(target_subreddits)
        
        # Step 2: Extract post IDs from trending posts
        hot_posts = trends_data.get("hot_posts", [])
        if not hot_posts:
            raise HTTPException(status_code=404, detail="No trending posts found")
        
        # Get the top N post IDs
        top_post_ids = [post.get("id") for post in hot_posts[:limit_posts] if post.get("id")]
        
        if not top_post_ids:
            raise HTTPException(status_code=404, detail="No valid post IDs found in trending posts")
        
        logger.info(f"📊 Step 2: Found {len(top_post_ids)} trending post IDs: {top_post_ids}")
        
        # Step 3: Fetch comments for these posts
        logger.info("💬 Step 3: Fetching comments for trending posts...")
        headers = authenticator.get_auth_headers()
        
        posts_with_comments = []
        total_comments_count = 0
        
        for i, post_id in enumerate(top_post_ids):
            try:
                logger.info(f"🔗 [{i+1}/{len(top_post_ids)}] Fetching comments for trending post: {post_id}")
                
                comments_url = f"{authenticator.reddit_oauth_url}/comments/{post_id}"
                comments_response = requests.get(comments_url, headers=headers, timeout=30)
                
                if comments_response.status_code != 200:
                    logger.warning(f"⚠️ Failed to fetch comments for post {post_id}: {comments_response.status_code}")
                    continue

                comments_data = comments_response.json()
                
                # Find the original post data from trends
                original_post = next((post for post in hot_posts if post.get("id") == post_id), None)
                
                # Extract post information and comments (reuse logic from single post endpoint)
                post_info = None
                if len(comments_data) > 0 and comments_data[0].get("data", {}).get("children"):
                    post_data = comments_data[0]["data"]["children"][0]["data"]
                    post_info = {
                        "id": post_data.get("id"),
                        "title": post_data.get("title"),
                        "author": post_data.get("author"),
                        "subreddit": post_data.get("subreddit"),
                        "score": post_data.get("score", 0),
                        "ups": post_data.get("ups", 0),
                        "downs": post_data.get("downs", 0),
                        "upvote_ratio": post_data.get("upvote_ratio", 0),
                        "num_comments": post_data.get("num_comments", 0),
                        "created_utc": format_unix_timestamp(post_data.get("created_utc")),
                        "url": post_data.get("url"),
                        "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                        "gilded": post_data.get("gilded", 0),
                        "all_awardings": post_data.get("all_awardings", []),
                        "total_awards_received": post_data.get("total_awards_received", 0),
                        "treatment_tags": post_data.get("treatment_tags", []),
                        "locked": post_data.get("locked", False),
                        "archived": post_data.get("archived", False),
                        "stickied": post_data.get("stickied", False),
                        "distinguished": post_data.get("distinguished"),
                        "edited": post_data.get("edited", False),
                        "trending_rank": i + 1,  # Add trending rank
                        "trending_score": original_post.get("score", 0) if original_post else 0
                    }
                
                # Extract comments
                all_comments = []
                if len(comments_data) > 1:
                    comments_listing = comments_data[1].get("data", {}).get("children", [])
                    
                    def extract_comments(comment_items, depth=0):
                        comments = []
                        for comment_item in comment_items:
                            comment_data = comment_item.get("data", {})
                            if comment_item.get("kind") != "t1":
                                continue
                            if comment_data.get("body"):
                                comment_info = {
                                    "id": comment_data.get("id"),
                                    "body": comment_data.get("body"),
                                    "body_html": comment_data.get("body_html"),
                                    "author": comment_data.get("author"),
                                    "score": comment_data.get("score", 0),
                                    "ups": comment_data.get("ups", 0),
                                    "downs": comment_data.get("downs", 0),
                                    "upvote_ratio": comment_data.get("upvote_ratio"),
                                    "created_utc": format_unix_timestamp(comment_data.get("created_utc")),
                                    "depth": depth,
                                    "permalink": f"https://reddit.com{comment_data.get('permalink', '')}",
                                    "parent_id": comment_data.get("parent_id"),
                                    "link_id": comment_data.get("link_id"),
                                    "is_submitter": comment_data.get("is_submitter", False),
                                    "distinguished": comment_data.get("distinguished"),
                                    "stickied": comment_data.get("stickied", False),
                                    "gilded": comment_data.get("gilded", 0),
                                    "all_awardings": comment_data.get("all_awardings", []),
                                    "total_awards_received": comment_data.get("total_awards_received", 0),
                                    "treatment_tags": comment_data.get("treatment_tags", []),
                                    "controversiality": comment_data.get("controversiality", 0),
                                    "locked": comment_data.get("locked", False),
                                    "archived": comment_data.get("archived", False),
                                    "edited": comment_data.get("edited", False),
                                    "replies": []
                                }
                                replies_data = comment_data.get("replies")
                                if replies_data and isinstance(replies_data, dict):
                                    reply_children = replies_data.get("data", {}).get("children", [])
                                    comment_info["replies"] = extract_comments(reply_children, depth + 1)
                                comments.append(comment_info)
                        return comments
                    
                    all_comments = extract_comments(comments_listing)
                
                def count_comments(comments):
                    count = len(comments)
                    for comment in comments:
                        count += count_comments(comment.get("replies", []))
                    return count

                total_comments = count_comments(all_comments)
                total_comments_count += total_comments
                
                posts_with_comments.append({
                    "post_id": post_id,
                    "trending_rank": i + 1,
                    "post_info": post_info,
                    "comments": all_comments,
                    "stats": {
                        "total_comments": total_comments,
                        "top_level_comments": len(all_comments),
                        "has_post_info": post_info is not None
                    }
                })
                
                logger.info(f"✅ [{i+1}/{len(top_post_ids)}] Fetched {total_comments} comments for trending post {post_id}")
                
                # Small delay to respect rate limits
                if i < len(top_post_ids) - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"💥 Error fetching comments for trending post {post_id}: {e}")
                continue
        
        # Prepare final response
        response_data = {
            "trending_data": {
                "target_subreddits": target_subreddits,
                "trending_keywords": trends_data.get("trending_keywords", [])[:10],
                "total_trending_posts": len(hot_posts),
                "selected_posts_for_comments": limit_posts
            },
            "posts_with_comments": posts_with_comments,
            "summary": {
                "total_posts_with_comments": len(posts_with_comments),
                "total_comments_fetched": total_comments_count,
                "avg_comments_per_post": total_comments_count / max(len(posts_with_comments), 1),
                "successful_rate": (len(posts_with_comments) / len(top_post_ids)) * 100 if top_post_ids else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ get_trending_comments() completed - {len(posts_with_comments)} trending posts with {total_comments_count} total comments")
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 get_trending_comments() failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trending comments fetch failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI app
    uvicorn.run(
        "reddit.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )