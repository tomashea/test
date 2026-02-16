"""
Scrape bilateral investment treaties (BITs) and treaties with investment
provisions (TIPs) from the UNCTAD IIA Navigator.

For each treaty the script collects:
  - short title, type (BIT / TIP), status, parties
  - date of signature, date of entry into force
  - date of termination  (terminated treaties only)
  - termination type      (terminated treaties only, from detail page)

Usage:
    pip install playwright pandas
    playwright install chromium
    python scrape_bits.py [--max-countries N] [--output FILE] [--resume]
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PwTimeout

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://investmentpolicy.unctad.org"
IIA_BASE = f"{BASE_URL}/international-investment-agreements"
COUNTRY_URL = f"{IIA_BASE}/countries"

DELAY_COUNTRY = 1.0        # seconds between country page loads
DELAY_DETAIL = 0.5         # seconds between treaty detail page loads
PAGE_TIMEOUT = 60_000      # ms – max wait for page navigation
SELECTOR_TIMEOUT = 30_000  # ms – max wait for an element to appear
MAX_RETRIES = 3

DATA_DIR = Path("data")
CHECKPOINT_FILE = DATA_DIR / "checkpoint.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_date(raw: str) -> str:
    """Convert DD/MM/YYYY → YYYY-MM-DD.  Return empty string on failure."""
    raw = raw.strip()
    if not raw:
        return ""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    return raw  # return as-is if format is unexpected


def split_parties(parties_str: str) -> tuple[str, str]:
    """Split 'Country A, Country B' into two parts.

    Handles edge cases like 'Korea, Republic of, Germany' by splitting
    on the last comma that is followed by a space and a capital letter
    which starts a new country name.
    """
    parties_str = parties_str.strip()
    # Try simple split first (most common case: exactly one comma separator)
    parts = [p.strip() for p in parties_str.split(",")]
    if len(parts) == 2:
        return parts[0], parts[1]

    # For cases with commas inside country names (e.g. "Korea, Republic of"),
    # find the separating comma: it's between two country names that both
    # appear in the original string.  Heuristic: try every comma position.
    for i in range(1, len(parts)):
        left = ", ".join(parts[:i]).strip()
        right = ", ".join(parts[i:]).strip()
        if left and right:
            # Keep trying – prefer the split where right starts with uppercase
            if right[0].isupper():
                candidate = (left, right)
    # Fallback: split at the midpoint comma
    try:
        return candidate  # type: ignore[possibly-undefined]
    except NameError:
        return parties_str, ""


async def retry_goto(page, url: str, retries: int = MAX_RETRIES):
    """Navigate to *url* with retries and exponential backoff."""
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            return
        except Exception as exc:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            log.warning("Navigation to %s failed (%s), retry in %ds…", url, exc, wait)
            await asyncio.sleep(wait)


# ---------------------------------------------------------------------------
# Step 1 – Discover countries
# ---------------------------------------------------------------------------

async def get_country_list(page) -> list[dict]:
    """Return a list of dicts: {id, slug, name} for every country/economy."""
    log.info("Discovering country list …")
    await retry_goto(page, f"{COUNTRY_URL}/1/afghanistan")

    # The country selector is typically a <select> or a list of <a> links
    # in a sidebar / dropdown.  We try multiple strategies.

    countries: list[dict] = []

    # Strategy 1: look for a <select> element whose options link to country pages.
    selects = await page.query_selector_all("select")
    for sel in selects:
        options = await sel.query_selector_all("option")
        for opt in options:
            value = (await opt.get_attribute("value")) or ""
            text = ((await opt.inner_text()) or "").strip()
            # value could be a full URL path or just an id
            m = re.search(r"/countries/(\d+)/([a-z0-9-]+)", value)
            if m:
                countries.append({"id": int(m.group(1)), "slug": m.group(2), "name": text})
    if countries:
        log.info("Strategy 1 (select/option) found %d countries", len(countries))
        return countries

    # Strategy 2: look for sidebar links matching /countries/{id}/{slug}
    links = await page.query_selector_all("a[href*='/countries/']")
    seen = set()
    for link in links:
        href = (await link.get_attribute("href")) or ""
        text = ((await link.inner_text()) or "").strip()
        m = re.search(r"/countries/(\d+)/([a-z0-9-]+)", href)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            countries.append({"id": int(m.group(1)), "slug": m.group(2), "name": text})
    if countries:
        log.info("Strategy 2 (sidebar links) found %d countries", len(countries))
        return countries

    # Strategy 3: brute-force IDs 1–250
    log.info("Falling back to brute-force country discovery (IDs 1–250) …")
    for cid in range(1, 251):
        test_url = f"{COUNTRY_URL}/{cid}/x"  # slug doesn't matter for redirect
        try:
            resp = await page.goto(test_url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            final_url = page.url
            m = re.search(r"/countries/(\d+)/([a-z0-9-]+)", final_url)
            if m and resp and resp.status < 400:
                name_el = await page.query_selector("h1, h2, .page-title")
                name = (await name_el.inner_text()).strip() if name_el else m.group(2)
                countries.append({"id": int(m.group(1)), "slug": m.group(2), "name": name})
                log.info("  found country id=%d  %s", cid, name)
        except Exception:
            pass  # skip non-existent IDs
        await asyncio.sleep(0.3)

    log.info("Brute-force discovery found %d countries", len(countries))
    return countries


# ---------------------------------------------------------------------------
# Step 2 – Scrape treaty table for one country
# ---------------------------------------------------------------------------

async def scrape_country_treaties(page, country: dict) -> list[dict]:
    """Navigate to a country's IIA page and extract every treaty row."""
    url = f"{COUNTRY_URL}/{country['id']}/{country['slug']}"
    await retry_goto(page, url)

    # Wait for the treaty table to appear
    try:
        await page.wait_for_selector(
            "table tbody tr", timeout=SELECTOR_TIMEOUT
        )
    except PwTimeout:
        log.warning("No treaty table found for %s (id=%d)", country["name"], country["id"])
        return []

    # --- extract rows --------------------------------------------------
    treaties: list[dict] = []

    rows = await page.query_selector_all("table tbody tr")
    for row in rows:
        cells = await row.query_selector_all("td")
        if len(cells) < 6:
            continue  # skip header / malformed rows

        # Try data-index attribute first (robust), fall back to position
        cell_map: dict[str, str] = {}
        for cell in cells:
            idx = await cell.get_attribute("data-index")
            text = ((await cell.inner_text()) or "").strip()
            if idx:
                cell_map[idx] = text

        # Extract treaty detail link from the row
        link_el = await row.query_selector("a[href*='/treaties/']")
        treaty_url = ""
        if link_el:
            treaty_url = (await link_el.get_attribute("href")) or ""

        if cell_map:
            # data-index based extraction
            treaty = {
                "treaty_url": treaty_url,
                "short_title": cell_map.get("2", cell_map.get("1", "")),
                "treaty_type": cell_map.get("3", cell_map.get("2", "")),
                "status": cell_map.get("4", cell_map.get("3", "")),
                "parties_raw": cell_map.get("5", cell_map.get("4", "")),
                "date_of_signature": cell_map.get("6", cell_map.get("5", "")),
                "date_of_entry_into_force": cell_map.get("7", cell_map.get("6", "")),
                "date_of_termination": cell_map.get("8", cell_map.get("7", "")),
            }
        else:
            # Positional fallback – typical order:
            # [#, title, type, status, parties, sign_date, entry_date, term_date, text]
            texts = []
            for cell in cells:
                texts.append(((await cell.inner_text()) or "").strip())
            treaty = {
                "treaty_url": treaty_url,
                "short_title": texts[1] if len(texts) > 1 else "",
                "treaty_type": texts[2] if len(texts) > 2 else "",
                "status": texts[3] if len(texts) > 3 else "",
                "parties_raw": texts[4] if len(texts) > 4 else "",
                "date_of_signature": texts[5] if len(texts) > 5 else "",
                "date_of_entry_into_force": texts[6] if len(texts) > 6 else "",
                "date_of_termination": texts[7] if len(texts) > 7 else "",
            }

        # Normalize type label
        ttype = treaty["treaty_type"].strip().lower()
        if "bit" in ttype:
            treaty["treaty_type"] = "BIT"
        elif ttype:
            treaty["treaty_type"] = "TIP"

        treaty["source_country_id"] = country["id"]
        treaty["source_country"] = country["name"]
        treaties.append(treaty)

    log.info(
        "  %s (id=%d): %d treaties", country["name"], country["id"], len(treaties)
    )
    return treaties


