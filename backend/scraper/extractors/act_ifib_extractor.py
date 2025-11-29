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
        
        # Extract opportunity name, bid closing date, clarification deadline, and expected contract award date from entire PDF using Groq
        opportunity_name, bid_closing_date, clarification_deadline, expected_contract_award_date = self._extract_fields_with_groq(pdf_text, opportunity_code)
        
        opportunity_data = {
            'opportunity_code': opportunity_code,
            'opportunity_type': 'IFIB',
            'opportunity_name': opportunity_name or page_info.get('page_title', 'Unknown'),
            'bid_closing_date': bid_closing_date,
            'clarification_deadline': clarification_deadline,
            'expected_contract_award_date': expected_contract_award_date,
            'url': page_info.get('url'),
            'pdf_url': page_info.get('pdf_url'),
        }
        
        logger.info(f"Extracted opportunity_code: {opportunity_code}")
        logger.info(f"Extracted opportunity_name: {opportunity_name}")
        logger.info(f"Extracted bid_closing_date: {bid_closing_date}")
        logger.info(f"Extracted clarification_deadline: {clarification_deadline}")
        logger.info(f"Extracted expected_contract_award_date: {expected_contract_award_date}")
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
    
    def _extract_fields_with_groq(self, pdf_text: str, opportunity_code: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extract opportunity_name, bid_closing_date, clarification_deadline, and expected_contract_award_date from PDF using Groq with chunking.
        
        Processes PDF in 5-page chunks until all fields are found or all pages are processed.
        Uses llama-3.1-8b-instant model (context window: ~8,192 tokens).
        
        Args:
            pdf_text: Full PDF text (entire document)
            opportunity_code: The opportunity code (e.g., "IFIB-ACT-SACT-26-07") for context
            
        Returns:
            Tuple of (opportunity_name, bid_closing_date, clarification_deadline, expected_contract_award_date)
        """
        if not self.use_llm or not self.llm_client:
            logger.warning("Groq client not available, skipping LLM extraction")
            return None, None, None, None
        
        if not pdf_text:
            logger.warning("No PDF text provided for Groq extraction")
            return None, None, None, None
        
        # Split PDF into pages
        pages = self._split_pdf_into_pages(pdf_text)
        total_pages = len(pages)
        logger.info(f"PDF split into {total_pages} pages")
        
        if total_pages == 0:
            logger.warning("No pages found in PDF text")
            return None, None, None, None
        
        # Track extracted fields
        opportunity_name = None
        bid_closing_date = None
        clarification_deadline = None
        expected_contract_award_date = None
        
        # Process in chunks of 5 pages to stay within Groq's ~8,192 token limit
        # With prompt overhead (~800 tokens) + 5 pages (~3,750 tokens) = ~4,550 tokens (safe)
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
            if not bid_closing_date:
                missing_fields.append("bid_closing_date")
            if not clarification_deadline:
                missing_fields.append("clarification_deadline")
            if not expected_contract_award_date:
                missing_fields.append("expected_contract_award_date")
            
            if missing_fields:
                logger.info(f"  Searching for: {', '.join(missing_fields)}")
            else:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
            
            # Extract from this chunk
            logger.info(f"  Calling Groq API for {page_range}...")
            chunk_name, chunk_date, chunk_clarification, chunk_award_date = self._extract_from_chunk(chunk_text, opportunity_code, page_range)
            
            # Add a small delay between API calls to avoid rate limits
            # This is especially important when processing multiple chunks
            if chunk_num > 1:
                import time
                time.sleep(1)  # 1 second delay between chunks
            
            # Update fields if found
            if chunk_name and not opportunity_name:
                opportunity_name = chunk_name
                logger.info(f"✅ Found opportunity_name in {page_range}: {chunk_name[:100]}...")
            elif not opportunity_name:
                logger.debug(f"  ❌ opportunity_name not found in {page_range}")
            
            if chunk_date and not bid_closing_date:
                bid_closing_date = chunk_date
                logger.info(f"✅ Found bid_closing_date in {page_range}: {chunk_date}")
            elif not bid_closing_date:
                logger.debug(f"  ❌ bid_closing_date not found in {page_range}")
            
            if chunk_clarification and not clarification_deadline:
                clarification_deadline = chunk_clarification
                logger.info(f"✅ Found clarification_deadline in {page_range}: {chunk_clarification}")
            elif not clarification_deadline:
                logger.debug(f"  ❌ clarification_deadline not found in {page_range}")
            
            if chunk_award_date and not expected_contract_award_date:
                expected_contract_award_date = chunk_award_date
                logger.info(f"✅ Found expected_contract_award_date in {page_range}: {chunk_award_date}")
            elif not expected_contract_award_date:
                logger.debug(f"  ❌ expected_contract_award_date not found in {page_range}")
            
            # If we have all fields, stop
            if opportunity_name and bid_closing_date and clarification_deadline and expected_contract_award_date:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
        
        logger.info(f"Final extraction result: name={bool(opportunity_name)}, date={bool(bid_closing_date)}, clarification={bool(clarification_deadline)}, award_date={bool(expected_contract_award_date)}")
        return opportunity_name, bid_closing_date, clarification_deadline, expected_contract_award_date
    
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
    
    def _extract_from_chunk(self, chunk_text: str, opportunity_code: Optional[str], page_range: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extract fields from a single chunk of PDF text.
        
        Args:
            chunk_text: Text from a chunk of pages
            opportunity_code: The opportunity code for context
            page_range: Description of which pages this chunk represents
            
        Returns:
            Tuple of (opportunity_name, bid_closing_date, clarification_deadline, expected_contract_award_date)
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

3. **clarification_deadline**: The deadline for submitting clarification questions. This MUST include:
   - The date (day, month, year)
   - The time (if specified)
   - The timezone (if specified)
   
   Look for phrases like:
   - "Clarification deadline"
   - "Deadline for clarifications"
   - "Questions must be submitted by"
   - "Clarification questions deadline"
   - "Deadline for questions"
   - "Clarification date"
   
   Extract the complete date and time information exactly as written in the document, including timezone if mentioned.

4. **expected_contract_award_date**: The expected date or timeframe when the contract will be awarded. This field can be:
   - A specific date (day, month, year) with time and timezone if specified
   - A month and year only (e.g., "March 2026", "Q2 2026")
   - A vague timeframe (e.g., "Spring 2026", "Summer 2026", "Q1 2026", "First quarter 2026")
   - A relative timeframe (e.g., "within 90 days of bid closing", "on date of award", "after evaluation")
   - Any other description of when the award is expected
   
   Look for phrases like:
   - "Expected contract award date"
   - "Contract award date"
   - "Award date"
   - "Expected award date"
   - "Anticipated award date"
   - "Contract award expected"
   - "Award timeframe"
   - "Expected award"
   - "Effective on date of award"
   - "On date of award"
   - "Upon date of award"
   - "Date of award"
   - "Award effective date"
   
   Extract the information exactly as written in the document, whether it's a specific date, a vague timeframe, or a relative description. Do not try to convert vague terms to specific dates. Phrases like "effective on date of award" or "upon date of award" should be extracted as-is.

Opportunity Code (for reference): {opportunity_code or 'Not provided'}
This section contains: {page_range}

Return your response as a JSON object with exactly these fields:
{{
    "opportunity_name": "the full opportunity name/title",
    "bid_closing_date": "the complete closing date with time and timezone if available",
    "clarification_deadline": "the complete clarification deadline with time and timezone if available",
    "expected_contract_award_date": "the expected contract award date/timeframe exactly as written (can be specific date, month/year, season, quarter, or relative description)"
}}

If a field cannot be found in this section, use null for that field. Do not make up information.

Document section text:
{chunk_text}"""

            # Call Groq API
            logger.info(f"    Preparing Groq API request for {page_range}...")
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
            logger.info(f"    Groq API response received for {page_range} ({len(response_content)} chars)")
            logger.debug(f"    Response preview: {response_content[:300]}...")
            
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
                clarification_deadline = extracted_data.get("clarification_deadline")
                expected_contract_award_date = extracted_data.get("expected_contract_award_date")
                
                # Validate and clean the extracted data
                if opportunity_name and (opportunity_name.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid opportunity_name: {opportunity_name}")
                    opportunity_name = None
                
                if bid_closing_date and (bid_closing_date.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid bid_closing_date: {bid_closing_date}")
                    bid_closing_date = None
                
                if clarification_deadline and (clarification_deadline.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid clarification_deadline: {clarification_deadline}")
                    clarification_deadline = None
                
                if expected_contract_award_date and (expected_contract_award_date.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid expected_contract_award_date: {expected_contract_award_date}")
                    expected_contract_award_date = None
                
                logger.info(f"    Extracted from {page_range}: name={bool(opportunity_name)}, bid_date={bool(bid_closing_date)}, clarification={bool(clarification_deadline)}, award_date={bool(expected_contract_award_date)}")
                if expected_contract_award_date:
                    logger.info(f"    Award date value: '{expected_contract_award_date}'")
                
                return opportunity_name, bid_closing_date, clarification_deadline, expected_contract_award_date
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Groq JSON response for {page_range}: {e}")
                logger.error(f"Response content: {response_content[:500]}")
                return None, None, None, None
                
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a timeout error (1 minute limit)
            if "timeout" in error_str or "timed out" in error_str or "read timeout" in error_str:
                logger.warning(f"⏱️  Timeout (1 minute limit) for {page_range}. This may cause missing fields. Error: {e}")
            # Check if it's a payload too large error (413) - chunk may be too big
            elif "413" in str(e) or "payload too large" in error_str or "request entity too large" in error_str:
                logger.warning(f"Payload too large for {page_range}. Chunk may exceed token limit. Error: {e}")
            # Check if it's a rate limit error
            elif "rate_limit" in error_str or "tokens per minute" in error_str or "rate limit" in error_str:
                logger.warning(f"Rate limit exceeded for {page_range}. Error: {e}")
            else:
                logger.error(f"Error calling Groq API for {page_range}: {e}")
            return None, None, None, None
