#!/usr/bin/env python3
"""
Test Reddit authentication
"""

from config import load_reddit_config
import requests

def test_reddit_auth():
    """Test Reddit authentication with current credentials"""
    
    config = load_reddit_config()
    print("Config loaded:")
    print(f"  Client ID: {config['client_id'][:10]}...")
    print(f"  Username: {config['username']}")
    print(f"  User Agent: {config['user_agent']}")
    
    # Test authentication
    client_auth = requests.auth.HTTPBasicAuth(config['client_id'], config['client_secret'])
    post_data = {
        'grant_type': 'password',
        'username': config['username'],
        'password': config['password']
    }
    headers = {'User-Agent': config['user_agent']}
    
    print("\nTesting authentication...")
    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=client_auth,
            data=post_data,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Success! Keys: {list(data.keys())}")
                if 'access_token' in data:
                    print(f"Token: {data['access_token'][:20]}...")
                    return True
            except Exception as e:
                print(f"Could not parse JSON: {e}")
        else:
            print("❌ Authentication failed!")
            
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_reddit_auth()