# ---------------------------------------------------------------------------
# Step 3 – Scrape termination type from treaty detail page
# ---------------------------------------------------------------------------

async def scrape_termination_type(page, treaty_url: str) -> str:
    """Visit a treaty detail page and extract the termination type."""
    full_url = treaty_url if treaty_url.startswith("http") else BASE_URL + treaty_url
    try:
        await retry_goto(page, full_url)
    except Exception as exc:
        log.warning("Could not load detail page %s: %s", full_url, exc)
        return ""

    # Metadata fields are in div.form-group elements with a <label> + value
    form_groups = await page.query_selector_all("div.form-group")
    for fg in form_groups:
        label_el = await fg.query_selector("label")
        if not label_el:
            continue
        label_text = ((await label_el.inner_text()) or "").strip().lower()
        if "termination" in label_text and "type" in label_text:
            # The value is the text content excluding the label
            full_text = ((await fg.inner_text()) or "").strip()
            label_raw = ((await label_el.inner_text()) or "").strip()
            value = full_text.replace(label_raw, "").strip()
            if value:
                return value

    # Fallback: look for any element containing "Type of termination" text
    try:
        el = await page.query_selector("text=/[Tt]ype of [Tt]ermination/")
        if el:
            parent = await el.evaluate_handle("el => el.closest('.form-group') || el.parentElement")
            text = await parent.evaluate("el => el.textContent")
            # Extract value after the label
            text = re.sub(r".*[Tt]ype of [Tt]ermination\s*:?\s*", "", text).strip()
            if text:
                return text
    except Exception:
        pass

    return ""


