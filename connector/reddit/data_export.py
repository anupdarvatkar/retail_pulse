"""
Data export utilities for Reddit comments

This module provides functionality to export fetched Reddit comments
to various formats including CSV, JSON, and other data formats.
"""

import csv
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def save_comments_to_csv(comments: List[Dict[str, Any]], filename: str = "fetched_comments.csv") -> str:
    """
    Save fetched comments to a CSV file
    
    Args:
        comments: List of comment dictionaries from Reddit API
        filename: Output CSV filename
        
    Returns:
        Full path to the saved CSV file
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            
            # Write header row
            writer.writerow([
                "Author", 
                "Comment Body", 
                "Subreddit", 
                "Permalink", 
                "Score", 
                "Created UTC",
                "Submission ID",
                "Submission Title",
                "Comment ID",
                "Parent ID"
            ])
            
            # Write comment data
            for comment in comments:
                if "data" in comment and "body" in comment["data"]:
                    comment_data = comment["data"]
                    writer.writerow([
                        comment_data.get("author", "N/A"),
                        comment_data.get("body", "N/A"),
                        comment.get("subreddit", "N/A"),
                        f"https://reddit.com{comment_data.get('permalink', '')}" if comment_data.get('permalink') else "N/A",
                        comment_data.get("score", 0),
                        comment_data.get("created_utc", "N/A"),
                        comment.get("submission_id", "N/A"),
                        comment.get("submission_title", "N/A"),
                        comment_data.get("id", "N/A"),
                        comment_data.get("parent_id", "N/A")
                    ])
        
        full_path = os.path.abspath(filename)
        logger.info(f"Fetched comments saved to {full_path}")
        print(f"Fetched comments saved to {filename}")
        
        return full_path
        
    except Exception as e:
        logger.error(f"Error saving comments to CSV: {e}")
        raise


def save_comments_to_json(comments: List[Dict[str, Any]], filename: str = "fetched_comments.json") -> str:
    """
    Save fetched comments to a JSON file
    
    Args:
        comments: List of comment dictionaries from Reddit API
        filename: Output JSON filename
        
    Returns:
        Full path to the saved JSON file
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        
        # Prepare data with metadata
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_comments": len(comments),
                "format_version": "1.0"
            },
            "comments": comments
        }
        
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(export_data, file, indent=2, ensure_ascii=False)
        
        full_path = os.path.abspath(filename)
        logger.info(f"Fetched comments saved to {full_path}")
        print(f"Fetched comments saved to {filename}")
        
        return full_path
        
    except Exception as e:
        logger.error(f"Error saving comments to JSON: {e}")
        raise


def generate_export_filename(query: str, format_type: str = "csv", include_timestamp: bool = True) -> str:
    """
    Generate a filename for export based on query and format
    
    Args:
        query: Search query used to fetch comments
        format_type: File format (csv, json)
        include_timestamp: Whether to include timestamp in filename
        
    Returns:
        Generated filename
    """
    # Clean query for filename
    clean_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_query = clean_query.replace(' ', '_').lower()
    
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_comments_{clean_query}_{timestamp}.{format_type}"
    else:
        filename = f"reddit_comments_{clean_query}.{format_type}"
    
    return filename


def get_comment_statistics(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate statistics about the fetched comments
    
    Args:
        comments: List of comment dictionaries
        
    Returns:
        Dictionary containing comment statistics
    """
    if not comments:
        return {"total_comments": 0}
    
    authors = set()
    subreddits = set()
    total_score = 0
    comment_lengths = []
    
    for comment in comments:
        if "data" in comment:
            comment_data = comment["data"]
            
            # Collect authors
            author = comment_data.get("author")
            if author and author != "N/A":
                authors.add(author)
            
            # Collect subreddits
            subreddit = comment.get("subreddit")
            if subreddit and subreddit != "N/A":
                subreddits.add(subreddit)
            
            # Collect scores
            score = comment_data.get("score", 0)
            if isinstance(score, (int, float)):
                total_score += score
            
            # Collect comment lengths
            body = comment_data.get("body", "")
            if body:
                comment_lengths.append(len(body))
    
    return {
        "total_comments": len(comments),
        "unique_authors": len(authors),
        "unique_subreddits": len(subreddits),
        "total_score": total_score,
        "average_score": round(total_score / len(comments), 2) if comments else 0,
        "average_comment_length": round(sum(comment_lengths) / len(comment_lengths), 2) if comment_lengths else 0,
        "max_comment_length": max(comment_lengths) if comment_lengths else 0,
        "min_comment_length": min(comment_lengths) if comment_lengths else 0
    }


def save_comments_with_stats(comments: List[Dict[str, Any]], query: str, 
                           subreddit_counts: Dict[str, int], 
                           export_format: str = "csv") -> Dict[str, str]:
    """
    Save comments with statistics to file(s)
    
    Args:
        comments: List of comment dictionaries
        query: Search query used
        subreddit_counts: Dictionary of subreddit counts
        export_format: Export format (csv, json, both)
        
    Returns:
        Dictionary with paths to saved files
    """
    results = {}
    
    if export_format in ["csv", "both"]:
        csv_filename = generate_export_filename(query, "csv")
        csv_path = save_comments_to_csv(comments, csv_filename)
        results["csv_file"] = csv_path
    
    if export_format in ["json", "both"]:
        json_filename = generate_export_filename(query, "json")
        
        # Add statistics to JSON export
        enhanced_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "search_query": query,
                "format_version": "1.0"
            },
            "statistics": get_comment_statistics(comments),
            "subreddit_counts": subreddit_counts,
            "comments": comments
        }
        
        with open(json_filename, "w", encoding="utf-8") as file:
            json.dump(enhanced_data, file, indent=2, ensure_ascii=False)
        
        json_path = os.path.abspath(json_filename)
        results["json_file"] = json_path
        logger.info(f"Enhanced JSON export saved to {json_path}")
    
    return results