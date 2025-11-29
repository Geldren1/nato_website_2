"""
ACT IFIB-specific metadata extractor.
Extracts opportunity_code from URL using pattern matching.
"""

import re
from typing import Dict, Optional
from scraper.extractors.base import BaseExtractor
from core.logging import get_logger

logger = get_logger(__name__)


class ACTIFIBExtractor(BaseExtractor):
    """Extractor for ACT IFIB (Invitation for Industry Bid) opportunities."""
    
    def extract(self, pdf_text: str, page_info: Dict) -> Dict:
        """
        Extract IFIB-specific metadata.
        
        Args:
            pdf_text: PDF text
            page_info: Page info (url, pdf_url, page_title, etc.)
            
        Returns:
            Dictionary with extracted opportunity data
        """
        logger.info("Extracting IFIB metadata...")
        
        # Extract opportunity code from URL
        opportunity_code = self._extract_opportunity_code_from_url(page_info.get('url', ''))
        
        # Extract opportunity name from first page of PDF using Groq
        opportunity_name = self._extract_opportunity_name_with_groq(pdf_text, opportunity_code)
        
        opportunity_data = {
            'opportunity_code': opportunity_code,
            'opportunity_type': 'IFIB',
            'opportunity_name': opportunity_name or page_info.get('page_title', 'Unknown'),
            'url': page_info.get('url'),
            'pdf_url': page_info.get('pdf_url'),
        }
        
        logger.info(f"Extracted opportunity_code: {opportunity_code}")
        logger.info(f"Extracted opportunity_name: {opportunity_name}")
        return opportunity_data
    
    def _extract_opportunity_code_from_url(self, url: str) -> Optional[str]:
        """
        Extract opportunity code from URL using pattern matching.
        
        URL format examples:
        - https://www.act.nato.int/opportunities/contracting/ifib-act-sact-26-07/
        - https://www.act.nato.int/opportunities/contracting/ifib-act-sact-26-01/
        
        Expected output: IFIB-ACT-SACT-26-07, IFIB-ACT-SACT-26-01, etc.
        
        Args:
            url: The opportunity URL
            
        Returns:
            Opportunity code string or None if not found
        """
        if not url:
            return None
        
        # Pattern: ifib-act-sact-26-07 or ifib-act-sact-26-01
        # Match: ifib-act-sact-XX-XX (case insensitive)
        pattern = r'ifib-act-sact-(\d+)-(\d+)'
        match = re.search(pattern, url.lower())
        
            if match:
            year = match.group(1)
            number = match.group(2)
            opportunity_code = f"IFIB-ACT-SACT-{year}-{number}"
            logger.info(f"Extracted opportunity_code from URL: {opportunity_code}")
            return opportunity_code
        
        logger.warning(f"Could not extract opportunity_code from URL: {url}")
        return None
    
    def _extract_opportunity_name_from_pdf(self, pdf_text: str, opportunity_code: Optional[str]) -> Optional[str]:
        """
        Extract opportunity name from first page of PDF, after the opportunity code.
        
        The opportunity name typically appears on the first page, right after the opportunity code.
        It may be on the same line or the next few lines.
        
        Args:
            pdf_text: Full PDF text
            opportunity_code: The opportunity code (e.g., "IFIB-ACT-SACT-26-07")
            
        Returns:
            Opportunity name string or None if not found
        """
        if not pdf_text:
                    return None
        
        # Get first page content
        first_page_text = ""
        if "--- PAGE 1 ---" in pdf_text:
            # Extract first page content
            first_page_end = pdf_text.find("--- PAGE 2 ---")
            if first_page_end > 0:
                first_page_text = pdf_text[:first_page_end]
            else:
                # If no page 2 marker, take first 3000 chars (likely first page)
                first_page_text = pdf_text[:3000]
        else:
            # No page markers, take first 3000 chars (likely first page)
            first_page_text = pdf_text[:3000]
        
        # If we have the opportunity code, look for text after it
        if opportunity_code:
            # Pattern 1: Look for opportunity code followed by title on same line or next lines
            # Remove dashes and spaces for flexible matching
            code_variations = [
                opportunity_code,  # IFIB-ACT-SACT-26-07
                opportunity_code.replace('-', ' '),  # IFIB ACT SACT 26 07
                opportunity_code.replace('-', ''),  # IFIBACTSACT2607
            ]
            
            for code_variant in code_variations:
                # Look for code followed by title (could be on same line or next few lines)
                # Pattern: code followed by whitespace/newlines, then title
                # Allow title to span multiple lines until we hit a blank line or certain delimiters
                # Stop at: blank line, "INVITATION FOR", "TABLE OF CONTENTS", or end of reasonable title length
                pattern = rf'{re.escape(code_variant)}[\s\n]+(.{{10,300}}?)(?:\n\s*\n|\n\s*(?:INVITATION\s+FOR|TABLE\s+OF\s+CONTENTS|1\.|ANNEX|SECTION)|$)'
                match = re.search(pattern, first_page_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                # Clean up common prefixes/suffixes
                title = re.sub(r'^(INVITATION\s+FOR\s+INDUSTRY\s+BID|IFIB|INVITATION\s+FOR\s+BID)\s*[-:]?\s*', '', title, flags=re.IGNORECASE)
                    # Replace newlines with spaces and clean up whitespace
                title = re.sub(r'\s+', ' ', title).strip()
                    # Remove trailing punctuation that might be from the next section
                    title = re.sub(r'[.:;]\s*$', '', title)
                    if len(title) > 10 and len(title) < 300:
                        logger.info(f"Extracted opportunity_name after code: {title[:100]}")
                    return title
        
        # Pattern 2: Look for common title patterns on first page
        # Titles often start with capital letters and contain keywords like "Support", "Management", "Development"
        title_patterns = [
            r'(?:Contractor\s+Support\s+(?:to|for)\s+[^\n]{10,150})',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\s+(?:Support|Management|Development|Initiative|Program|System)[^\n]{0,100})',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,}\s+[^\n]{0,100})',  # At least 3 capitalized words
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, first_page_text, re.IGNORECASE)
            if match:
                title = match.group(0).strip() if match.groups() == () else match.group(1).strip()
                # Clean up
                title = re.sub(r'^(INVITATION\s+FOR\s+INDUSTRY\s+BID|IFIB|INVITATION\s+FOR\s+BID)\s*[-:]?\s*', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s+', ' ', title).strip()
                if len(title) > 10 and len(title) < 200:
                    logger.info(f"Extracted opportunity_name via pattern: {title[:100]}")
                    return title
        
        logger.warning("Could not extract opportunity_name from PDF first page")
        return None
