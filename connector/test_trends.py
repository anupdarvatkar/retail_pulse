#!/usr/bin/env python3
"""
Test the updated trends API that now uses only DEFAULT_SUBREDDITS
"""

import requests
import json
from config import get_full_config

def test_trends_api():
    """Test that /trends API now uses only DEFAULT_SUBREDDITS"""
    
    # Get current config to see what subreddits should be used
    config = get_full_config()
    default_subreddits = config.get('default_subreddits', [])
    
    print(f"Testing /trends API with DEFAULT_SUBREDDITS: {default_subreddits}")
    print("=" * 60)
    
    try:
        # Test the regular /trends endpoint
        response = requests.get("http://127.0.0.1:9090/trends", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ /trends API Response Structure:")
            print(f"  📊 Target Subreddits: {data.get('target_subreddits', [])}")
            print(f"  📈 Hot Posts Count: {len(data.get('hot_posts', []))}")
            print(f"  🔍 Keywords Count: {len(data.get('trending_keywords', []))}")
            print(f"  📍 Active Subreddits: {data.get('summary', {}).get('active_subreddits', 0)}")
            
            # Verify it's using our configured subreddits
            target_subreddits = data.get('target_subreddits', [])
            if set(target_subreddits) == set(default_subreddits):
                print("✅ SUCCESS: API is using configured DEFAULT_SUBREDDITS!")
            else:
                print(f"⚠️  WARNING: Expected {default_subreddits}, got {target_subreddits}")
            
            # Show some sample data
            hot_posts = data.get('hot_posts', [])
            if hot_posts:
                print(f"\n📝 Sample Hot Posts from {target_subreddits}:")
                for i, post in enumerate(hot_posts[:3], 1):
                    subreddit = post.get('subreddit', 'unknown')
                    title = post.get('title', 'No title')[:60]
                    score = post.get('score', 0)
                    print(f"  {i}. r/{subreddit} - {title}... (Score: {score})")
            
            # Show trending keywords
            keywords = data.get('trending_keywords', [])
            if keywords:
                print(f"\n🔥 Top Trending Keywords:")
                for i, kw in enumerate(keywords[:5], 1):
                    keyword = kw.get('keyword', 'unknown')
                    count = kw.get('count', 0)
                    print(f"  {i}. {keyword} (mentioned {count} times)")
        
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the FastAPI server is running on port 9090")
        print("Start server with: python -m uvicorn reddit.api:app --host 127.0.0.1 --port 9090")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_trends_api()