# ---------------------------------------------------------------------------
# Step 4 – De-duplicate
# ---------------------------------------------------------------------------

def deduplicate(treaties: list[dict]) -> list[dict]:
    """Remove duplicate treaties (each BIT appears on both countries' pages)."""
    seen: dict[str, dict] = {}
    for t in treaties:
        # Primary key: treaty URL (most reliable)
        key = t.get("treaty_url", "").strip()
        if not key:
            # Fallback key: normalized title
            key = t.get("short_title", "").strip().lower()
        if not key:
            continue
        if key not in seen:
            seen[key] = t
    return list(seen.values())


# ---------------------------------------------------------------------------
# Checkpointing helpers
# ---------------------------------------------------------------------------

def save_checkpoint(done_ids: list[int], treaties: list[dict]):
    """Persist progress so the script can resume after interruption."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"done_country_ids": done_ids, "treaty_count": len(treaties)}, f)
    # Also save raw treaties collected so far
    _write_csv(treaties, DATA_DIR / "treaties_partial.csv", dedupe=False)


def load_checkpoint() -> tuple[set[int], list[dict]]:
    """Load checkpoint if it exists. Returns (done_ids, treaties)."""
    if not CHECKPOINT_FILE.exists():
        return set(), []
    with open(CHECKPOINT_FILE) as f:
        ckpt = json.load(f)
    done = set(ckpt.get("done_country_ids", []))
    partial = DATA_DIR / "treaties_partial.csv"
    treaties: list[dict] = []
    if partial.exists():
        with open(partial, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                treaties.append(dict(row))
    log.info("Resumed from checkpoint: %d countries done, %d treaties", len(done), len(treaties))
    return done, treaties


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

COLUMNS = [
    "treaty_url",
    "short_title",
    "treaty_type",
    "status",
    "party_1",
    "party_2",
    "date_of_signature",
    "date_of_entry_into_force",
    "date_of_termination",
    "termination_type",
]


def _write_csv(treaties: list[dict], path: Path, dedupe: bool = True):
    """Write treaties to a CSV file."""
    data = deduplicate(treaties) if dedupe else treaties
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for t in data:
            writer.writerow(t)
    log.info("Wrote %d treaties to %s", len(data), path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Scrape UNCTAD IIA Navigator")
    parser.add_argument(
        "--max-countries", type=int, default=0,
        help="Limit to first N countries (0 = all, useful for testing)",
    )
    parser.add_argument(
        "--output", type=str, default="data/treaties.csv",
        help="Output CSV path (default: data/treaties.csv)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="Run browser in headed mode (visible window) for debugging",
    )
    args = parser.parse_args()
    output_path = Path(args.output)

    # Load checkpoint if resuming
    done_ids: set[int] = set()
    all_treaties: list[dict] = []
    if args.resume:
        done_ids, all_treaties = load_checkpoint()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.headed)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        # ── Step 1: discover countries ─────────────────────────────
        countries = await get_country_list(page)
        if not countries:
            log.error("Could not discover any countries – aborting.")
            await browser.close()
            sys.exit(1)

        log.info("Total countries discovered: %d", len(countries))

        if args.max_countries:
            countries = countries[: args.max_countries]
            log.info("Limited to first %d countries", args.max_countries)

        # ── Step 2: scrape treaty tables ───────────────────────────
        for i, country in enumerate(countries, 1):
            if country["id"] in done_ids:
                log.info("Skipping %s (id=%d) – already done", country["name"], country["id"])
                continue

            log.info("[%d/%d] Scraping %s …", i, len(countries), country["name"])
            try:
                treaties = await scrape_country_treaties(page, country)
                all_treaties.extend(treaties)
                done_ids.add(country["id"])
            except Exception as exc:
                log.error("Failed on %s (id=%d): %s", country["name"], country["id"], exc)

            # Checkpoint every 10 countries
            if len(done_ids) % 10 == 0:
                save_checkpoint(sorted(done_ids), all_treaties)

            await asyncio.sleep(DELAY_COUNTRY)

        # Save after all countries are done
        save_checkpoint(sorted(done_ids), all_treaties)

        # ── Step 3: de-duplicate ───────────────────────────────────
        unique = deduplicate(all_treaties)
        log.info(
            "De-duplicated: %d raw → %d unique treaties", len(all_treaties), len(unique)
        )

        # ── Step 4: parse parties and dates ────────────────────────
        for t in unique:
            p1, p2 = split_parties(t.get("parties_raw", ""))
            t["party_1"] = p1
            t["party_2"] = p2
            t["date_of_signature"] = parse_date(t.get("date_of_signature", ""))
            t["date_of_entry_into_force"] = parse_date(t.get("date_of_entry_into_force", ""))
            t["date_of_termination"] = parse_date(t.get("date_of_termination", ""))
            t.setdefault("termination_type", "")

        # ── Step 5: fetch termination types ────────────────────────
        terminated = [t for t in unique if "terminat" in t.get("status", "").lower()]
        log.info("Fetching termination type for %d terminated treaties …", len(terminated))

        for i, t in enumerate(terminated, 1):
            treaty_url = t.get("treaty_url", "")
            if not treaty_url:
                continue
            log.info("  [%d/%d] %s", i, len(terminated), t.get("short_title", "?"))
            t["termination_type"] = await scrape_termination_type(page, treaty_url)
            await asyncio.sleep(DELAY_DETAIL)

        # ── Step 6: export ─────────────────────────────────────────
        _write_csv(unique, output_path)

        # Also save as JSON for convenience
        json_path = output_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            export = [{k: t.get(k, "") for k in COLUMNS} for t in unique]
            json.dump(export, f, indent=2, ensure_ascii=False)
        log.info("Wrote JSON to %s", json_path)

        # Clean up checkpoint
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
        partial = DATA_DIR / "treaties_partial.csv"
        if partial.exists():
            partial.unlink()

        await browser.close()

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
