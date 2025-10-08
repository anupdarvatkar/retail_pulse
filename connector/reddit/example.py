"""
Example usage of Reddit authentication

This file demonstrates how to use the Reddit authentication module
with the configuration system.
"""

import logging
from config import create_reddit_authenticator, get_full_config
from reddit.auth import RedditAuthenticator

# Set up logging to see authentication messages
logging.basicConfig(level=logging.INFO)


def test_reddit_authentication():
    """
    Test Reddit authentication using the configuration system
    """
    print("Testing Reddit Authentication...")
    print("=" * 50)
    
    try:
        # Get configuration
        config = get_full_config()
        print(f"Loaded configuration for brands: {config['brands']}")
        
        # Create authenticator
        authenticator = create_reddit_authenticator()
        
        # Test authentication
        if authenticator.test_authentication():
            print("✅ Reddit authentication successful!")
            
            # Get auth headers for API calls
            headers = authenticator.get_auth_headers()
            print("✅ Auth headers obtained successfully")
            print(f"User-Agent: {headers['User-Agent']}")
            
        else:
            print("❌ Reddit authentication failed!")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def example_manual_authentication():
    """
    Example of manual authentication without using config system
    """
    print("\nManual Authentication Example...")
    print("=" * 50)
    
    # Manual credentials (you would get these from environment or config)
    authenticator = RedditAuthenticator(
        client_id="your_client_id",
        client_secret="your_client_secret", 
        username="your_username",
        password="your_password",
        user_agent="your_app:v1.0"
    )
    
    # Get token
    token = authenticator.get_valid_token()
    if token:
        print("✅ Manual authentication successful!")
        print(f"Token: {token[:20]}...")  # Show first 20 chars only
    else:
        print("❌ Manual authentication failed!")


if __name__ == "__main__":
    print("Reddit Authentication Test Suite")
    print("=" * 50)
    
    # Test with config system
    test_reddit_authentication()
    
    # Example of manual usage
    example_manual_authentication()
    
    print("\nDone!")