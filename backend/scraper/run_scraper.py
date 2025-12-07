"""
Script to run a NATO opportunities scraper.
Accepts config_name as command-line argument (e.g., "ACT-IFIB", "ACT-NOI").
"""

import asyncio
import sys
from scraper.scraper import NATOOpportunitiesScraper
from core.logging import get_logger

logger = get_logger(__name__)


async def main(config_name: str = "ACT-IFIB"):
    """
    Main function to run the scraper.
    
    Args:
        config_name: Name of scraper config to use (e.g., "ACT-IFIB", "ACT-NOI")
    """
    try:
        scraper = NATOOpportunitiesScraper(config_name=config_name, use_llm=True)
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
    # Get config_name from command-line argument, default to "ACT-IFIB"
    config_name = sys.argv[1] if len(sys.argv) > 1 else "ACT-IFIB"
    asyncio.run(main(config_name=config_name))

