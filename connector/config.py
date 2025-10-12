"""
Configuration utilities for the Fivetran connector
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_reddit_config() -> Dict[str, Any]:
    """
    Load Reddit API configuration from environment variables
    
    Returns:
        Dictionary containing Reddit API configuration
    """
    return {
        'client_id': os.getenv('CLIENT_ID', ''),
        'client_secret': os.getenv('CLIENT_SECRET', ''),
        'username': os.getenv('REDDIT_USERNAME', ''),
        'password': os.getenv('PASSWORD', ''),
        'user_agent': os.getenv('USER_AGENT', 'desktop:social-listener:v1.0'),
    }


def load_brands_config() -> List[str]:
    """
    Load brands configuration from environment variables
    
    Returns:
        List of brand names to monitor
    """
    brands_str = os.getenv('BRANDS', '')
    return [brand.strip() for brand in brands_str.split(',') if brand.strip()]


def load_subreddits_config() -> List[str]:
    """
    Load default subreddits configuration from environment variables
    
    Returns:
        List of subreddit names to monitor for brand content
    """
    subreddits_str = os.getenv('DEFAULT_SUBREDDITS', 'sneakers,running,deals')
    return [subreddit.strip() for subreddit in subreddits_str.split(',') if subreddit.strip()]


def load_optional_config() -> Dict[str, Any]:
    """
    Load optional configuration settings
    
    Returns:
        Dictionary containing optional configuration
    """
    return {
        'reddit_base_url': os.getenv('REDDIT_BASE_URL', 'https://www.reddit.com'),
        'reddit_oauth_url': os.getenv('REDDIT_OAUTH_URL', 'https://oauth.reddit.com'),
        'reddit_token_url': os.getenv('REDDIT_TOKEN_URL', 'https://www.reddit.com/api/v1/access_token'),
        'rate_limit_requests': int(os.getenv('RATE_LIMIT_REQUESTS', '100')),
        'rate_limit_period': int(os.getenv('RATE_LIMIT_PERIOD', '60')),
        'max_posts_per_brand': int(os.getenv('MAX_POSTS_PER_BRAND', '1000')),
        'sync_interval_hours': int(os.getenv('SYNC_INTERVAL_HOURS', '24')),
    }


def load_server_config() -> Dict[str, Any]:
    """
    Load server configuration settings for FastAPI
    
    Returns:
        Dictionary containing server configuration
    """
    return {
        'host': os.getenv('API_HOST', '0.0.0.0'),
        'port': int(os.getenv('API_PORT', '8000')),
        'reload': os.getenv('API_RELOAD', 'true').lower() == 'true',
        'log_level': os.getenv('API_LOG_LEVEL', 'info'),
        'workers': int(os.getenv('API_WORKERS', '1')),
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that all required configuration is present
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If required configuration is missing
    """
    required_fields = ['client_id', 'client_secret', 'username', 'password']
    
    for field in required_fields:
        if not config.get(field):
            raise ValueError(f"Required configuration field '{field}' is missing or empty")
    
    brands = load_brands_config()
    if not brands:
        raise ValueError("At least one brand must be specified in BRANDS configuration")
    
    return True


def get_full_config() -> Dict[str, Any]:
    """
    Get complete configuration including Reddit API, brands, and optional settings
    
    Returns:
        Complete configuration dictionary
    """
    reddit_config = load_reddit_config()
    brands = load_brands_config()
    optional_config = load_optional_config()
    server_config = load_server_config()
    
    # Validate configuration
    validate_config(reddit_config)
    
    return {
        **reddit_config,
        'brands': brands,
        'default_subreddits': load_subreddits_config(),
        **optional_config,
        'server': server_config
    }


def get_server_config() -> Dict[str, Any]:
    """
    Get server configuration for FastAPI
    
    Returns:
        Server configuration dictionary
    """
    return load_server_config()


def create_reddit_authenticator():
    """
    Create a Reddit authenticator instance using the current configuration
    
    Returns:
        RedditAuthenticator instance configured with environment variables
    """
    from reddit.auth import create_authenticator_from_config
    
    config = get_full_config()
    return create_authenticator_from_config(config)