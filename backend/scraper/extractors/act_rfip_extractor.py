"""
ACT RFIP-specific metadata extractor.
Extracts opportunity_code from URL using pattern matching.
"""

import json
import re
from typing import Dict, Optional, Tuple
from scraper.extractors.base import BaseExtractor
from core.logging import get_logger

logger = get_logger(__name__)


class ACTRFIPExtractor(BaseExtractor):
    """Extractor for ACT RFIP (Request for Innovation Proposals) opportunities."""
    
    def extract(self, pdf_text: str, page_info: Dict) -> Dict:
        """
        Extract RFIP-specific metadata.
        
        Args:
            pdf_text: PDF text
            page_info: Page info (url, pdf_url, page_title, etc.)
            
        Returns:
            Dictionary with extracted opportunity data
        """
        logger.info("Extracting RFIP metadata...")
        
        # Extract opportunity code from URL
        opportunity_code = self._extract_opportunity_code_from_url(page_info.get('url', ''))
        
        # Extract opportunity name and bid submission deadline from entire PDF using Groq
        opportunity_name, bid_submission_deadline = self._extract_fields_with_groq(pdf_text, opportunity_code)
        
        opportunity_data = {
            'opportunity_code': opportunity_code,
            'opportunity_type': 'RFIP',
            'nato_body': 'ACT',
            'opportunity_name': opportunity_name or page_info.get('page_title', 'Unknown'),
            'bid_closing_date': bid_submission_deadline,  # Maps to bid_submission_deadline
            'url': page_info.get('url'),
            'pdf_url': page_info.get('pdf_url'),
        }
        
        logger.info(f"Extracted opportunity_code: {opportunity_code}")
        logger.info(f"Extracted opportunity_name: {opportunity_name}")
        logger.info(f"Extracted bid_submission_deadline: {bid_submission_deadline}")
        return opportunity_data
    
    def _extract_opportunity_code_from_url(self, url: str) -> Optional[str]:
        """
        Extract opportunity code from URL using pattern matching.
        
        URL format examples:
        - https://www.act.nato.int/opportunities/contracting/rfip-act-sact-25-104/
        - https://www.act.nato.int/opportunities/contracting/rfip-act-sact-25-01/
        
        Expected output: RFIP-ACT-SACT-25-104, RFIP-ACT-SACT-25-01, etc.
        
        Args:
            url: The opportunity URL
            
        Returns:
            Opportunity code string or None if not found
        """
        if not url:
            return None
        
        # Pattern: rfip-act-sact-25-104 or rfip-act-sact-25-01
        # Match: rfip-act-sact-XX-XXX (case insensitive)
        pattern = r'rfip-act-sact-(\d+)-(\d+)'
        match = re.search(pattern, url.lower())
        
        if match:
            year = match.group(1)
            number = match.group(2)
            opportunity_code = f"RFIP-ACT-SACT-{year}-{number}"
            logger.info(f"Extracted opportunity_code from URL: {opportunity_code}")
            return opportunity_code
        
        logger.warning(f"Could not extract opportunity_code from URL: {url}")
        return None
    
    def _extract_fields_with_groq(self, pdf_text: str, opportunity_code: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract opportunity_name and bid_submission_deadline from PDF using Groq with chunking.
        
        Processes PDF in 5-page chunks until all fields are found or all pages are processed.
        Uses llama-3.1-8b-instant model (context window: ~8,192 tokens).
        
        Args:
            pdf_text: Full PDF text (entire document)
            opportunity_code: The opportunity code (e.g., "RFIP-ACT-SACT-25-104") for context
            
        Returns:
            Tuple of (opportunity_name, bid_submission_deadline)
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
        bid_submission_deadline = None
        
        # Process in chunks of 5 pages to stay within Groq's ~8,192 token limit
        chunk_size = 5
        chunk_num = 0
        
        for start_page in range(0, total_pages, chunk_size):
            chunk_num += 1
            end_page = min(start_page + chunk_size, total_pages)
            page_range = f"pages {start_page + 1}-{end_page}"
            logger.info(f"Processing chunk {chunk_num}: {page_range} (total pages: {total_pages})")
            
            # Get chunk text
            chunk_text = "\n\n".join(pages[start_page:end_page])
            chunk_length = len(chunk_text)
            logger.info(f"  Chunk text length: {chunk_length:,} characters (~{chunk_length/4:.0f} tokens)")
            
            # Check what fields we still need
            missing_fields = []
            if not opportunity_name:
                missing_fields.append("opportunity_name")
            if not bid_submission_deadline:
                missing_fields.append("bid_submission_deadline")
            
            if missing_fields:
                logger.info(f"  Searching for: {', '.join(missing_fields)}")
            else:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
            
            # Extract from this chunk
            logger.info(f"  Calling Groq API for {page_range}...")
            chunk_name, chunk_deadline = self._extract_from_chunk(chunk_text, opportunity_code, page_range)
            
            # Add a small delay between API calls to avoid rate limits
            if chunk_num > 1:
                import time
                time.sleep(1)  # 1 second delay between chunks
            
            # Update fields if found
            if chunk_name and not opportunity_name:
                opportunity_name = chunk_name
                logger.info(f"✅ Found opportunity_name in {page_range}: {chunk_name[:100]}...")
            elif not opportunity_name:
                logger.debug(f"  ❌ opportunity_name not found in {page_range}")
            
            if chunk_deadline and not bid_submission_deadline:
                bid_submission_deadline = chunk_deadline
                logger.info(f"✅ Found bid_submission_deadline in {page_range}: {chunk_deadline}")
            elif not bid_submission_deadline:
                logger.debug(f"  ❌ bid_submission_deadline not found in {page_range}")
            
            # If we have all fields, stop
            if opportunity_name and bid_submission_deadline:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
        
        logger.info(f"Final extraction result: name={bool(opportunity_name)}, deadline={bool(bid_submission_deadline)}")
        return opportunity_name, bid_submission_deadline
    
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
            Tuple of (opportunity_name, bid_submission_deadline)
        """
        try:
            prompt = f"""Extract the following information from this section of an RFIP (Request for Innovation Proposals) document:

1. **opportunity_name**: The full title/name of this opportunity. This is typically found near the opportunity code or at the beginning of the document. It should be the complete, descriptive title of the opportunity. Examples may include phrases like "Innovation Challenge" followed by a date or theme.

2. **bid_submission_deadline**: The deadline for submitting bid proposals. This MUST include:
   - The date (day, month, year)
   - The time (if specified)
   - The timezone (if specified)
   
   Look for phrases like:
   - "Bid submission deadline"
   - "Submission deadline"
   - "Proposal deadline"
   - "Deadline for submission"
   - "Bids must be received by"
   - "Closing date"
   - "Closing time"
   - "Deadline"
   - "Due date"
   - "Submission due date"
   
   Extract the complete date and time information exactly as written in the document, including timezone if mentioned.

Opportunity Code (for reference): {opportunity_code or 'Not provided'}
This section contains: {page_range}

Return your response as a JSON object with exactly these fields:
{{
    "opportunity_name": "the full opportunity name/title",
    "bid_submission_deadline": "the complete bid submission deadline with date, time and timezone if available"
}}

If a field cannot be found in this section, use null for that field. Do not make up information.

Document section text:
{chunk_text}"""

            response = self.llm_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from RFIP documents. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            response_content = response_content.strip()
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            elif response_content.startswith("```"):
                response_content = response_content[3:]
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            response_content = response_content.strip()
            
            extracted_data = json.loads(response_content)
            opportunity_name = extracted_data.get("opportunity_name")
            bid_submission_deadline = extracted_data.get("bid_submission_deadline")
            
            # Basic validation/cleanup
            if opportunity_name and opportunity_name.lower() in ["null", "none", "n/a", "not found"]:
                opportunity_name = None
            if bid_submission_deadline and bid_submission_deadline.lower() in ["null", "none", "n/a", "not found"]:
                bid_submission_deadline = None
            
            return opportunity_name, bid_submission_deadline
        except Exception as e:
            logger.error(f"Error calling Groq API for {page_range}: {e}")
            return None, None

