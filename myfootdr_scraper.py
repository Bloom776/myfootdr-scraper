#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding="utf-8")

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from urllib.parse import urljoin, urlparse
import re

START_URL = "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/"
OUTPUT = "myfootdr_clinics.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
DEBUG_MODE = True
MAX_RETRIES = 3
BASE_DELAY = 2.0  # Increased delay to avoid rate limiting

def safe_text(el):
    return el.get_text(" ", strip=True) if el else ""

def fetch_soup(url, retry_count=0):
    """Fetch a page with retry logic and exponential backoff"""
    try:
        # Longer delay with jitter to avoid rate limiting
        delay = BASE_DELAY + random.uniform(0.5, 2.0) + (retry_count * 2)
        time.sleep(delay)
        
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"[!] HTTP {r.status_code} on {url}")
            return None
        return BeautifulSoup(r.text, "html.parser")
    except requests.exceptions.ConnectionError as e:
        if retry_count < MAX_RETRIES:
            wait_time = (retry_count + 1) * 10
            print(f"[!] Connection error, retrying in {wait_time}s... (attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return fetch_soup(url, retry_count + 1)
        else:
            print(f"[ERROR] Max retries exceeded for {url}: {e}")
            return None
    except Exception as e:
        print(f"[ERROR] fetching {url}: {e}")
        return None

def is_clinic_page(url):
    """Check if URL is likely an individual clinic page"""
    # Clinic pages typically have specific patterns
    path = urlparse(url).path
    # Exclude region pages and main clinic page
    if "/regions/" in path or path.endswith("/our-clinics/") or path == "/our-clinics":
        return False
    # Clinic pages are under /our-clinics/ with a specific name
    if "/our-clinics/" in path and path.count("/") >= 3:
        return True
    return False

def get_all_clinic_urls_from_page(url):
    """Extract all clinic URLs from any page"""
    soup = fetch_soup(url)
    if not soup:
        return []
    
    clinic_urls = set()
    
    # Find all links
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        
        # Build full URL
        full_url = urljoin(url, href)
        
        # Check if it's a clinic page
        if is_clinic_page(full_url) and "myfootdr.com.au/our-clinics/" in full_url:
            # Remove anchors
            clean_url = full_url.split("#")[0]
            clinic_urls.add(clean_url)
    
    return list(clinic_urls)

def scrape_clinic(url):
    """Scrape clinic info from individual clinic page"""
    soup = fetch_soup(url)
    if not soup:
        return None
    
    if DEBUG_MODE:
        print(f"\n{'='*60}")
        print(f"SCRAPING CLINIC: {url}")
        print(f"{'='*60}")
        print(f"Fetching page...")
    
    # Extract clinic name
    name = None
    # Strategy 1: h1 tags
    h1s = soup.find_all("h1")
    for h1 in h1s:
        text = safe_text(h1)
        # Prefer h1 that looks like a clinic name (contains "Foot" or "Podiatry")
        if text and any(word in text for word in ["My FootDr", "Foot", "Podiatry", "Clinic"]):
            name = text
            break
    
    # Fallback to first h1
    if not name and h1s:
        name = safe_text(h1s[0])
    
    # Last resort: title tag
    if not name:
        title = soup.find("title")
        if title:
            name = safe_text(title).split("|")[0].split("-")[0].strip()
    
    # Extract address - look for the cleanest address text
    address = None
    
    # Strategy 1: Look for specific address containers (smallest/most specific first)
    for elem in soup.find_all(["p", "span", "div", "address"]):
        classes = " ".join(elem.get("class", [])).lower()
        
        # Skip if it has child divs (means it's a container, not the address itself)
        if elem.find("div"):
            continue
            
        # Look for address-specific classes
        if "address" in classes and "meta" not in classes:
            text = safe_text(elem)
            # Should be relatively short and contain a postcode
            if text and len(text) < 200 and re.search(r"\b\d{4}\b", text):
                # Clean out common prefixes/suffixes and icons
                text = re.sub(r"^(Address|Location|i|v|V|U)[\s:]*", "", text, flags=re.I)
                text = re.sub(r"(Book online|Call|Get directions|with Google Maps).*$", "", text, flags=re.I)
                # Clean up multiple spaces and trim
                text = re.sub(r"\s+", " ", text).strip()
                if len(text) > 10:
                    address = text
                    break
    
    # Strategy 2: Use regex to find clean address pattern in full text
    if not address:
        all_text = soup.get_text()
        # Pattern: number + street + suburb + state + postcode
        address_pattern = r"(\d+[A-Za-z]?\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Parade|Way|Boulevard|Blvd|Court|Ct|Place|Pl|Crescent|Cres)\s+[A-Za-z\s]+(?:QLD|NSW|VIC|SA|WA|TAS|NT|ACT)\s+\d{4})"
        matches = re.findall(address_pattern, all_text, re.I)
        if matches:
            # Take first match and clean it
            address = re.sub(r"\s+", " ", matches[0].strip())
    
    # Extract email - clean extraction
    email = None
    
    # Strategy 1: Look for mailto links
    email_links = soup.find_all("a", href=re.compile(r"mailto:", re.I))
    for email_link in email_links:
        email_raw = email_link.get("href", "")
        # Remove archive.org wrapper if present
        if "web.archive.org" in email_raw:
            # Extract just the email from archived mailto link
            email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', email_raw)
            if email_match:
                email = email_match.group(1)
                break
        else:
            # Normal mailto link
            email_candidate = email_raw.replace("mailto:", "").split("?")[0].strip()
            if "@" in email_candidate and "." in email_candidate and len(email_candidate) > 5:
                email = email_candidate
                break
    
    # Strategy 2: If no mailto link, search for email patterns in text
    if not email:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        all_text = soup.get_text()
        email_matches = re.findall(email_pattern, all_text)
        # Filter out common non-email patterns
        for match in email_matches:
            if not any(skip in match.lower() for skip in ["example", "test", "noreply", "donotreply"]):
                email = match
                break
    
    # Extract phone - capture all phones, prioritize local numbers
    phone = None
    phone_links = soup.find_all("a", href=re.compile(r"^tel:", re.I))
    
    local_phones = []
    toll_free_phones = []
    
    for phone_link in phone_links:
        phone_raw = phone_link.get("href", "").replace("tel:", "").strip()
        # Clean up the phone number - keep only digits and basic formatting
        phone_clean = re.sub(r"[^\d\s\+\(\)\-]", "", phone_raw)
        phone_clean = re.sub(r"\s+", "", phone_clean)  # Remove all spaces
        
        if phone_clean and len(phone_clean) >= 10:
            # Separate local vs toll-free
            if phone_clean.startswith("1800") or phone_clean.startswith("1300"):
                toll_free_phones.append(phone_clean)
            else:
                local_phones.append(phone_clean)
    
    # Prefer local phone, but use toll-free if no local found
    if local_phones:
        phone = local_phones[0]
    elif toll_free_phones:
        phone = toll_free_phones[0]
    
    if DEBUG_MODE:
        print(f"  Found {len(phone_links)} phone links: {len(local_phones)} local, {len(toll_free_phones)} toll-free")
    
    # Extract services - get unique, clean service names
    services = []
    seen_services = set()
    
    # Strategy 1: Look for service lists with specific classes
    service_lists = soup.find_all("ul", class_=re.compile(r"service|treatment", re.I))
    for ul in service_lists:
        for li in ul.find_all("li", recursive=False):  # Only direct children
            service = safe_text(li)
            # Clean and validate
            service = re.sub(r"\s+", " ", service).strip()
            if service and 3 < len(service) < 150 and service.lower() not in seen_services:
                services.append(service)
                seen_services.add(service.lower())
    
    # Strategy 2: Look for lists after service headings
    if not services:
        for heading in soup.find_all(["h2", "h3", "h4", "strong"]):
            heading_text = safe_text(heading).lower()
            if any(word in heading_text for word in ["service", "treatment", "we offer", "what we treat", "specialt"]):
                # Find the next ul sibling
                next_ul = heading.find_next_sibling("ul")
                if not next_ul:
                    # Try looking in next few siblings
                    sibling = heading.next_sibling
                    for _ in range(5):
                        if not sibling:
                            break
                        if sibling.name == "ul":
                            next_ul = sibling
                            break
                        sibling = sibling.next_sibling
                
                if next_ul:
                    for li in next_ul.find_all("li", recursive=False):
                        service = safe_text(li)
                        service = re.sub(r"\s+", " ", service).strip()
                        if service and 3 < len(service) < 150 and service.lower() not in seen_services:
                            services.append(service)
                            seen_services.add(service.lower())
                    if services:  # Stop after first successful heading
                        break
    
    services_str = "; ".join(services[:20]) if services else "N/A"  # Limit to 20 services
    
    result = [
        name or "N/A",
        address or "N/A",
        email or "N/A",
        phone or "N/A",
        services_str
    ]
    
    if DEBUG_MODE:
        print(f"  Name: {result[0]}")
        print(f"  Address: {result[1][:80]}...")
        print(f"  Email: {result[2]}")
        print(f"  Phone: {result[3]}")
        print(f"  Services: {len(services)} found")
        if services:
            for i, s in enumerate(services[:3], 1):
                print(f"    {i}. {s}")
    
    return result

def main():
    print(f"[*] MyFootDr Clinic Scraper")
    print(f"[*] Target: {START_URL}")
    print(f"[*] Debug mode: {DEBUG_MODE}\n")
    
    # Step 1: Get all clinic URLs from main page
    print("[1/3] Discovering clinic URLs from main page...")
    main_page_clinics = get_all_clinic_urls_from_page(START_URL)
    print(f"      Found {len(main_page_clinics)} clinic URLs from main page")
    
    # Step 2: Check if there are region pages to explore
    print("\n[2/3] Checking for region pages...")
    soup = fetch_soup(START_URL)
    region_urls = set()
    
    if soup:
        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if href and "/regions/" in href and "myfootdr.com.au" in urljoin(START_URL, href):
                full_url = urljoin(START_URL, href)
                region_urls.add(full_url.split("#")[0])
    
    print(f"      Found {len(region_urls)} region pages")
    
    # Collect clinics from region pages
    all_clinic_urls = set(main_page_clinics)
    
    for i, region_url in enumerate(sorted(region_urls), 1):
        print(f"      Exploring region {i}/{len(region_urls)}: {region_url}")
        clinics = get_all_clinic_urls_from_page(region_url)
        print(f"        -> Found {len(clinics)} clinics")
        all_clinic_urls.update(clinics)
    
    all_clinic_urls = sorted(all_clinic_urls)
    print(f"\n[*] TOTAL unique clinic pages: {len(all_clinic_urls)}")
    
    if len(all_clinic_urls) == 0:
        print("[!] No clinic pages found. Check URL or site structure.")
        return
    
    # In debug mode, limit to first few
    if DEBUG_MODE:
        print(f"\n[!] DEBUG MODE: Scraping first 5 clinics only")
        print(f"[!] Set DEBUG_MODE=False to scrape all {len(all_clinic_urls)} clinics\n")
        all_clinic_urls = all_clinic_urls[:5]
    
    # Step 3: Scrape each clinic
    print(f"\n[3/3] Scraping clinic details...")
    
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name of Clinic", "Address", "Email", "Phone", "Services"])
        
        successful = 0
        failed = 0
        
        for i, url in enumerate(all_clinic_urls, start=1):
            print(f"\n[{i}/{len(all_clinic_urls)}] {url}")
            row = scrape_clinic(url)
            
            if row and row[0] != "N/A":
                writer.writerow(row)
                successful += 1
                print(f"      ✓ Success")
            else:
                failed += 1
                print(f"      ✗ Failed to extract data")
    
    print(f"\n{'='*60}")
    print(f"[DONE] Scraping complete!")
    print(f"       Successful: {successful}")
    print(f"       Failed: {failed}")
    print(f"       Output: {OUTPUT}")
    print(f"{'='*60}")
    
    if DEBUG_MODE:
        print(f"\n[!] To scrape all clinics, set DEBUG_MODE=False")

if __name__ == "__main__":
    main()