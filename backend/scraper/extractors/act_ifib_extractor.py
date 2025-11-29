"""
ACT IFIB-specific metadata extractor.
Extracts opportunity_code from URL using pattern matching.
"""

import json
import re
from typing import Dict, Optional, Tuple
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
        
        # Extract opportunity name and bid closing date from entire PDF using Groq
        opportunity_name, bid_closing_date = self._extract_fields_with_groq(pdf_text, opportunity_code)
        
        opportunity_data = {
            'opportunity_code': opportunity_code,
            'opportunity_type': 'IFIB',
            'opportunity_name': opportunity_name or page_info.get('page_title', 'Unknown'),
            'bid_closing_date': bid_closing_date,
            'url': page_info.get('url'),
            'pdf_url': page_info.get('pdf_url'),
        }
        
        logger.info(f"Extracted opportunity_code: {opportunity_code}")
        logger.info(f"Extracted opportunity_name: {opportunity_name}")
        logger.info(f"Extracted bid_closing_date: {bid_closing_date}")
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
    
    def _extract_fields_with_groq(self, pdf_text: str, opportunity_code: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract opportunity_name and bid_closing_date from PDF using Groq with chunking.
        
        Processes PDF in 10-page chunks until all fields are found or all pages are processed.
        Uses llama-3.1-8b-instant model.
        
        Args:
            pdf_text: Full PDF text (entire document)
            opportunity_code: The opportunity code (e.g., "IFIB-ACT-SACT-26-07") for context
            
        Returns:
            Tuple of (opportunity_name, bid_closing_date)
        """
        if not self.use_llm or not self.llm_client:
            logger.warning("Groq client not available, skipping LLM extraction")
            return None, None
        
        if not pdf_text:
            logger.warning("No PDF text provided for Groq extraction")
            return None, None
        
        # Split PDF into pages
        pages = self._split_pdf_into_pages(pdf_text)
        total_pages = len(pages)
        logger.info(f"PDF split into {total_pages} pages")
        
        if total_pages == 0:
            logger.warning("No pages found in PDF text")
            return None, None
        
        # Track extracted fields
        opportunity_name = None
        bid_closing_date = None
        
        # Process in chunks of 10 pages
        chunk_size = 10
        chunk_num = 0
        
        for start_page in range(0, total_pages, chunk_size):
            chunk_num += 1
            end_page = min(start_page + chunk_size, total_pages)
            page_range = f"pages {start_page + 1}-{end_page}"
            logger.info(f"Processing chunk {chunk_num}: {page_range} (total pages: {total_pages})")
            
            # Get chunk text
            chunk_text = "\n\n".join(pages[start_page:end_page])
            
            # Check if we already have all fields
            if opportunity_name and bid_closing_date:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
            
            # Extract from this chunk
            chunk_name, chunk_date = self._extract_from_chunk(chunk_text, opportunity_code, page_range)
            
            # Update fields if found
            if chunk_name and not opportunity_name:
                opportunity_name = chunk_name
                logger.info(f"✅ Found opportunity_name in {page_range}")
            
            if chunk_date and not bid_closing_date:
                bid_closing_date = chunk_date
                logger.info(f"✅ Found bid_closing_date in {page_range}")
            
            # If we have all fields, stop
            if opportunity_name and bid_closing_date:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
        
        logger.info(f"Final extraction result: name={bool(opportunity_name)}, date={bool(bid_closing_date)}")
        return opportunity_name, bid_closing_date
    
    def _split_pdf_into_pages(self, pdf_text: str) -> list:
        """
        Split PDF text into individual pages.
        
        Args:
            pdf_text: Full PDF text
            
        Returns:
            List of page texts
        """
        pages = []
        
        # Check if PDF has page markers
        if "--- PAGE " in pdf_text:
            # Split by page markers
            page_pattern = r'--- PAGE (\d+) ---'
            page_matches = list(re.finditer(page_pattern, pdf_text))
            
            if page_matches:
                for i, match in enumerate(page_matches):
                    start_pos = match.end()
                    # End position is start of next page marker, or end of text
                    if i + 1 < len(page_matches):
                        end_pos = page_matches[i + 1].start()
                    else:
                        end_pos = len(pdf_text)
                    
                    page_text = pdf_text[start_pos:end_pos].strip()
                    if page_text:
                        pages.append(page_text)
            else:
                # Page markers found but no matches - use entire text as one page
                pages.append(pdf_text)
        else:
            # No page markers - estimate pages by splitting into chunks
            # Assume ~3000 characters per page
            chars_per_page = 3000
            for i in range(0, len(pdf_text), chars_per_page):
                page_text = pdf_text[i:i + chars_per_page].strip()
                if page_text:
                    pages.append(page_text)
        
        return pages
    
    def _extract_from_chunk(self, chunk_text: str, opportunity_code: Optional[str], page_range: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract fields from a single chunk of PDF text.
        
        Args:
            chunk_text: Text from a chunk of pages
            opportunity_code: The opportunity code for context
            page_range: Description of which pages this chunk represents
            
        Returns:
            Tuple of (opportunity_name, bid_closing_date)
        """
        try:
            # Prepare the prompt
            prompt = f"""Extract the following information from this section of an IFIB (Invitation for Industry Bid) document:

1. **opportunity_name**: The full title/name of this opportunity. This is typically found near the opportunity code or at the beginning of the document. It should be the complete, descriptive title of the opportunity.

2. **bid_closing_date**: The bid submission closing date/deadline. This MUST include:
   - The date (day, month, year)
   - The time (if specified)
   - The timezone (if specified)
   
   Look for phrases like:
   - "Closing date"
   - "Submission deadline"
   - "Bid closing date"
   - "Deadline for submission"
   - "Bids must be received by"
   - "Closing time"
   
   Extract the complete date and time information exactly as written in the document, including timezone if mentioned.

Opportunity Code (for reference): {opportunity_code or 'Not provided'}
This section contains: {page_range}

Return your response as a JSON object with exactly these fields:
{{
    "opportunity_name": "the full opportunity name/title",
    "bid_closing_date": "the complete closing date with time and timezone if available"
}}

If a field cannot be found in this section, use null for that field. Do not make up information.

Document section text:
{chunk_text}"""

            # Call Groq API
            logger.debug(f"Calling Groq API for {page_range}...")
            try:
                # Try with response_format first (if supported)
                response = self.llm_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that extracts structured information from IFIB documents. Always return valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,  # Low temperature for more deterministic extraction
                    response_format={"type": "json_object"}  # Force JSON response
                )
            except Exception as e:
                # If response_format is not supported, try without it
                if "response_format" in str(e) or "413" not in str(e):
                    logger.debug(f"response_format not supported for {page_range}, trying without it: {e}")
                response = self.llm_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that extracts structured information from IFIB documents. Always return valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1
                )
            
            # Parse the response
            response_content = response.choices[0].message.content
            logger.debug(f"Groq response for {page_range}: {response_content[:200]}...")  # Log first 200 chars
            
            # Clean up response - remove markdown code blocks if present
            response_content = response_content.strip()
            if response_content.startswith("```json"):
                response_content = response_content[7:]  # Remove ```json
            elif response_content.startswith("```"):
                response_content = response_content[3:]  # Remove ```
            if response_content.endswith("```"):
                response_content = response_content[:-3]  # Remove closing ```
            response_content = response_content.strip()
            
            # Parse JSON response
            try:
                extracted_data = json.loads(response_content)
                opportunity_name = extracted_data.get("opportunity_name")
                bid_closing_date = extracted_data.get("bid_closing_date")
                
                # Validate and clean the extracted data
                if opportunity_name and (opportunity_name.lower() in ["null", "none", "n/a", "not found"]):
                    opportunity_name = None
                
                if bid_closing_date and (bid_closing_date.lower() in ["null", "none", "n/a", "not found"]):
                    bid_closing_date = None
                
                return opportunity_name, bid_closing_date
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Groq JSON response for {page_range}: {e}")
                logger.error(f"Response content: {response_content[:500]}")
                return None, None
                
        except Exception as e:
            # Check if it's a rate limit error
            if "413" in str(e) or "rate_limit" in str(e).lower() or "tokens per minute" in str(e).lower():
                logger.warning(f"Rate limit exceeded for {page_range}. Chunk may be too large. Error: {e}")
            else:
                logger.error(f"Error calling Groq API for {page_range}: {e}")
            return None, None
