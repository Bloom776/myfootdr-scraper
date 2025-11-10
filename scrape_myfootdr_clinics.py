#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding="utf-8")

import csv
import re

INPUT_FILE = "myfootdr_clinics.csv"
OUTPUT_FILE = "myfootdr_clinics_cleaned.csv"

def clean_address(address):
    """Clean address field"""
    if not address or address == "N/A":
        return address
    
    # Remove leading icons and prefixes
    address = re.sub(r'^[ivVU\s]+', '', address)
    
    # Remove "Shop" numbers with extra formatting
    address = re.sub(r'^\s*Shop\s+\d+[A-Z]?,?\s*', 'Shop ', address, flags=re.I)
    
    # Remove excessive whitespace and newlines
    address = re.sub(r'\s+', ' ', address)
    
    # Remove common suffixes
    address = re.sub(r'(Book online|Call|Get directions|with Google Maps).*$', '', address, flags=re.I)
    
    return address.strip()

def clean_email(email):
    """Clean email field"""
    if not email or email == "N/A":
        return email
    
    # Remove leading v, i, icons
    email = re.sub(r'^[ivVU\s\n]+', '', email)
    
    # Extract just the email using regex
    email_pattern = r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
    match = re.search(email_pattern, email)
    
    if match:
        return match.group(1).strip()
    
    return email.strip()

def clean_phone(phone):
    """Clean and standardize phone number"""
    if not phone or phone == "N/A":
        return phone
    
    # Remove "Call" prefix
    phone = re.sub(r'^Call\s+', '', phone, flags=re.I)
    
    # Remove all non-digit characters except + at the start
    if phone.startswith('+'):
        phone = '+' + re.sub(r'[^\d]', '', phone[1:])
    else:
        phone = re.sub(r'[^\d]', '', phone)
    
    # Format Australian numbers: 0X XXXX XXXX or 1800 XXX XXX
    if len(phone) == 10:
        if phone.startswith('1800') or phone.startswith('1300'):
            # Format: 1800 XXX XXX
            phone = f"{phone[:4]} {phone[4:7]} {phone[7:]}"
        else:
            # Format: 0X XXXX XXXX
            phone = f"{phone[:2]} {phone[2:6]} {phone[6:]}"
    elif len(phone) == 8:
        # Format: XXXX XXXX (local numbers)
        phone = f"{phone[:4]} {phone[4:]}"
    
    return phone.strip()

def clean_services(services):
    """Clean services field - convert newlines to semicolons"""
    if not services or services == "N/A":
        return services
    
    # Split by newlines
    service_list = services.split('\n')
    
    # Clean each service
    cleaned = []
    seen = set()
    
    for service in service_list:
        service = service.strip()
        
        # Skip empty or very short items
        if not service or len(service) < 3:
            continue
        
        # Skip duplicates (case-insensitive)
        if service.lower() in seen:
            continue
        
        seen.add(service.lower())
        cleaned.append(service)
    
    # Join with semicolons
    return '; '.join(cleaned)

def clean_name(name):
    """Clean clinic name"""
    if not name or name == "N/A":
        return name
    
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    
    # Remove quotes if present
    name = name.strip('"')
    
    return name.strip()

def main():
    print(f"[*] Cleaning CSV file: {INPUT_FILE}")
    
    # Read input file
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"[*] Found {len(rows)} rows")
    
    # Clean each row
    cleaned_rows = []
    seen_clinics = set()
    duplicates = 0
    
    for i, row in enumerate(rows, 1):
        # Clean each field
        name = clean_name(row.get('Name of Clinic', ''))
        address = clean_address(row.get('Address', ''))
        email = clean_email(row.get('Email', ''))
        phone = clean_phone(row.get('Phone', ''))
        services = clean_services(row.get('Services', ''))
        
        # Check for duplicates (same name + address)
        clinic_key = f"{name.lower()}|{address.lower()}"
        if clinic_key in seen_clinics:
            print(f"[!] Duplicate found: {name} - Skipping")
            duplicates += 1
            continue
        
        seen_clinics.add(clinic_key)
        
        cleaned_rows.append({
            'Name of Clinic': name,
            'Address': address,
            'Email': email,
            'Phone': phone,
            'Services': services
        })
        
        # Show progress
        if i % 20 == 0:
            print(f"    Processed {i}/{len(rows)} rows...")
    
    # Write cleaned file
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Name of Clinic', 'Address', 'Email', 'Phone', 'Services'])
        writer.writeheader()
        writer.writerows(cleaned_rows)
    
    print(f"\n[✓] Cleaning complete!")
    print(f"    Original rows: {len(rows)}")
    print(f"    Duplicates removed: {duplicates}")
    print(f"    Final rows: {len(cleaned_rows)}")
    print(f"    Output file: {OUTPUT_FILE}")
    
    # Show sample of cleaned data
    print(f"\n[*] Sample of cleaned data (first 3 rows):")
    for i, row in enumerate(cleaned_rows[:3], 1):
        print(f"\n  Row {i}:")
        print(f"    Name: {row['Name of Clinic']}")
        print(f"    Address: {row['Address'][:60]}...")
        print(f"    Email: {row['Email']}")
        print(f"    Phone: {row['Phone']}")
        print(f"    Services: {row['Services'][:80]}...")

if __name__ == "__main__":
    main()