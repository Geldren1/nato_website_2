"""
NATO Opportunities Scraper - ACT IFIB Scraper
"""

from playwright.async_api import async_playwright
import requests
import asyncio
import re
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging
import pdfplumber
import tempfile
from urllib.parse import urljoin

from database.session import get_db_session
from models import Opportunity
from utils.date_parser import parse_opportunity_dates
from scraper.config import SCRAPER_CONFIGS, extract_nato_body_from_url
from scraper.extractors import get_act_extractor
from external.groq.client import get_groq_client
from core.logging import get_logger

logger = get_logger(__name__)


class NATOOpportunitiesScraper:
    """Main scraper class for NATO ACT IFIB opportunities."""
    
    def __init__(self, config_name: str = "ACT", use_llm: bool = True):
        """
        Initialize scraper.
        
        Args:
            config_name: Name of scraper config to use (e.g., "ACT")
            use_llm: Whether to use LLM for extraction
        """
        if config_name not in SCRAPER_CONFIGS:
            raise ValueError(f"Unknown config: {config_name}. Available: {list(SCRAPER_CONFIGS.keys())}")
        
        self.config = SCRAPER_CONFIGS[config_name]
        self.config_name = config_name
        self.base_url = self.config["base_url"]
        self.use_llm = use_llm
        self.llm_client = None
        
        # Initialize Groq client if using LLM
        if self.use_llm:
            try:
                groq_client_wrapper = get_groq_client()
                if groq_client_wrapper and groq_client_wrapper.is_configured():
                    self.llm_client = groq_client_wrapper.get_client()
                    if self.llm_client:
                        logger.info("✅ Groq API client initialized successfully", event_type="groq_init_success")
                    else:
                        logger.warning("⚠️  Groq client not available - will use pattern matching", event_type="groq_init_warning")
                        self.use_llm = False
                else:
                    logger.warning("⚠️  Groq API key not found in environment - will use pattern matching", event_type="groq_init_warning")
                    self.use_llm = False
            except Exception as e:
                logger.warning(f"❌ Could not initialize Groq client: {e}", event_type="groq_init_error", error=str(e))
                logger.warning("⚠️  Falling back to pattern matching extraction")
                self.use_llm = False
    
    async def get_opportunity_links(self) -> List[Dict]:
        """
        Get list of IFIB opportunity links from main page.
        
        Returns:
            List of dicts with 'url' and 'text' keys for IFIB opportunities only
        """
        logger.info(f"Getting IFIB opportunity links from {self.base_url}...")
        
        try:
            headless_mode = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
            
            async with async_playwright() as p:
                logger.info("Launching Chromium...")
                browser = await p.chromium.launch(
                    headless=headless_mode,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                logger.info("Navigating to website...")
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
                logger.info("Navigation completed")
                
                logger.info("Waiting for JavaScript to render content...")
                await asyncio.sleep(5)
                
                # Get all links
                logger.info("Looking for opportunity links...")
                all_links = await page.query_selector_all("a")
                logger.info(f"Found {len(all_links)} total links on page")
                
                # Filter for IFIB opportunity links using pattern from config
                opportunity_links = []
                pattern = self.config.get("url_pattern")
                
                for link in all_links:
                    href = await link.get_attribute("href")
                    if not href:
                        continue
                    
                    # Check if it matches the pattern
                    matches = False
                    final_url = href
                    
                    if pattern and re.match(pattern, href):
                        matches = True
                        final_url = href if href.startswith('http') else urljoin(self.base_url, href)
                    else:
                        # Try resolving relative URLs and check again
                        resolved_href = href if href.startswith('http') else urljoin(self.base_url, href)
                        if pattern and re.match(pattern, resolved_href):
                            matches = True
                            final_url = resolved_href
                    
                    # Only include IFIB opportunities
                    if matches and 'ifib' in final_url.lower():
                        text = await link.inner_text()
                        text = text.strip() if text else ""
                        if text:
                            opportunity_links.append({
                                'url': final_url,
                                'text': text
                            })
                            logger.info(f"✅ Found IFIB opportunity link: {text[:50]} -> {final_url}")
                
                logger.info("Closing browser...")
                await context.close()
                await browser.close()
                
                logger.info(f"Found {len(opportunity_links)} IFIB opportunity links")
                return opportunity_links
                
        except Exception as e:
            logger.error(f"Error getting opportunity links: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def visit_opportunity_page(self, url: str) -> Optional[Dict]:
        """
        Visit opportunity page and extract PDF link.
        
        Args:
            url: URL of the opportunity page
            
        Returns:
            Dict with page info and PDF link, or None if failed
        """
        logger.info(f"Visiting opportunity page: {url}")
        
        try:
            headless_mode = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
            
            async with async_playwright() as p:
                logger.info("Launching Chromium...")
                browser = await p.chromium.launch(
                    headless=headless_mode,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                
                await page.set_extra_http_headers({
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })
                
                logger.info("Navigating to opportunity page...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                logger.info("Navigation completed")
                
                logger.info("Waiting 5 seconds for content to load...")
                await asyncio.sleep(5)
                
                page_title = await page.title()
                logger.info(f"Page title: {page_title}")
                
                # Look for PDF download link
                logger.info("Looking for PDF download link...")
                pdf_selector = self.config.get("pdf_selector", 'a[target="_blank"][rel="noopener"]')
                pdf_links = await page.query_selector_all(pdf_selector)
                logger.info(f"Found {len(pdf_links)} links with selector '{pdf_selector}'")
                
                pdf_url = None
                
                for link in pdf_links:
                    href = await link.get_attribute("href")
                    if href and href.endswith('.pdf'):
                        # Resolve relative PDF URLs
                        if not href.startswith('http'):
                            href = urljoin(url, href)
                        pdf_url = href
                        logger.info(f"✅ Found PDF link: {pdf_url}")
                        break
                
                # Fallback: look for any PDF link
                if not pdf_url:
                    logger.warning("No PDF link found with method 1, trying alternative methods...")
                    all_links = await page.query_selector_all("a")
                    for link in all_links:
                        href = await link.get_attribute("href")
                        if href and href.endswith('.pdf'):
                            if not href.startswith('http'):
                                href = urljoin(url, href)
                            pdf_url = href
                            logger.info(f"✅ Found PDF link (method 2): {pdf_url}")
                            break
                
                await context.close()
                await browser.close()
                
                if pdf_url:
                    return {
                        'url': url,
                        'pdf_url': pdf_url,
                        'page_title': page_title,
                    }
                else:
                    logger.warning(f"❌ No PDF link found for {url}")
                    return {
                        'url': url,
                        'pdf_url': None,
                        'page_title': page_title,
                    }
                    
        except Exception as e:
            logger.error(f"Error visiting page {url}: {e}")
            import traceback
            traceback.print_exc()
            # Browser cleanup is handled by async_playwright context manager
            return None
    
    def download_pdf(self, pdf_url: str, filepath: str) -> bool:
        """
        Download PDF from given URL.
        
        Args:
            pdf_url: URL of the PDF to download
            filepath: Local filepath to save PDF
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading PDF from: {pdf_url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/pdf,*/*',
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type or pdf_url.lower().endswith('.pdf'):
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"✅ PDF saved successfully")
                    return True
                else:
                    logger.warning(f"❌ Not a PDF file. Content type: {content_type}")
                    return False
            else:
                logger.warning(f"❌ Failed to download PDF. Status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error downloading PDF: {e}")
            return False
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        try:
            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"\n--- PAGE {i+1} ---\n"
                        full_text += page_text
                
                logger.info(f"Total text extracted: {len(full_text)} characters")
                return full_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def parse_opportunity_data(self, pdf_text: str, page_info: Dict) -> Dict:
        """
        Parse opportunity data from PDF text and page info.
        Uses organization-specific extractors (e.g., ACT IFIB extractor).
        
        Args:
            pdf_text: Extracted text from PDF
            page_info: Basic info from HTML page
            
        Returns:
            Structured opportunity data dictionary
        """
        logger.info("Parsing opportunity data from PDF text...")
        
        try:
            # Determine opportunity type from URL or config
            # For ACT, we know it's IFIB from the config
            opportunity_type = "IFIB"  # TODO: Make this dynamic based on URL/config
            
            # Get the appropriate extractor for this organization and opportunity type
            extractor = get_act_extractor(opportunity_type, use_llm=self.use_llm, llm_client=self.llm_client)
            opportunity_data = extractor.extract(pdf_text or "", page_info)
            
            # Add additional fields that are common to all opportunities
            url = page_info.get('url', '')
            opportunity_data['nato_body'] = extract_nato_body_from_url(url, self.config)
            opportunity_data['source_url'] = self.base_url
            
            # Parse dates
            opportunity_data = parse_opportunity_dates(opportunity_data)
            
            logger.info(f"Extracted data: {len([v for v in opportunity_data.values() if v is not None])} fields with data")
            return opportunity_data
            
        except Exception as e:
            logger.error(f"Error parsing opportunity data: {e}")
            import traceback
            traceback.print_exc()
            error_data = {
                'opportunity_code': None,
                'opportunity_name': page_info.get('page_title', 'Unknown'),
                'url': page_info.get('url'),
                'pdf_url': page_info.get('pdf_url'),
                'nato_body': extract_nato_body_from_url(page_info.get('url', ''), self.config),
                'source_url': self.base_url,
            }
            return error_data
    
    async def scrape_all(self) -> int:
        """
        Scrape all IFIB opportunities and save to database.
        
        Returns:
            Number of opportunities scraped
        """
        logger.info("Starting ACT IFIB scraper...")
        
        # Get all IFIB opportunity links
        links = await self.get_opportunity_links()
        
        if not links:
            logger.warning("No IFIB opportunities found")
            return 0
        
        logger.info(f"Found {len(links)} IFIB opportunities to scrape")
        
        scraped_count = 0
        
        # Process each opportunity
        for i, link in enumerate(links, 1):
            url = link['url']
            logger.info(f"\n[{i}/{len(links)}] Processing: {url}")
            
            try:
                # Visit the opportunity page to get PDF link
                page_info = await self.visit_opportunity_page(url)
                
                if not page_info:
                    logger.warning(f"Failed to visit page: {url}")
                    continue
                
                pdf_url = page_info.get('pdf_url')
                if not pdf_url:
                    logger.warning(f"No PDF found for: {url}")
                    continue
                
                # Download PDF to temporary file
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_path = tmp_file.name
                    
                    if not self.download_pdf(pdf_url, tmp_path):
                        logger.warning(f"Failed to download PDF: {pdf_url}")
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                        continue
                    
                    # Extract text from PDF
                    pdf_text = self.extract_pdf_text(tmp_path)
                    
                finally:
                    # Always clean up temp file, even if extraction fails
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                            logger.debug(f"Cleaned up temporary PDF file: {tmp_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete temp PDF file {tmp_path}: {e}")
                
                if not pdf_text or len(pdf_text.strip()) < 100:
                    logger.warning(f"PDF text too short or empty: {url}")
                    continue
                
                # Parse opportunity data
                opportunity_data = self.parse_opportunity_data(pdf_text, page_info)
                
                # Save to database
                db = get_db_session()
                try:
                    # Check if opportunity already exists
                    existing = db.query(Opportunity).filter(
                        Opportunity.url == opportunity_data.get('url')
                    ).first()
                    
                    if existing:
                        # Update existing opportunity
                        for key, value in opportunity_data.items():
                            if value is not None:
                                setattr(existing, key, value)
                        existing.last_checked_at = datetime.utcnow()
                        existing.updated_at = datetime.utcnow()
                        logger.info(f"✅ Updated existing opportunity: {existing.opportunity_code}")
                    else:
                        # Create new opportunity
                        opportunity = Opportunity(**opportunity_data)
                        opportunity.last_checked_at = datetime.utcnow()
                        opportunity.extracted_at = datetime.utcnow()
                        db.add(opportunity)
                        logger.info(f"✅ Created new opportunity: {opportunity.opportunity_code}")
                    
                    db.commit()
                    scraped_count += 1
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error saving opportunity to database: {e}")
                    raise
                finally:
                    db.close()
                
                # Add delay between opportunities to be respectful
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing opportunity {url}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        logger.info(f"\n✅ Scraping complete! Processed {scraped_count} opportunities")
        return scraped_count

