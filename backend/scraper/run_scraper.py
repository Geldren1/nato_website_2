"""
Script to run the ACT IFIB scraper.
"""

import asyncio
import sys
from scraper.scraper import NATOOpportunitiesScraper
from core.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Main function to run the scraper."""
    try:
        scraper = NATOOpportunitiesScraper(config_name="ACT", use_llm=True)
        results = await scraper.scrape_all(mode="incremental")
        logger.info(f"Scraping completed. Processed {results.get('processed_count', 0)} opportunities.")
        logger.info(f"  New: {len(results.get('new', []))}, Amended: {len(results.get('amendments', []))}")
        return results.get('processed_count', 0)
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

