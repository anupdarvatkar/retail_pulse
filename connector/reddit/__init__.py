"""
Reddit API integration package for Fivetran connector

This package provides Reddit API authentication and data collection functionality.
"""

from .auth import RedditAuthenticator, create_authenticator_from_config, get_oauth_token
from .data_export import (
    save_comments_to_csv, 
    save_comments_to_json, 
    save_comments_with_stats,
    generate_export_filename,
    get_comment_statistics
)
from .trends_streamer import RedditTrendsStreamer

__all__ = [
    'RedditAuthenticator',
    'create_authenticator_from_config', 
    'get_oauth_token',
    'save_comments_to_csv',
    'save_comments_to_json',
    'save_comments_with_stats',
    'generate_export_filename',
    'get_comment_statistics',
    'RedditTrendsStreamer'
]