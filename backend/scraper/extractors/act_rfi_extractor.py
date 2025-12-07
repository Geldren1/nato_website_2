"""
ACT RFI-specific metadata extractor.
Extracts opportunity_code from URL using pattern matching.
"""

import json
import re
from typing import Dict, Optional, Tuple
from scraper.extractors.base import BaseExtractor
from core.logging import get_logger

logger = get_logger(__name__)


class ACTRFIExtractor(BaseExtractor):
    """Extractor for ACT RFI (Request for Information) opportunities."""
    
    def extract(self, pdf_text: str, page_info: Dict) -> Dict:
        """
        Extract RFI-specific metadata.
        
        Args:
            pdf_text: PDF text
            page_info: Page info (url, pdf_url, page_title, etc.)
            
        Returns:
            Dictionary with extracted opportunity data
        """
        logger.info("Extracting RFI metadata...")
        
        # Extract opportunity code from URL
        opportunity_code = self._extract_opportunity_code_from_url(page_info.get('url', ''))
        
        # Extract opportunity name, clarification deadline, and bid closing date from entire PDF using Groq
        opportunity_name, clarification_deadline, bid_closing_date = self._extract_fields_with_groq(pdf_text, opportunity_code)
        
        opportunity_data = {
            'opportunity_code': opportunity_code,
            'opportunity_type': 'RFI',
            'nato_body': 'ACT',
            'opportunity_name': opportunity_name or page_info.get('page_title', 'Unknown'),
            'clarification_deadline': clarification_deadline,
            'bid_closing_date': bid_closing_date,
            'url': page_info.get('url'),
            'pdf_url': page_info.get('pdf_url'),
        }
        
        logger.info(f"Extracted opportunity_code: {opportunity_code}")
        logger.info(f"Extracted opportunity_name: {opportunity_name}")
        logger.info(f"Extracted clarification_deadline: {clarification_deadline}")
        logger.info(f"Extracted bid_closing_date: {bid_closing_date}")
        return opportunity_data
    
    def _extract_opportunity_code_from_url(self, url: str) -> Optional[str]:
        """
        Extract opportunity code from URL using pattern matching.
        
        URL format examples:
        - https://www.act.nato.int/opportunities/contracting/rfi-act-sact-25-105/
        - https://www.act.nato.int/opportunities/contracting/rfi-act-sact-25-01/
        
        Expected output: RFI-ACT-SACT-25-105, RFI-ACT-SACT-25-01, etc.
        
        Args:
            url: The opportunity URL
            
        Returns:
            Opportunity code string or None if not found
        """
        if not url:
            return None
        
        # Pattern: rfi-act-sact-25-105 or rfi-act-sact-25-01
        # Match: rfi-act-sact-XX-XXX (case insensitive)
        pattern = r'rfi-act-sact-(\d+)-(\d+)'
        match = re.search(pattern, url.lower())
        
        if match:
            year = match.group(1)
            number = match.group(2)
            opportunity_code = f"RFI-ACT-SACT-{year}-{number}"
            logger.info(f"Extracted opportunity_code from URL: {opportunity_code}")
            return opportunity_code
        
        logger.warning(f"Could not extract opportunity_code from URL: {url}")
        return None
    
    def _extract_fields_with_groq(self, pdf_text: str, opportunity_code: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract opportunity_name, clarification_deadline, and bid_closing_date from PDF using Groq with chunking.
        
        Processes PDF in 5-page chunks until all fields are found or all pages are processed.
        Uses llama-3.1-8b-instant model (context window: ~8,192 tokens).
        
        Args:
            pdf_text: Full PDF text (entire document)
            opportunity_code: The opportunity code (e.g., "RFI-ACT-SACT-25-105") for context
            
        Returns:
            Tuple of (opportunity_name, clarification_deadline, bid_closing_date)
        """
        if not self.use_llm or not self.llm_client:
            logger.warning("Groq client not available, skipping LLM extraction")
            return None, None, None
        
        if not pdf_text:
            logger.warning("No PDF text provided for Groq extraction")
            return None, None, None
        
        # Split PDF into pages
        pages = self._split_pdf_into_pages(pdf_text)
        total_pages = len(pages)
        logger.info(f"PDF split into {total_pages} pages")
        
        if total_pages == 0:
            logger.warning("No pages found in PDF text")
            return None, None, None
        
        # Track extracted fields
        opportunity_name = None
        clarification_deadline = None
        bid_closing_date = None
        
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
            if not clarification_deadline:
                missing_fields.append("clarification_deadline")
            if not bid_closing_date:
                missing_fields.append("bid_closing_date")
            
            if missing_fields:
                logger.info(f"  Searching for: {', '.join(missing_fields)}")
            else:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
            
            # Extract from this chunk
            logger.info(f"  Calling Groq API for {page_range}...")
            chunk_name, chunk_clarification, chunk_date = self._extract_from_chunk(chunk_text, opportunity_code, page_range)
            
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
            
            if chunk_clarification and not clarification_deadline:
                clarification_deadline = chunk_clarification
                logger.info(f"✅ Found clarification_deadline in {page_range}: {chunk_clarification}")
            elif not clarification_deadline:
                logger.debug(f"  ❌ clarification_deadline not found in {page_range}")
            
            if chunk_date and not bid_closing_date:
                bid_closing_date = chunk_date
                logger.info(f"✅ Found bid_closing_date in {page_range}: {chunk_date}")
            elif not bid_closing_date:
                logger.debug(f"  ❌ bid_closing_date not found in {page_range}")
            
            # If we have all fields, stop
            if opportunity_name and clarification_deadline and bid_closing_date:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
        
        logger.info(f"Final extraction result: name={bool(opportunity_name)}, clarification={bool(clarification_deadline)}, bid_date={bool(bid_closing_date)}")
        return opportunity_name, clarification_deadline, bid_closing_date
    
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
    
    def _extract_from_chunk(self, chunk_text: str, opportunity_code: Optional[str], page_range: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract fields from a single chunk of PDF text.
        
        Args:
            chunk_text: Text from a chunk of pages
            opportunity_code: The opportunity code for context
            page_range: Description of which pages this chunk represents
            
        Returns:
            Tuple of (opportunity_name, clarification_deadline, bid_closing_date)
        """
        try:
            prompt = f"""Extract the following information from this section of an RFI (Request for Information) document:

1. **opportunity_name**: The full title/name of this opportunity. This is typically found near the opportunity code or at the beginning of the document. It should be the complete, descriptive title of the opportunity.

2. **clarification_deadline**: The deadline for submitting clarification questions. This MUST include:
   - The date (day, month, year)
   - The time (if specified)
   - The timezone (if specified)
   
   Look for phrases like:
   - "Clarification question deadline"
   - "Clarification deadline"
   - "Deadline for clarifications"
   - "Questions must be submitted by"
   - "Clarification questions deadline"
   - "Deadline for questions"
   - "Clarification date"
   
   Extract the complete date and time information exactly as written in the document, including timezone if mentioned.

3. **bid_closing_date**: The due date for submitting the RFI response. This MUST include:
   - The date (day, month, year)
   - The time (if specified)
   - The timezone (if specified)
   
   Look for phrases like:
   - "Due date"
   - "Submission deadline"
   - "Response deadline"
   - "Closing date"
   - "Bid closing date"
   - "Deadline for submission"
   - "Bids must be received by"
   - "Closing time"
   - "Response due date"
   - "RFI response deadline"
   
   Extract the complete date and time information exactly as written in the document, including timezone if mentioned.

Opportunity Code (for reference): {opportunity_code or 'Not provided'}
This section contains: {page_range}

Return your response as a JSON object with exactly these fields:
{{
    "opportunity_name": "the full opportunity name/title",
    "clarification_deadline": "the complete clarification deadline with time and timezone if available",
    "bid_closing_date": "the complete due date for submitting response with time and timezone if available"
}}

If a field cannot be found in this section, use null for that field. Do not make up information.

Document section text:
{chunk_text}"""

            response = self.llm_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from RFI documents. Always return valid JSON."},
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
            clarification_deadline = extracted_data.get("clarification_deadline")
            bid_closing_date = extracted_data.get("bid_closing_date")
            
            # Basic validation/cleanup
            if opportunity_name and opportunity_name.lower() in ["null", "none", "n/a", "not found"]:
                opportunity_name = None
            if clarification_deadline and clarification_deadline.lower() in ["null", "none", "n/a", "not found"]:
                clarification_deadline = None
            if bid_closing_date and bid_closing_date.lower() in ["null", "none", "n/a", "not found"]:
                bid_closing_date = None
            
            return opportunity_name, clarification_deadline, bid_closing_date
        except Exception as e:
            logger.error(f"Error calling Groq API for {page_range}: {e}")
            return None, None, None

