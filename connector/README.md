# Fivetran Custom Connector

This is a custom connector for Fivetran built using Python. The connector follows the Fivetran Custom Connector SDK patterns and protocols.

## Project Structure

```
fivetran_connector/
├── myenv/            # Local virtual environment directory
├── connector.py      # Main connector script
├── requirements.txt  # Dependency file for pip
└── README.md        # This file
```

## Setup

1. **Activate the virtual environment:**
   ```bash
   # On Windows
   myenv\Scripts\activate
   
   # On macOS/Linux
   source myenv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Your connector expects the following configuration parameters:

- `api_key`: API key for your data source
- `base_url`: Base URL for your data source API

## Usage

### Schema Discovery
To get the connector schema:
```bash
echo '{"selection":{"action":"schema"}}' | python connector.py
```

### Test Connection
To test the connection:
```bash
echo '{"secrets":{"api_key":"your_api_key","base_url":"https://api.example.com"},"selection":{"action":"test"}}' | python connector.py
```

### Data Sync
To run a data sync:
```bash
echo '{"secrets":{"api_key":"your_api_key","base_url":"https://api.example.com"},"state":{}}' | python connector.py
```

## Development

### Customizing the Connector

1. **Update the schema** in the `schema()` method to match your data source
2. **Implement data fetching logic** in the `_fetch_data()` method
3. **Add connection testing** in the `test_connection()` method
4. **Configure logging** as needed for your use case

### Key Methods to Customize

- `schema()`: Define your data schema
- `_fetch_data()`: Implement API calls to fetch data
- `test_connection()`: Test connectivity to your data source
- `update()`: Main sync logic (usually doesn't need changes)

### Testing

Run tests using pytest:
```bash
pytest
```

## Fivetran Integration

Once your connector is ready:

1. Package your connector code
2. Upload to Fivetran using the Custom Connector interface
3. Configure your connector in the Fivetran dashboard
4. Set up your destination and start syncing

## Error Handling

The connector includes comprehensive error handling and logging. Check the logs for debugging information if issues occur.

## Dependencies

See `requirements.txt` for a full list of dependencies. Key dependencies include:

- `requests`: HTTP client for API calls
- `jsonschema`: JSON schema validation
- `python-dateutil`: Date/time handling
- `structlog`: Structured logging

## License

[Add your license information here]