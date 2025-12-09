"""
NATO Opportunities Scraper - ACT IFIB Scraper
"""

from playwright.async_api import async_playwright
import requests
import asyncio
import re
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
import pdfplumber
import tempfile
from urllib.parse import urljoin

from database.session import get_db_session
from models import Opportunity
from utils.date_parser import parse_opportunity_dates
from utils.url_comparison import urls_differ_by_ending, pdf_urls_differ
from scraper.config import SCRAPER_CONFIGS, extract_nato_body_from_url
from scraper.extractors import get_act_extractor
from external.groq.client import get_groq_client
from core.logging import get_logger

logger = get_logger(__name__)


class NATOOpportunitiesScraper:
    """Main scraper class for NATO ACT IFIB opportunities."""
    
    def __init__(self, config_name: str = "ACT-IFIB", use_llm: bool = True):
        """
        Initialize scraper.
        
        Args:
            config_name: Name of scraper config to use (e.g., "ACT-IFIB", "ACT-NOI")
            use_llm: Whether to use LLM for extraction
        """
        if config_name not in SCRAPER_CONFIGS:
            raise ValueError(f"Unknown config: {config_name}. Available: {list(SCRAPER_CONFIGS.keys())}")
        
        self.config = SCRAPER_CONFIGS[config_name]
        self.config_name = config_name
        self.base_url = self.config["base_url"]
        self.opportunity_type = self.config.get("opportunity_type", "IFIB")
        self.nato_body = self.config.get("nato_body", "ACT")
        self.url_filter = self.config.get("url_filter", "").lower()
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
                    
                    # Filter by opportunity type (e.g., 'ifib', 'noi')
                    if matches and self.url_filter and self.url_filter in final_url.lower():
                        text = await link.inner_text()
                        text = text.strip() if text else ""
                        if text:
                            opportunity_links.append({
                                'url': final_url,
                                'text': text
                            })
                            logger.info(f"✅ Found {self.opportunity_type} opportunity link: {text[:50]} -> {final_url}")
                
                logger.info("Closing browser...")
                await context.close()
                await browser.close()
                
                logger.info(f"Found {len(opportunity_links)} {self.opportunity_type} opportunity links")
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
            # Get opportunity type from config
            opportunity_type = self.opportunity_type
            
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
    
    def _extract_opportunity_code_from_url(self, url: str) -> Optional[str]:
        """
        Extract opportunity code from URL using the ACT IFIB extractor pattern.
        
        Args:
            url: The opportunity URL
            
        Returns:
            Opportunity code string or None if not found
        """
        # Use the appropriate extractor's method to extract opportunity code
        # Create a temporary extractor instance to use its method
        extractor = get_act_extractor(self.opportunity_type, use_llm=False, llm_client=None)
        return extractor._extract_opportunity_code_from_url(url)
    
    async def _reconcile_opportunities(self, website_links: List[Dict], db) -> Dict:
        """
        Reconcile website opportunities with database opportunities.
        
        Categorizes opportunities into:
        - New: opportunity_code not in DB
        - Amendments: opportunity_code exists but URL ending differs
        - Unchanged: opportunity_code exists and URL ending same
        - Removed: opportunity_code in DB but not on website
        
        Args:
            website_links: List of dicts with 'url' and 'text' keys from website
            db: Database session
            
        Returns:
            Dictionary with keys:
            - 'new': List of links to process (new opportunities)
            - 'amendments': List of tuples (link, existing_opportunity) for URL changes
            - 'unchanged': List of existing opportunities (just update last_checked_at)
            - 'removed': List of opportunities in DB but not on website (for logging only)
        """
        logger.info("Reconciling website opportunities with database...")
        
        # Extract opportunity_codes from website links
        website_codes = {}
        for link in website_links:
            url = link.get('url')
            if not url:
                continue
            
            opportunity_code = self._extract_opportunity_code_from_url(url)
            if opportunity_code:
                website_codes[opportunity_code] = link
            else:
                logger.warning(f"Could not extract opportunity_code from URL: {url}")
        
        logger.info(f"Found {len(website_codes)} opportunities on website (by opportunity_code)")
        
        # Get all existing opportunities for this nato_body and opportunity_type
        nato_body = self.nato_body
        opportunity_type = self.opportunity_type
        
        existing = db.query(Opportunity).filter(
            Opportunity.nato_body == nato_body,
            Opportunity.opportunity_type == opportunity_type
        ).all()
        
        existing_by_code = {opp.opportunity_code: opp for opp in existing}
        logger.info(f"Found {len(existing_by_code)} existing opportunities in database")
        
        # Categorize opportunities
        new = []
        amendments = []
        unchanged = []
        
        for code, link in website_codes.items():
            if code not in existing_by_code:
                # New opportunity
                new.append(link)
                logger.debug(f"New opportunity: {code} -> {link.get('url')}")
            else:
                # Existing opportunity - check if page URL or PDF URL has changed
                existing_opp = existing_by_code[code]
                website_url = link.get('url')
                
                # First check if page URL ending differs
                page_url_changed = urls_differ_by_ending(website_url, existing_opp.url)
                
                # Visit the page to get the PDF URL and compare
                logger.debug(f"Checking PDF URL for existing opportunity: {code}")
                page_info = await self.visit_opportunity_page(website_url)
                
                if page_info and page_info.get('pdf_url'):
                    website_pdf_url = page_info.get('pdf_url')
                    pdf_url_changed = pdf_urls_differ(website_pdf_url, existing_opp.pdf_url)
                    
                    if page_url_changed or pdf_url_changed:
                        # Either page URL or PDF URL changed - this is an amendment
                        amendments.append((link, existing_opp))
                        if page_url_changed:
                            logger.info(f"Amendment detected: {code} - Page URL changed from '{existing_opp.url}' to '{website_url}'")
                        if pdf_url_changed:
                            logger.info(f"Amendment detected: {code} - PDF URL changed from '{existing_opp.pdf_url}' to '{website_pdf_url}'")
                    else:
                        # Both page URL and PDF URL are the same - unchanged
                        unchanged.append(existing_opp)
                        logger.debug(f"Unchanged: {code} -> {website_url} (PDF: {website_pdf_url})")
                else:
                    # Could not get PDF URL - fall back to page URL comparison only
                    if page_url_changed:
                        amendments.append((link, existing_opp))
                        logger.info(f"Amendment detected: {code} - Page URL changed from '{existing_opp.url}' to '{website_url}' (could not check PDF URL)")
                    else:
                        unchanged.append(existing_opp)
                        logger.warning(f"Could not get PDF URL for {code}, marking as unchanged based on page URL only")
        
        # Find removed (in DB but not on website)
        removed = []
        for code, opp in existing_by_code.items():
            if code not in website_codes:
                removed.append(opp)
                logger.debug(f"Removed from website (keeping in DB): {code}")
        
        logger.info(f"Reconciliation complete: {len(new)} new, {len(amendments)} amendments, {len(unchanged)} unchanged, {len(removed)} removed from website")
        
        return {
            'new': new,
            'amendments': amendments,
            'unchanged': unchanged,
            'removed': removed
        }
    
    async def scrape_all(self, mode: str = "incremental") -> Dict[str, Any]:
        """
        Scrape all IFIB opportunities and save to database.
        
        Args:
            mode: "full" (process all) or "incremental" (reconcile first)
        
        Returns:
            Dictionary with detailed results:
            - new: List of newly created opportunities
            - amendments: List of amended opportunities
            - unchanged_count: Number of unchanged opportunities
            - removed_count: Number of opportunities removed from website
            - processed_count: Total number processed
            - timestamp: When the scrape completed
        """
        logger.info(f"Starting ACT IFIB scraper in {mode} mode...")
        
        # Phase 1: Discovery - Get all IFIB opportunity links from website
        links = await self.get_opportunity_links()
        
        if not links:
            logger.warning("No IFIB opportunities found")
            return 0
        
        logger.info(f"Found {len(links)} IFIB opportunities on website")
        
        if mode == "incremental":
            # Phase 2: Reconciliation - Compare with database
            db = get_db_session()
            try:
                reconciliation = await self._reconcile_opportunities(links, db)
                
                # Phase 3: Processing - Process only what needs it
                new_links = reconciliation['new']
                amendments = reconciliation['amendments']
                unchanged = reconciliation['unchanged']
                removed = reconciliation['removed']
                
                logger.info(f"Processing: {len(new_links)} new, {len(amendments)} amendments, {len(unchanged)} unchanged")
                
                # Process new opportunities and collect results
                new_opportunities = []
                for i, link in enumerate(new_links, 1):
                    logger.info(f"\n[NEW {i}/{len(new_links)}] Processing: {link.get('url')}")
                    success = await self._process_opportunity(link)
                    if success:
                        # Get the newly created opportunity using existing session
                        opportunity_code = self._extract_opportunity_code_from_url(link.get('url'))
                        if opportunity_code:
                            # Refresh session to see committed changes
                            db.commit()
                            new_opp = db.query(Opportunity).filter(
                                Opportunity.opportunity_code == opportunity_code
                            ).first()
                            if new_opp:
                                new_opportunities.append(new_opp)
                    await asyncio.sleep(2)
                
                # Process amendments and collect results
                amended_opportunities = []
                for i, (link, existing_opp) in enumerate(amendments, 1):
                    logger.info(f"\n[AMENDMENT {i}/{len(amendments)}] Processing: {link.get('url')} (existing: {existing_opp.opportunity_code})")
                    success = await self._process_opportunity(link, existing_opportunity=existing_opp)
                    if success:
                        # Refresh session to see committed changes
                        db.commit()
                        updated_opp = db.query(Opportunity).filter(
                            Opportunity.opportunity_code == existing_opp.opportunity_code
                        ).first()
                        if updated_opp:
                            amended_opportunities.append(updated_opp)
                    await asyncio.sleep(2)
                
                # Update last_checked_at for unchanged opportunities
                if unchanged:
                    logger.info(f"Updating last_checked_at for {len(unchanged)} unchanged opportunities...")
                    for opp in unchanged:
                        opp.last_checked_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"✅ Updated {len(unchanged)} unchanged opportunities")
                
                # Log removed opportunities (keep in DB, don't mark inactive)
                if removed:
                    logger.info(f"Note: {len(removed)} opportunities are in DB but not on website (keeping in DB)")
                    for opp in removed:
                        logger.debug(f"  - {opp.opportunity_code}: {opp.url}")
                
                processed_count = len(new_opportunities) + len(amended_opportunities)
                
                logger.info(f"\n✅ Scraping complete! Processed {processed_count} opportunities")
                
                return {
                    'new': new_opportunities,
                    'amendments': amended_opportunities,
                    'unchanged_count': len(unchanged),
                    'removed_count': len(removed),
                    'processed_count': processed_count,
                    'timestamp': datetime.utcnow()
                }
                
            finally:
                db.close()
        else:
            # Full mode: process all opportunities (current behavior)
            logger.info("Running in full mode - processing all opportunities")
            processed_count = 0
            new_opportunities = []
            
            # Process each opportunity
            db = get_db_session()
            try:
                for i, link in enumerate(links, 1):
                    url = link['url']
                    logger.info(f"\n[{i}/{len(links)}] Processing: {url}")
                    success = await self._process_opportunity(link)
                    if success:
                        processed_count += 1
                        # Get the opportunity that was created/updated
                        opportunity_code = self._extract_opportunity_code_from_url(url)
                        if opportunity_code:
                            # Refresh session to see committed changes
                            db.commit()
                            opp = db.query(Opportunity).filter(
                                Opportunity.opportunity_code == opportunity_code
                            ).first()
                            if opp:
                                new_opportunities.append(opp)
                    await asyncio.sleep(2)
            finally:
                db.close()
            
            logger.info(f"\n✅ Scraping complete! Processed {processed_count} opportunities")
            
            return {
                'new': new_opportunities,
                'amendments': [],
                'unchanged_count': 0,
                'removed_count': 0,
                'processed_count': processed_count,
                'timestamp': datetime.utcnow()
            }
    
    async def _process_opportunity(self, link: Dict, existing_opportunity: Optional[Opportunity] = None) -> bool:
        """
        Process a single opportunity: visit page, download PDF, extract data, save to database.
        
        Args:
            link: Dict with 'url' and 'text' keys
            existing_opportunity: Optional existing Opportunity object (for amendments)
            
        Returns:
            True if successful, False otherwise
        """
        url = link.get('url')
        if not url:
            logger.warning("Link missing URL")
            return False
        
        try:
            # Visit the opportunity page to get PDF link
            page_info = await self.visit_opportunity_page(url)
            
            if not page_info:
                logger.warning(f"Failed to visit page: {url}")
                return False
            
            pdf_url = page_info.get('pdf_url')
            if not pdf_url:
                logger.warning(f"No PDF found for: {url}")
                return False
            
            # Download PDF to temporary file
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_path = tmp_file.name
                
                if not self.download_pdf(pdf_url, tmp_path):
                    logger.warning(f"Failed to download PDF: {pdf_url}")
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    return False
                
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
                return False
            
            # Parse opportunity data
            opportunity_data = self.parse_opportunity_data(pdf_text, page_info)
            
            # Save to database
            db = get_db_session()
            try:
                opportunity_code = opportunity_data.get('opportunity_code')
                
                if existing_opportunity and opportunity_code:
                    # Re-query the opportunity in this session to avoid session issues
                    existing = db.query(Opportunity).filter(
                        Opportunity.opportunity_code == opportunity_code
                    ).first()
                    
                    if existing:
                        # Update existing opportunity (amendment or update)
                        # Check if this is an amendment (page URL or PDF URL changed)
                        page_url_changed = urls_differ_by_ending(url, existing.url)
                        pdf_url_changed = pdf_urls_differ(opportunity_data.get('pdf_url'), existing.pdf_url)
                        is_amendment = page_url_changed or pdf_url_changed
                        
                        # Track which fields are changing
                        changed_fields = []
                        
                        # Update all fields from new extraction and track changes
                        for key, value in opportunity_data.items():
                            if value is not None:
                                # Skip opportunity_code as it shouldn't change
                                if key == 'opportunity_code':
                                    continue
                                
                                # Get current value
                                current_value = getattr(existing, key, None)
                                
                                # Check if value actually changed
                                if current_value != value:
                                    setattr(existing, key, value)
                                    changed_fields.append(key)
                                    logger.debug(f"Field '{key}' changed: '{current_value}' -> '{value}'")
                        
                        # If URL changed, this is an amendment
                        if is_amendment:
                            # This is an amendment - increment amendment tracking
                            existing.amendment_count += 1
                            existing.has_amendments = True
                            existing.last_amendment_at = datetime.utcnow()
                            logger.info(f"Amendment detected for {existing.opportunity_code} (count: {existing.amendment_count})")
                            
                            # Ensure URL and PDF URL are in changed fields
                            if 'url' not in changed_fields:
                                changed_fields.append('url')
                            if 'pdf_url' not in changed_fields and opportunity_data.get('pdf_url') != existing.pdf_url:
                                changed_fields.append('pdf_url')
                        
                        # Update last_changed_fields if any fields changed
                        if changed_fields:
                            # Merge with existing changed_fields (keep unique)
                            existing_changed = existing.last_changed_fields or []
                            merged_changed = list(set(existing_changed + changed_fields))
                            existing.last_changed_fields = merged_changed
                            logger.debug(f"Changed fields: {merged_changed}")
                        
                        existing.last_checked_at = datetime.utcnow()
                        existing.updated_at = datetime.utcnow()
                        existing.update_count += 1
                        
                        if is_amendment:
                            logger.info(f"✅ Updated opportunity with amendment: {existing.opportunity_code} ({len(changed_fields)} fields changed)")
                        else:
                            logger.info(f"✅ Updated existing opportunity: {existing.opportunity_code} ({len(changed_fields)} fields changed)")
                    else:
                        # Opportunity code exists but not found in DB - create new
                        opportunity = Opportunity(**opportunity_data)
                        opportunity.last_checked_at = datetime.utcnow()
                        opportunity.extracted_at = datetime.utcnow()
                        db.add(opportunity)
                        logger.info(f"✅ Created new opportunity: {opportunity.opportunity_code}")
                else:
                    # Check if opportunity already exists by code (fallback - for full mode)
                    if opportunity_code:
                        existing = db.query(Opportunity).filter(
                            Opportunity.opportunity_code == opportunity_code
                        ).first()
                        
                        if existing:
                            # Update existing opportunity
                            # Check if this is an amendment (page URL or PDF URL changed)
                            page_url_changed = urls_differ_by_ending(url, existing.url)
                            pdf_url_changed = pdf_urls_differ(opportunity_data.get('pdf_url'), existing.pdf_url)
                            is_amendment = page_url_changed or pdf_url_changed
                            
                            # Track which fields are changing
                            changed_fields = []
                            
                            # Update all fields from new extraction and track changes
                            for key, value in opportunity_data.items():
                                if value is not None:
                                    # Skip opportunity_code as it shouldn't change
                                    if key == 'opportunity_code':
                                        continue
                                    
                                    # Get current value
                                    current_value = getattr(existing, key, None)
                                    
                                    # Check if value actually changed
                                    if current_value != value:
                                        setattr(existing, key, value)
                                        changed_fields.append(key)
                                        logger.debug(f"Field '{key}' changed: '{current_value}' -> '{value}'")
                            
                            # If URL changed, this is an amendment
                            if is_amendment:
                                # This is an amendment - increment amendment tracking
                                existing.amendment_count += 1
                                existing.has_amendments = True
                                existing.last_amendment_at = datetime.utcnow()
                                logger.info(f"Amendment detected for {existing.opportunity_code} (count: {existing.amendment_count})")
                                
                                # Ensure URL and PDF URL are in changed fields
                                if 'url' not in changed_fields:
                                    changed_fields.append('url')
                                if 'pdf_url' not in changed_fields and opportunity_data.get('pdf_url') != existing.pdf_url:
                                    changed_fields.append('pdf_url')
                            
                            # Update last_changed_fields if any fields changed
                            if changed_fields:
                                # Merge with existing changed_fields (keep unique)
                                existing_changed = existing.last_changed_fields or []
                                merged_changed = list(set(existing_changed + changed_fields))
                                existing.last_changed_fields = merged_changed
                                logger.debug(f"Changed fields: {merged_changed}")
                            
                            existing.last_checked_at = datetime.utcnow()
                            existing.updated_at = datetime.utcnow()
                            existing.update_count += 1
                            
                            if is_amendment:
                                logger.info(f"✅ Updated opportunity with amendment: {existing.opportunity_code} ({len(changed_fields)} fields changed)")
                            else:
                                logger.info(f"✅ Updated existing opportunity: {existing.opportunity_code} ({len(changed_fields)} fields changed)")
                        else:
                            # Create new opportunity
                            opportunity = Opportunity(**opportunity_data)
                            opportunity.last_checked_at = datetime.utcnow()
                            opportunity.extracted_at = datetime.utcnow()
                            db.add(opportunity)
                            logger.info(f"✅ Created new opportunity: {opportunity.opportunity_code}")
                    else:
                        logger.error("Cannot save opportunity: missing opportunity_code")
                        return False
                
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                logger.error(f"Error saving opportunity to database: {e}")
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing opportunity {url}: {e}")
            import traceback
            traceback.print_exc()
            return False

