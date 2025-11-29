# ACT IFIB Updater Implementation Plan

## Overview
This plan outlines the implementation of an incremental updater for ACT IFIB opportunities that handles new opportunities, URL changes (amendments), and automatic deactivation of past-due opportunities.

## Requirements Summary

### Phase 2 Reconciliation Logic
- **New**: URLs on website but not in DB (by opportunity_code) → process
- **Existing with URL change**: Same opportunity_code but URL has changed → update (this is an amendment)
- **Removed**: URLs in DB but not on website → **keep** (don't mark inactive, just skip)

### Update Detection
- Compare URL endings only (opportunity code should be same, but URL end differs)
- Example: `ifib-act-sact-26-07/` vs `ifib-act-sact-26-07-amendment-1/`

### Removal Handling
- Mark opportunities as inactive based on rule: `bid_closing_date_parsed < current_datetime`
- This requires ensuring `bid_closing_date_parsed` is populated from `bid_closing_date` string

### Amendment Tracking
- Add field to track if amendments have occurred
- Track count of amendments

---

## Implementation Steps

### Step 1: Database Schema Changes

#### 1.1 Add Amendment Tracking Fields
**File**: `backend/models/opportunity.py`

Add new fields:
- `amendment_count` (Integer, default=0) - Count of how many amendments have occurred
- `has_amendments` (Boolean, default=False) - Whether any amendments have occurred
- `last_amendment_at` (DateTime, nullable=True) - When the last amendment was detected

**Migration**: Create new Alembic migration to add these columns

**Rationale**: 
- `amendment_count` tracks total amendments
- `has_amendments` provides quick boolean check
- `last_amendment_at` tracks when last amendment occurred

#### 1.2 Update URL Constraint
**Current**: `url` has unique constraint
**Change**: Remove unique constraint on `url` (since same opportunity_code can have different URLs due to amendments)

**Note**: `opportunity_code` already has unique constraint, which is what we'll use for matching

---

### Step 2: Create URL Comparison Utility

#### 2.1 Create URL Comparison Function
**File**: `backend/utils/url_comparison.py` (new file)

Function: `extract_url_ending(url: str) -> str`
- Extracts the last segment of URL (after last `/`)
- Example: `https://www.act.nato.int/opportunities/contracting/ifib-act-sact-26-07-amendment-1/` → `ifib-act-sact-26-07-amendment-1`
- Handles trailing slashes

Function: `urls_differ_by_ending(url1: str, url2: str) -> bool`
- Compares URL endings only
- Returns True if endings differ (indicating potential amendment)

**Rationale**: Isolates URL comparison logic for reuse and testing

---

### Step 3: Refactor Scraper Reconciliation Logic

#### 3.1 Modify `scrape_all()` Method
**File**: `backend/scraper/scraper.py`

**Current Flow**:
1. Get all links from website
2. Process each link individually (check by URL, update or create)

**New Flow**:
1. **Phase 1: Discovery** - Get all opportunity links from website (unchanged)
2. **Phase 2: Reconciliation** - Compare website opportunities with database:
   - Extract opportunity_code from each website URL
   - Query database by opportunity_code (not URL)
   - Categorize:
     - **New**: opportunity_code not in DB → add to process queue
     - **Existing with URL change**: opportunity_code exists but URL ending differs → add to process queue (amendment)
     - **Existing unchanged**: opportunity_code exists and URL ending same → skip (just update `last_checked_at`)
     - **Removed**: opportunity_code in DB but not on website → skip (keep in DB, don't mark inactive)
3. **Phase 3: Processing** - Process only opportunities in queue

#### 3.2 Create Reconciliation Method
**File**: `backend/scraper/scraper.py`

New method: `_reconcile_opportunities(website_links: List[Dict], db_session) -> Dict`
- Input: List of links from website, database session
- Output: Dictionary with keys:
  - `new`: List of links to process (new opportunities)
  - `amendments`: List of tuples (link, existing_opportunity) for URL changes
  - `unchanged`: List of existing opportunities (just update last_checked_at)
  - `removed`: List of opportunities in DB but not on website (for logging only)

**Logic**:
```python
# Extract opportunity_codes from website links
website_codes = {extract_code(link['url']): link for link in website_links}

# Get all existing opportunities for this nato_body and opportunity_type
existing = db.query(Opportunity).filter(
    Opportunity.nato_body == 'ACT',
    Opportunity.opportunity_type == 'IFIB'
).all()

existing_by_code = {opp.opportunity_code: opp for opp in existing}

# Categorize
for code, link in website_codes.items():
    if code not in existing_by_code:
        new.append(link)
    else:
        existing_opp = existing_by_code[code]
        if urls_differ_by_ending(link['url'], existing_opp.url):
            amendments.append((link, existing_opp))
        else:
            unchanged.append(existing_opp)

# Find removed (in DB but not on website)
for code, opp in existing_by_code.items():
    if code not in website_codes:
        removed.append(opp)
```

---

### Step 4: Update Processing Logic

#### 4.1 Modify Opportunity Save Logic
**File**: `backend/scraper/scraper.py`

**Current**: Check by URL, update or create

**New**: 
- For **new opportunities**: Create new record
- For **amendments**: 
  - Update all fields from new extraction
  - Increment `amendment_count`
  - Set `has_amendments = True`
  - Set `last_amendment_at = now()`
  - Update `last_changed_fields` to track what changed
  - Update `url` to new URL (old URL preserved in history if needed, or just overwrite)

**Amendment Detection Logic**:
```python
if existing_opportunity.url != new_url:
    # URL ending differs - this is an amendment
    existing_opportunity.amendment_count += 1
    existing_opportunity.has_amendments = True
    existing_opportunity.last_amendment_at = datetime.utcnow()
    # Track URL change in last_changed_fields
    changed_fields = existing_opportunity.last_changed_fields or []
    if 'url' not in changed_fields:
        changed_fields.append('url')
    existing_opportunity.last_changed_fields = changed_fields
```

#### 4.2 Update Unchanged Opportunities
**File**: `backend/scraper/scraper.py`

For opportunities that haven't changed:
- Just update `last_checked_at = datetime.utcnow()`
- Skip PDF download and extraction (performance optimization)

---

### Step 5: Auto-Deactivation Logic

#### 5.1 Create Auto-Deactivation Method
**File**: `backend/scraper/scraper.py`

New method: `_deactivate_past_due_opportunities(db_session) -> int`
- Query all active opportunities where `bid_closing_date_parsed < datetime.utcnow()`
- Set `is_active = False` for these opportunities
- Return count of deactivated opportunities
- Log deactivations

**Logic**:
```python
now = datetime.utcnow()
past_due = db.query(Opportunity).filter(
    Opportunity.is_active == True,
    Opportunity.bid_closing_date_parsed.isnot(None),
    Opportunity.bid_closing_date_parsed < now
).all()

for opp in past_due:
    opp.is_active = False
    logger.info(f"Auto-deactivated past-due opportunity: {opp.opportunity_code}")

db.commit()
return len(past_due)
```

#### 5.2 Ensure Date Parsing
**File**: `backend/scraper/scraper.py`

Ensure `parse_opportunity_dates()` is called for all opportunities (already done in `parse_opportunity_data()`)
- This populates `bid_closing_date_parsed` from `bid_closing_date` string
- If parsing fails, `bid_closing_date_parsed` remains None (opportunity won't be auto-deactivated)

#### 5.3 Call Auto-Deactivation
**File**: `backend/scraper/scraper.py`

Call `_deactivate_past_due_opportunities()` at the end of `scrape_all()`:
- After processing all opportunities
- Before final logging
- This ensures opportunities are deactivated even if they weren't found on website

---

### Step 6: Update Main Scrape Flow

#### 6.1 Refactor `scrape_all()` Method
**File**: `backend/scraper/scraper.py`

**New Structure**:
```python
async def scrape_all(self, mode: str = "incremental") -> Dict:
    """
    Scrape all IFIB opportunities.
    
    Args:
        mode: "full" (process all) or "incremental" (reconcile first)
    
    Returns:
        Dictionary with counts: new, updated, amendments, unchanged, deactivated
    """
    # Phase 1: Discovery
    links = await self.get_opportunity_links()
    
    if mode == "incremental":
        # Phase 2: Reconciliation
        db = get_db_session()
        try:
            reconciliation = self._reconcile_opportunities(links, db)
            
            # Phase 3: Processing
            # Process new opportunities
            # Process amendments
            # Update last_checked_at for unchanged
            
        finally:
            db.close()
    else:
        # Full mode: process all (current behavior)
        # ... existing logic ...
    
    # Auto-deactivate past-due opportunities
    db = get_db_session()
    try:
        deactivated_count = self._deactivate_past_due_opportunities(db)
    finally:
        db.close()
    
    return {
        'new': new_count,
        'amendments': amendment_count,
        'updated': updated_count,
        'unchanged': unchanged_count,
        'deactivated': deactivated_count
    }
```

---

### Step 7: Update Run Script

#### 7.1 Add Mode Parameter
**File**: `backend/scraper/run_scraper.py`

Add command-line argument or environment variable for mode:
- Default: `incremental`
- Option: `--mode full` for full scrape
- Option: `--mode incremental` for incremental update

---

### Step 8: Testing Considerations

#### 8.1 Test Cases to Consider
1. **New Opportunity**: Opportunity code not in DB → should create new
2. **Amendment**: Same code, different URL ending → should increment amendment_count
3. **Unchanged**: Same code, same URL ending → should skip processing, update last_checked_at
4. **Removed from Website**: In DB but not on website → should keep in DB, not mark inactive
5. **Past Due**: bid_closing_date_parsed < now → should set is_active = False
6. **Date Parsing**: Ensure bid_closing_date_parsed is populated correctly

#### 8.2 Edge Cases
- URL parsing fails (can't extract opportunity_code)
- Date parsing fails (bid_closing_date_parsed remains None)
- Multiple opportunities with same code (shouldn't happen due to unique constraint)
- URL ending comparison with/without trailing slashes

---

## File Changes Summary

### New Files
1. `backend/utils/url_comparison.py` - URL comparison utilities

### Modified Files
1. `backend/models/opportunity.py` - Add amendment tracking fields
2. `backend/scraper/scraper.py` - Refactor reconciliation and processing logic
3. `backend/scraper/run_scraper.py` - Add mode parameter
4. Database migration - Add amendment fields, remove URL unique constraint

### Unchanged Files (but used)
1. `backend/utils/date_parser.py` - Already handles date parsing
2. `backend/scraper/extractors/act_ifib_extractor.py` - Already extracts opportunity_code from URL

---

## Implementation Order

1. **Step 1**: Database schema changes (migration)
2. **Step 2**: URL comparison utility (foundation)
3. **Step 3**: Reconciliation method (core logic)
4. **Step 4**: Update processing logic (amendment detection)
5. **Step 5**: Auto-deactivation logic
6. **Step 6**: Refactor main scrape flow
7. **Step 7**: Update run script
8. **Step 8**: Testing

---

## Key Design Decisions

1. **Match by opportunity_code, not URL**: More robust for amendments
2. **Keep removed opportunities**: Don't delete, just skip (user requirement)
3. **URL ending comparison**: Simple heuristic for amendment detection
4. **Auto-deactivation separate**: Runs after processing, independent of website presence
5. **Incremental by default**: More efficient for regular runs
6. **Amendment count tracking**: Separate from general update_count

---

## Notes

- The `update_count` field already exists and tracks general updates
- `amendment_count` is specifically for URL changes (amendments)
- Both can increment independently (e.g., content update + URL change = both increment)
- Date parsing already happens via `parse_opportunity_dates()` - just need to ensure it's called
- URL unique constraint removal allows same opportunity_code with different URLs

