"""
Startup script for Reddit Comment Fetcher API

This script starts the FastAPI server with proper configuration.
"""

import uvicorn
import logging
import sys
import os

# Add the current directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """
    Main function to start the FastAPI server
    """
    logger.info("Starting Reddit Comment Fetcher API...")
    
    try:
        # Test configuration before starting
        from config import get_full_config, get_server_config
        config = get_full_config()
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"Monitoring brands: {config.get('brands', [])}")
        
        # Get server configuration
        server_config = get_server_config()
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 8000)
        reload = server_config.get('reload', True)
        log_level = server_config.get('log_level', 'info')
        workers = server_config.get('workers', 1)
        
        logger.info(f"🚀 Starting server on {host}:{port}")
        logger.info(f"📊 Server config: reload={reload}, log_level={log_level}, workers={workers}")
        
        # Start the FastAPI server with environment configuration
        uvicorn.run(
            "reddit.api:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            workers=workers if not reload else 1  # Workers > 1 not compatible with reload
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()