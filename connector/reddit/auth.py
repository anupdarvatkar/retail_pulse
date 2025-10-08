"""
Reddit API Authentication Module

This module handles Reddit OAuth authentication for the Fivetran connector.
It provides functionality to obtain and manage access tokens for Reddit API calls.
"""

import requests
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)


class RedditAuthenticator:
    """
    Handles Reddit OAuth authentication and token management
    """
    
    def __init__(self, client_id: str, client_secret: str, username: str, password: str, user_agent: str, 
                 reddit_oauth_url: str = "https://oauth.reddit.com", 
                 reddit_token_url: str = "https://www.reddit.com/api/v1/access_token"):
        """
        Initialize the Reddit authenticator
        
        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            username: Reddit username
            password: Reddit password
            user_agent: User agent string for API requests
            reddit_oauth_url: Reddit OAuth API base URL
            reddit_token_url: Reddit token endpoint URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self.reddit_oauth_url = reddit_oauth_url
        self.reddit_token_url = reddit_token_url
        self.access_token = None
        self.token_expires_at = None
        self.token_type = None
        
    def get_oauth_token(self) -> Optional[str]:
        """
        Authenticate with Reddit API and get OAuth access token
        
        Returns:
            Access token string if authentication succeeds, None otherwise
        """
        client_auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        post_data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password
        }
        headers = {"User-Agent": self.user_agent}
        
        try:
            logger.info("Attempting Reddit OAuth authentication...")
            response = requests.post(
                self.reddit_token_url,
                auth=client_auth,
                data=post_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.token_type = token_data.get("token_type", "bearer")
                
                # Calculate token expiration (Reddit tokens typically expire in 1 hour)
                expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Reddit authentication succeeded!")
                logger.info(f"Token expires at: {self.token_expires_at}")
                
                return self.access_token
            else:
                logger.error(f"Reddit authentication failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during Reddit authentication: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Reddit authentication: {e}")
            return None
    
    def is_token_valid(self) -> bool:
        """
        Check if the current access token is valid and not expired
        
        Returns:
            True if token is valid, False otherwise
        """
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Add 5-minute buffer before expiration
        buffer_time = timedelta(minutes=5)
        return datetime.now() < (self.token_expires_at - buffer_time)
    
    def get_valid_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary
        
        Returns:
            Valid access token or None if authentication fails
        """
        if self.is_token_valid():
            logger.debug("Using existing valid token")
            return self.access_token
        
        logger.info("Token expired or invalid, getting new token...")
        return self.get_oauth_token()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get headers with authentication for Reddit API requests
        
        Returns:
            Dictionary containing authorization and user-agent headers
        """
        token = self.get_valid_token()
        if not token:
            raise ValueError("Failed to obtain valid Reddit access token")
        
        return {
            "Authorization": f"{self.token_type} {token}",
            "User-Agent": self.user_agent
        }
    
    def test_authentication(self) -> bool:
        """
        Test the authentication by making a simple API call
        
        Returns:
            True if authentication is working, False otherwise
        """
        try:
            headers = self.get_auth_headers()
            response = requests.get(
                f"{self.reddit_oauth_url}/api/v1/me",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Authentication test successful! Logged in as: {user_data.get('name', 'Unknown')}")
                return True
            else:
                logger.error(f"Authentication test failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing authentication: {e}")
            return False


def create_authenticator_from_config(config: Dict[str, Any]) -> RedditAuthenticator:
    """
    Create a RedditAuthenticator instance from configuration dictionary
    
    Args:
        config: Configuration dictionary containing Reddit credentials
        
    Returns:
        Configured RedditAuthenticator instance
    """
    return RedditAuthenticator(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        username=config['username'],
        password=config['password'],
        user_agent=config['user_agent'],
        reddit_oauth_url=config.get('reddit_oauth_url', 'https://oauth.reddit.com'),
        reddit_token_url=config.get('reddit_token_url', 'https://www.reddit.com/api/v1/access_token')
    )


# Legacy function for backward compatibility
def get_oauth_token(client_id: str, client_secret: str, username: str, password: str, user_agent: str) -> Optional[str]:
    """
    Legacy function to get OAuth token (for backward compatibility)
    
    Args:
        client_id: Reddit app client ID
        client_secret: Reddit app client secret
        username: Reddit username
        password: Reddit password
        user_agent: User agent string
        
    Returns:
        Access token string if authentication succeeds, None otherwise
    """
    authenticator = RedditAuthenticator(client_id, client_secret, username, password, user_agent)
    return authenticator.get_oauth_token()