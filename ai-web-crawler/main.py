import asyncio

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL, CSS_SELECTOR, REQUIRED_KEYS
from utils.data_utils import (
    save_reviews_to_csv,
)
from utils.scraper_utils import (
    fetch_and_process_page,
    get_browser_config,
    get_llm_strategy,
)

load_dotenv()


async def crawl_amazon_reviews():
    """
    Main function to crawl amazon reviews.
    """
    # Initialize configurations
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "amazon_crawl_session"

    # Initialize state variables
    page_number = 1
    all_reviews = []
    seen_names = set()

    # Start the web crawler context
    # https://docs.crawl4ai.com/api/async-webcrawler/#asyncwebcrawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        while True:
            # Fetch and process data from the current page
            reviews, no_results_found = await fetch_and_process_page(
                crawler,
                page_number,
                BASE_URL,
                CSS_SELECTOR,
                llm_strategy,
                session_id,
                REQUIRED_KEYS,
                seen_names,
            )

            if no_results_found:
                print("No more reviews found. Ending crawl.")
                break  # Stop crawling when "No Results Found" message appears

            if not reviews:
                print(f"No reviews extracted from page {page_number}.")
                break  # Stop if no reviews are extracted

            # Add the reviews from this page to the total list
            all_reviews.extend(reviews)
            page_number += 1  # Move to the next page

            # Pause between requests to be polite and avoid rate limits
            await asyncio.sleep(2)  # Adjust sleep time as needed

    # Save the collected reviews to a CSV file
    if all_reviews:
        save_reviews_to_csv(all_reviews, "complete_reviews.csv")
        print(f"Saved {len(all_reviews)} reviews to 'complete_reviews.csv'.")
    else:
        print("No reviews were found during the crawl.")

    # Display usage statistics for the LLM strategy
    llm_strategy.show_usage()


async def main():
    """
    Entry point of the script.
    """
    await crawl_amazon_reviews()


if __name__ == "__main__":
    asyncio.run(main())
