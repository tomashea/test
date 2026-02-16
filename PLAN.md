# Plan: Scraping Bilateral Investment Treaties from UNCTAD IIA Navigator

## Objective

Collect data on all bilateral investment treaties (BITs) and treaties with investment provisions (TIPs) for every country listed on the UNCTAD Investment Policy Hub IIA Navigator. For each treaty, capture:

- **Short title** (e.g., "Afghanistan - Germany BIT (2005)")
- **Treaty type** (BIT or TIP)
- **Status** (In force / Signed but not in force / Terminated)
- **Parties** (the two countries involved)
- **Date of signature**
- **Date of entry into force**
- **Termination date** (for terminated treaties)
- **Termination type** (for terminated treaties — e.g., unilateral denunciation, mutual consent, replacement by new treaty)

## Website Structure

**Base URL:** `https://investmentpolicy.unctad.org/international-investment-agreements/countries/{id}/{slug}`

- Country IDs are sequential integers starting at 1 (Afghanistan) through ~237+ (European Union).
- Some IDs may be gaps (no country assigned).
- Each country page lists all treaties in a table.
- The site uses JavaScript to dynamically render content, so a **headless browser is required** (simple HTTP requests return 403 or incomplete HTML).
- No official API exists; data must be scraped from the rendered HTML.

### Table columns per country page (9 fields):

| # | Column | Notes |
|---|--------|-------|
| 1 | Treaty link/URL | Relative path to treaty detail page |
| 2 | Short title | e.g., "Afghanistan - Germany BIT (2005)" |
| 3 | Type | "BITs" or "TIPs" |
| 4 | Status | "In force", "Signed (not in force)", "Terminated" |
| 5 | Parties | Comma-separated country names |
| 6 | Date of signature | DD/MM/YYYY format |
| 7 | Date of entry into force | DD/MM/YYYY or empty |
| 8 | Termination date | DD/MM/YYYY or empty |
| 9 | Full text availability | Language codes |

**Termination type** is NOT shown in the country-level table. It must be obtained from the individual **treaty detail page** (e.g., `/international-investment-agreements/treaties/bit/{id}/{slug}`).

## Architecture

```
scrape_bits.py          # Main script
requirements.txt        # Dependencies
data/
  treaties_raw.csv      # Full output with all fields
  treaties_by_country/  # Optional: per-country JSON files
```

## Implementation Plan

### Step 1: Discover all country IDs and slugs

**Approach A (preferred):** Navigate to the IIA main page or use the country dropdown on any country page to extract the full list of `(id, slug)` pairs. The dropdown `<select>` element contains all countries with their IDs embedded in option values or data attributes.

**Approach B (fallback):** Iterate IDs 1–250, attempt to load each page, and skip 404s.

### Step 2: For each country, scrape the treaty table

1. Navigate to `https://investmentpolicy.unctad.org/international-investment-agreements/countries/{id}/{slug}`
2. Wait for the treaty table to render (JavaScript-dependent)
3. Parse all rows from the table
4. Extract the 9 fields listed above
5. De-duplicate treaties (each treaty appears on both partner countries' pages)

### Step 3: For terminated treaties, scrape termination type from detail pages

1. Collect all unique treaty URLs where `status == "Terminated"`
2. Navigate to each treaty detail page
3. Extract the "Termination type" field from the metadata section
4. Join back to the main dataset

### Step 4: Clean and export data

1. Parse dates from DD/MM/YYYY to ISO 8601 (YYYY-MM-DD)
2. De-duplicate (each treaty appears under both partner countries)
3. Export to CSV

## Technology Choice: Playwright (Python)

**Why Playwright over Selenium:**
- Modern async API, faster execution
- Built-in auto-wait for elements
- Better handling of dynamic content
- Headless by default, lighter footprint

**Dependencies:**
```
playwright
pandas
```

### Script Pseudocode

```python
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import csv, json, time, re

BASE = "https://investmentpolicy.unctad.org/international-investment-agreements"

async def get_country_list(page):
    """Navigate to any country page and extract all (id, slug, name) from dropdown."""
    await page.goto(f"{BASE}/countries/1/afghanistan")
    # Extract options from the country selector dropdown
    # Return list of dicts: [{id: 1, slug: "afghanistan", name: "Afghanistan"}, ...]

async def scrape_country_treaties(page, country_id, slug):
    """Navigate to a country page and extract all treaty rows."""
    url = f"{BASE}/countries/{country_id}/{slug}"
    await page.goto(url)
    # Wait for table to render
    # Parse each row → extract 9 fields
    # Return list of treaty dicts

async def scrape_treaty_detail(page, treaty_url):
    """For terminated treaties, get termination type from detail page."""
    await page.goto(f"https://investmentpolicy.unctad.org{treaty_url}")
    # Extract termination type from metadata
    # Return termination_type string

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Step 1: Get country list
        countries = await get_country_list(page)

        # Step 2: Scrape all country pages
        all_treaties = []
        for country in countries:
            treaties = await scrape_country_treaties(page, country["id"], country["slug"])
            all_treaties.extend(treaties)
            time.sleep(0.5)  # Be respectful

        # Step 3: De-duplicate
        unique_treaties = deduplicate(all_treaties)

        # Step 4: Get termination types for terminated treaties
        terminated = [t for t in unique_treaties if t["status"] == "Terminated"]
        for treaty in terminated:
            treaty["termination_type"] = await scrape_treaty_detail(page, treaty["url"])
            time.sleep(0.3)

        # Step 5: Export
        df = pd.DataFrame(unique_treaties)
        df.to_csv("data/treaties_raw.csv", index=False)

        await browser.close()

asyncio.run(main())
```

## Rate Limiting and Politeness

- **0.5-second delay** between country page requests
- **0.3-second delay** between treaty detail page requests
- Respect `robots.txt` if it disallows scraping
- Use a single browser instance (not parallel) to avoid overloading the server
- Add retry logic with exponential backoff for transient failures

## Scale Estimate

- ~230 countries × 1 page each = ~230 country page requests
- ~3,300 total unique treaties (after dedup)
- ~800–1,000 terminated treaties needing detail page visits
- **Total requests: ~1,200–1,500**
- At 0.5s delay: ~10–15 minutes for country pages, ~5–8 minutes for detail pages

## Edge Cases to Handle

1. **Countries with zero treaties** — skip gracefully
2. **Empty date fields** — store as null/empty
3. **Non-standard date formats** — fallback parsing
4. **Pagination** — evidence suggests all treaties load on one page, but check for "load more" buttons
5. **Network errors** — retry with exponential backoff (3 retries max)
6. **Duplicate treaties** — each BIT appears on both countries' pages; deduplicate by treaty URL or short title
7. **Supranational entities** — EU (ID 237) and possibly others have TIPs but not BITs

## Output Schema (CSV)

| Column | Type | Example |
|--------|------|---------|
| treaty_url | string | /international-investment-agreements/treaties/bit/1/... |
| short_title | string | Afghanistan - Germany BIT (2005) |
| treaty_type | string | BIT |
| status | string | In force |
| party_1 | string | Afghanistan |
| party_2 | string | Germany |
| date_of_signature | date | 2005-04-20 |
| date_of_entry_into_force | date | 2007-10-12 |
| date_of_termination | date | (null if not terminated) |
| termination_type | string | (null if not terminated) |
