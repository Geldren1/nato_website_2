"""
ACT NOI-specific metadata extractor.
Extracts opportunity_code from URL using pattern matching.
"""

import json
import re
from typing import Dict, Optional, Tuple
from scraper.extractors.base import BaseExtractor
from core.logging import get_logger

logger = get_logger(__name__)


class ACTNOIExtractor(BaseExtractor):
    """Extractor for ACT NOI (Notification of Intent) opportunities."""
    
    def extract(self, pdf_text: str, page_info: Dict) -> Dict:
        """
        Extract NOI-specific metadata.
        
        Args:
            pdf_text: PDF text
            page_info: Page info (url, pdf_url, page_title, etc.)
            
        Returns:
            Dictionary with extracted opportunity data
        """
        logger.info("Extracting NOI metadata...")
        
        # Extract opportunity code from URL
        opportunity_code = self._extract_opportunity_code_from_url(page_info.get('url', ''))
        
        # Extract opportunity name, contract type, estimated value, target issue date, and target bid closing date from entire PDF using Groq
        opportunity_name, contract_type, estimated_value, target_issue_date, target_bid_closing_date = self._extract_fields_with_groq(pdf_text, opportunity_code)
        
        opportunity_data = {
            'opportunity_code': opportunity_code,
            'opportunity_type': 'NOI',
            'opportunity_name': opportunity_name or page_info.get('page_title', 'Unknown'),
            'contract_type': contract_type,
            'estimated_value': estimated_value,
            'target_issue_date': target_issue_date,
            'target_bid_closing_date': target_bid_closing_date,
            'url': page_info.get('url'),
            'pdf_url': page_info.get('pdf_url'),
        }
        
        logger.info(f"Extracted opportunity_code: {opportunity_code}")
        logger.info(f"Extracted opportunity_name: {opportunity_name}")
        logger.info(f"Extracted contract_type: {contract_type}")
        logger.info(f"Extracted estimated_value: {estimated_value}")
        logger.info(f"Extracted target_issue_date: {target_issue_date}")
        logger.info(f"Extracted target_bid_closing_date: {target_bid_closing_date}")
        return opportunity_data
    
    def _extract_opportunity_code_from_url(self, url: str) -> Optional[str]:
        """
        Extract opportunity code from URL using pattern matching.
        
        URL format examples:
        - https://www.act.nato.int/opportunities/contracting/noi-act-sact-26-16/
        - https://www.act.nato.int/opportunities/contracting/noi-act-sact-26-01/
        
        Expected output: NOI-ACT-SACT-26-16, NOI-ACT-SACT-26-01, etc.
        
        Args:
            url: The opportunity URL
            
        Returns:
            Opportunity code string or None if not found
        """
        if not url:
            return None
        
        # Pattern: noi-act-sact-26-16 or noi-act-sact-26-01
        # Match: noi-act-sact-XX-XX (case insensitive)
        pattern = r'noi-act-sact-(\d+)-(\d+)'
        match = re.search(pattern, url.lower())
        
        if match:
            year = match.group(1)
            number = match.group(2)
            opportunity_code = f"NOI-ACT-SACT-{year}-{number}"
            logger.info(f"Extracted opportunity_code from URL: {opportunity_code}")
            return opportunity_code
        
        logger.warning(f"Could not extract opportunity_code from URL: {url}")
        return None
    
    def _extract_fields_with_groq(self, pdf_text: str, opportunity_code: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extract opportunity_name, contract_type, estimated_value, target_issue_date, and target_bid_closing_date from PDF using Groq with chunking.
        
        Processes PDF in 5-page chunks until all fields are found or all pages are processed.
        Uses llama-3.1-8b-instant model (context window: ~8,192 tokens).
        
        Args:
            pdf_text: Full PDF text (entire document)
            opportunity_code: The opportunity code (e.g., "NOI-ACT-SACT-26-16") for context
            
        Returns:
            Tuple of (opportunity_name, contract_type, estimated_value, target_issue_date, target_bid_closing_date)
        """
        if not self.use_llm or not self.llm_client:
            logger.warning("Groq client not available, skipping LLM extraction")
            return None, None, None, None, None
        
        if not pdf_text:
            logger.warning("No PDF text provided for Groq extraction")
            return None, None, None, None, None
        
        # Split PDF into pages
        pages = self._split_pdf_into_pages(pdf_text)
        total_pages = len(pages)
        logger.info(f"PDF split into {total_pages} pages")
        
        if total_pages == 0:
            logger.warning("No pages found in PDF text")
            return None, None, None, None, None
        
        # Track extracted fields
        opportunity_name = None
        contract_type = None
        estimated_value = None
        target_issue_date = None
        target_bid_closing_date = None
        
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
            if not contract_type:
                missing_fields.append("contract_type")
            if not estimated_value:
                missing_fields.append("estimated_value")
            if not target_issue_date:
                missing_fields.append("target_issue_date")
            if not target_bid_closing_date:
                missing_fields.append("target_bid_closing_date")
            
            if missing_fields:
                logger.info(f"  Searching for: {', '.join(missing_fields)}")
            else:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
            
            # Extract from this chunk
            logger.info(f"  Calling Groq API for {page_range}...")
            chunk_name, chunk_contract_type, chunk_estimated_value, chunk_issue_date, chunk_bid_date = self._extract_from_chunk(chunk_text, opportunity_code, page_range)
            
            # Add a small delay between API calls to avoid rate limits
            if chunk_num > 1:
                import time
                time.sleep(1)  # 1 second delay between chunks
            
            # Update fields if found
            if chunk_name and not opportunity_name:
                opportunity_name = chunk_name
                logger.info(f"✅ Found opportunity_name in {page_range}: {chunk_name[:100]}...")
            
            if chunk_contract_type and not contract_type:
                contract_type = chunk_contract_type
                logger.info(f"✅ Found contract_type in {page_range}: {chunk_contract_type}")
            
            if chunk_estimated_value and not estimated_value:
                estimated_value = chunk_estimated_value
                logger.info(f"✅ Found estimated_value in {page_range}: {chunk_estimated_value}")
            
            if chunk_issue_date and not target_issue_date:
                target_issue_date = chunk_issue_date
                logger.info(f"✅ Found target_issue_date in {page_range}: {chunk_issue_date}")
            
            if chunk_bid_date and not target_bid_closing_date:
                target_bid_closing_date = chunk_bid_date
                logger.info(f"✅ Found target_bid_closing_date in {page_range}: {chunk_bid_date}")
            
            # If we have all fields, stop
            if opportunity_name and contract_type and estimated_value and target_issue_date and target_bid_closing_date:
                logger.info(f"✅ All fields extracted! Stopping at {page_range}")
                break
        
        logger.info(f"Final extraction result: name={bool(opportunity_name)}, contract_type={bool(contract_type)}, estimated_value={bool(estimated_value)}, target_issue_date={bool(target_issue_date)}, target_bid_closing_date={bool(target_bid_closing_date)}")
        return opportunity_name, contract_type, estimated_value, target_issue_date, target_bid_closing_date
    
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
    
    def _extract_from_chunk(self, chunk_text: str, opportunity_code: Optional[str], page_range: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extract fields from a single chunk of PDF text.
        
        Args:
            chunk_text: Text from a chunk of pages
            opportunity_code: The opportunity code for context
            page_range: Description of which pages this chunk represents
            
        Returns:
            Tuple of (opportunity_name, contract_type, estimated_value, target_issue_date, target_bid_closing_date)
        """
        try:
            # Prepare the prompt
            prompt = f"""Extract the following information from this section of an NOI (Notification of Intent) document:

1. **opportunity_name**: The full title/name of this opportunity. This is typically found near the opportunity code or at the beginning of the document. It should be the complete, descriptive title of the opportunity.

2. **contract_type**: The type of contract (e.g., "Firm Fixed Price", "Cost Plus Fixed Fee", "Time and Materials", etc.). Look for phrases like:
   - "Type of Contract"
   - "Contract Type"
   - "Type:"
   - "Contracting method"

3. **estimated_value**: The estimated contract value. This should include:
   - The currency (e.g., EUR, USD, GBP)
   - The amount (e.g., "EUR 500,000", "USD 1,000,000")
   - Look for phrases like:
     - "Estimated value"
     - "Estimated contract value"
     - "Value"
     - "Budget"
     - "Estimated cost"

4. **target_issue_date**: The target date when the opportunity will be issued. This MUST include:
   - The date (day, month, year)
   - The time (if specified)
   - The timezone (if specified)
   
   Look for phrases like:
   - "Target issue date"
   - "Expected issue date"
   - "Planned issue date"
   - "Issue date"
   - "Target date for issue"
   
   Extract the complete date and time information exactly as written in the document, including timezone if mentioned.

5. **target_bid_closing_date**: The target date for bid closing/submission deadline. This MUST include:
   - The date (day, month, year)
   - The time (if specified)
   - The timezone (if specified)
   
   Look for phrases like:
   - "Target bid closing date"
   - "Target closing date"
   - "Expected closing date"
   - "Planned closing date"
   - "Target submission date"
   - "Bid closing date"
   
   Extract the complete date and time information exactly as written in the document, including timezone if mentioned.

Opportunity Code (for reference): {opportunity_code or 'Not provided'}
This section contains: {page_range}

Return your response as a JSON object with exactly these fields:
{{
    "opportunity_name": "the full opportunity name/title",
    "contract_type": "the type of contract",
    "estimated_value": "the estimated value with currency",
    "target_issue_date": "the complete target issue date with time and timezone if available",
    "target_bid_closing_date": "the complete target bid closing date with time and timezone if available"
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
                            "content": "You are a helpful assistant that extracts structured information from NOI documents. Always return valid JSON."
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
                            "content": "You are a helpful assistant that extracts structured information from NOI documents. Always return valid JSON."
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
                contract_type = extracted_data.get("contract_type")
                estimated_value = extracted_data.get("estimated_value")
                target_issue_date = extracted_data.get("target_issue_date")
                target_bid_closing_date = extracted_data.get("target_bid_closing_date")
                
                # Validate and clean the extracted data
                if opportunity_name and (opportunity_name.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid opportunity_name: {opportunity_name}")
                    opportunity_name = None
                
                if contract_type and (contract_type.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid contract_type: {contract_type}")
                    contract_type = None
                
                if estimated_value and (estimated_value.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid estimated_value: {estimated_value}")
                    estimated_value = None
                
                if target_issue_date and (target_issue_date.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid target_issue_date: {target_issue_date}")
                    target_issue_date = None
                
                if target_bid_closing_date and (target_bid_closing_date.lower() in ["null", "none", "n/a", "not found"]):
                    logger.debug(f"    Filtered out invalid target_bid_closing_date: {target_bid_closing_date}")
                    target_bid_closing_date = None
                
                logger.info(f"    Extracted from {page_range}: name={bool(opportunity_name)}, contract_type={bool(contract_type)}, estimated_value={bool(estimated_value)}, target_issue_date={bool(target_issue_date)}, target_bid_closing_date={bool(target_bid_closing_date)}")
                
                return opportunity_name, contract_type, estimated_value, target_issue_date, target_bid_closing_date
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Groq JSON response for {page_range}: {e}")
                logger.error(f"Response content: {response_content[:500]}")
                return None, None, None, None, None
                
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
            return None, None, None, None, None

