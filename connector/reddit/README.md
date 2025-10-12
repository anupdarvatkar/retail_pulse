# Reddit Comment Fetcher API

A FastAPI-based REST API for fetching comments from Reddit using OAuth authentication.

## Features

- 🔐 **Secure Authentication**: Uses Reddit OAuth with token management
- 🚀 **FastAPI**: High-performance async API framework
- 📊 **Comment Analytics**: Fetches comments with subreddit statistics
- ⚙️ **Configurable**: Environment-based configuration
- 🔍 **Flexible Search**: Customizable search queries and limits
- 📈 **Health Monitoring**: Built-in health checks and status endpoints

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```env
# Reddit API Configuration
CLIENT_ID=your_reddit_client_id
CLIENT_SECRET=your_reddit_client_secret
USERNAME=your_reddit_username
PASSWORD=your_reddit_password
USER_AGENT=your_app_name:v1.0
BRANDS=ceiling fans,home improvement,hvac

# FastAPI Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_LOG_LEVEL=info
API_WORKERS=1
```

## Running the API

### Option 1: Using the startup script
```bash
python start_api.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn reddit.api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### 🏠 Root Endpoint
- **GET** `/` - API information and available endpoints

### 💊 Health Check
- **GET** `/health` - Health status and Reddit authentication check

### ⚙️ Configuration
- **GET** `/config` - Current configuration (safe, no sensitive data)

### 💬 Fetch Comments
- **GET** `/comments` - Fetch comments from Reddit
  - **Parameters:**
    - `search_query` (str): Search term (default: "ceiling fans")
    - `submission_limit` (int): Max submissions to fetch (1-100, default: 10)
    - `include_metadata` (bool): Include detailed metadata (default: true)

### 📊 Comments Summary
- **GET** `/comments/summary` - Get summary statistics only (faster)
  - **Parameters:**
    - `search_query` (str): Search term (default: "ceiling fans")
    - `submission_limit` (int): Max submissions to fetch (1-100, default: 10)

## Usage Examples

### Basic Comment Fetching
```bash
curl "http://localhost:8000/comments?search_query=ceiling fans&submission_limit=5"
```

### Get Summary Only
```bash
curl "http://localhost:8000/comments/summary?search_query=home improvement&submission_limit=20"
```

### Health Check
```bash
curl "http://localhost:8000/health"
```

## Response Format

### Comments Endpoint Response
```json
{
  "query": "ceiling fans",
  "submission_limit": 10,
  "total_comments": 150,
  "subreddit_counts": {
    "HomeImprovement": 45,
    "hvac": 30,
    "DIY": 25
  },
  "summary": {
    "unique_subreddits": 8,
    "top_subreddits": {
      "HomeImprovement": 45,
      "hvac": 30
    },
    "average_comments_per_subreddit": 18.75
  },
  "comments": [
    {
      "data": {
        "body": "Comment text here...",
        "author": "reddit_user",
        "score": 5,
        "created_utc": 1623456789
      },
      "subreddit": "HomeImprovement",
      "submission_id": "abc123",
      "submission_title": "Best ceiling fans for large rooms?"
    }
  ],
  "timestamp": "2025-10-08T12:00:00"
}
```

## Interactive Documentation

Once the API is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│  Authentication │───▶│   Reddit API    │
│                 │    │     Module      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Configuration  │    │     Logging     │
│     System      │    │   & Monitoring  │
└─────────────────┘    └─────────────────┘
```

## Error Handling

The API includes comprehensive error handling:
- **401**: Authentication failures
- **403**: Reddit API access denied
- **429**: Rate limit exceeded
- **500**: Internal server errors
- **503**: Reddit API unavailable

## Logging

The API provides detailed logging for:
- Authentication attempts
- API requests and responses
- Error conditions
- Performance metrics

## Development

### Project Structure
```
reddit/
├── api.py          # FastAPI application
├── auth.py         # Reddit authentication
├── __init__.py     # Package initialization
└── example.py      # Usage examples

config.py           # Configuration management
start_api.py        # Server startup script
requirements.txt    # Dependencies
```

### Adding New Endpoints

1. Create new endpoint in `reddit/api.py`
2. Add authentication if needed using `Depends(get_comment_fetcher)`
3. Update documentation in this README
4. Test the endpoint

## License

This project is part of the Retail Pulse Fivetran connector.