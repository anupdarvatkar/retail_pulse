#!/usr/bin/env python3
"""
Fivetran Custom Connector

This is the main connector script for your custom Fivetran connector.
It follows the Fivetran Custom Connector SDK patterns and structure.
"""

import json
import sys
import logging
import os
from typing import Dict, Any, Iterator, List
from datetime import datetime, timezone
from decouple import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FivetranConnector:
    """
    Main connector class implementing Fivetran Custom Connector protocol
    """
    
    def __init__(self, configuration: Dict[str, Any]):
        """
        Initialize the connector with configuration
        
        Args:
            configuration: Dictionary containing connector configuration
        """
        self.configuration = configuration
        
        # Load environment variables with fallback to configuration
        self.client_id = configuration.get('client_id') or config('CLIENT_ID', default='')
        self.client_secret = configuration.get('client_secret') or config('CLIENT_SECRET', default='')
        self.username = configuration.get('username') or config('USERNAME', default='')
        self.password = configuration.get('password') or config('PASSWORD', default='')
        self.user_agent = configuration.get('user_agent') or config('USER_AGENT', default='desktop:social-listener:v1.0')
        
        # Parse brands from environment or configuration
        brands_str = configuration.get('brands') or config('BRANDS', default='')
        self.brands = [brand.strip() for brand in brands_str.split(',') if brand.strip()]
        
        # Validate required configuration
        if not self.client_id:
            raise ValueError("Reddit CLIENT_ID is required in configuration or environment")
        if not self.client_secret:
            raise ValueError("Reddit CLIENT_SECRET is required in configuration or environment")
        if not self.username:
            raise ValueError("Reddit USERNAME is required in configuration or environment")
        if not self.password:
            raise ValueError("Reddit PASSWORD is required in configuration or environment")
        if not self.brands:
            raise ValueError("BRANDS list is required in configuration or environment")
    
    def schema(self) -> Dict[str, Any]:
        """
        Define the schema for your connector
        
        Returns:
            Dictionary containing the schema definition
        """
        return {
            "schemas": {
                "your_schema_name": {
                    "tables": {
                        "your_table_name": {
                            "columns": {
                                "id": {"type": "STRING", "primary_key": True},
                                "name": {"type": "STRING"},
                                "created_at": {"type": "UTC_DATETIME"},
                                "updated_at": {"type": "UTC_DATETIME"}
                            }
                        }
                    }
                }
            }
        }
    
    def update(self, state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Main update method that fetches data from your source
        
        Args:
            state: Dictionary containing the current state of the connector
            
        Yields:
            Dictionary containing records and state updates
        """
        logger.info("Starting data sync...")
        
        try:
            # Your data fetching logic goes here
            # This is a sample implementation
            
            # Get the last sync timestamp from state
            last_sync = state.get('last_sync_timestamp')
            current_sync = datetime.now(timezone.utc).isoformat()
            
            # Sample data - replace with your actual data fetching logic
            records = self._fetch_data(last_sync)
            
            # Yield records
            for record in records:
                yield {
                    "type": "RECORD",
                    "record": {
                        "your_schema_name": {
                            "your_table_name": record
                        }
                    }
                }
            
            # Update state with new sync timestamp
            yield {
                "type": "STATE",
                "state": {
                    "last_sync_timestamp": current_sync
                }
            }
            
            logger.info(f"Sync completed successfully. Processed {len(records)} records.")
            
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
            raise
    
    def _fetch_data(self, last_sync: str = None) -> List[Dict[str, Any]]:
        """
        Fetch data from your source API
        
        Args:
            last_sync: Timestamp of the last successful sync
            
        Returns:
            List of records from your data source
        """
        # TODO: Implement your actual data fetching logic here
        # This is a placeholder implementation
        
        logger.info(f"Fetching data since: {last_sync}")
        
        # Sample data - replace with actual API calls
        sample_data = [
            {
                "id": "1",
                "name": "Sample Record 1",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "2",
                "name": "Sample Record 2",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        return sample_data
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to your data source
        
        Returns:
            Dictionary indicating connection test result
        """
        try:
            # TODO: Implement actual connection test logic
            # This could be a simple API call to verify credentials
            
            logger.info("Testing connection...")
            
            # Placeholder test - replace with actual test logic
            test_successful = True
            
            if test_successful:
                return {"status": "SUCCESS", "message": "Connection test passed"}
            else:
                return {"status": "FAILURE", "message": "Connection test failed"}
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {"status": "FAILURE", "message": f"Connection test failed: {str(e)}"}


def main():
    """
    Main entry point for the connector
    """
    try:
        # Read input from stdin
        input_data = sys.stdin.read()
        
        if not input_data.strip():
            logger.error("No input data provided")
            sys.exit(1)
        
        # Parse the input JSON
        try:
            request = json.loads(input_data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input: {str(e)}")
            sys.exit(1)
        
        # Extract configuration and state
        configuration = request.get('secrets', {})
        state = request.get('state', {})
        
        # Initialize the connector
        connector = FivetranConnector(configuration)
        
        # Determine the operation type
        operation = request.get('selection', {}).get('action')
        
        if operation == 'schema':
            # Return schema
            schema = connector.schema()
            print(json.dumps(schema))
            
        elif operation == 'test':
            # Test connection
            test_result = connector.test_connection()
            print(json.dumps(test_result))
            
        else:
            # Default to update operation
            for output in connector.update(state):
                print(json.dumps(output))
                sys.stdout.flush()
    
    except Exception as e:
        logger.error(f"Connector failed: {str(e)}")
        error_response = {
            "type": "LOG",
            "log": {
                "level": "SEVERE",
                "message": f"Connector failed: {str(e)}"
            }
        }
        print(json.dumps(error_response))
        sys.exit(1)


if __name__ == "__main__":
    main()