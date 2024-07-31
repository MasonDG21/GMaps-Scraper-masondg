import os
import time
import random
import re
import csv
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from tqdm import tqdm
from dotenv import load_dotenv

# 2^31 - 1, which is the maximum value for a C long
csv.field_size_limit(2147483647)


filtered_domains = [
    "google.com", "yelp.com", "facebook.com", "squarespace.com",
    "yellowpages.com", "tripadvisor.com", "homedepot.com",
    "amazon.com","amazonaws.com", "walmart.com", "bing.com",
    "microsoft.com", "apple.com", "linkedin.com",
    "instagram.com", "twitter.com", "craigslist.org",
    "reddit.com", "tumblr.com", "pinterest.com",
    "quora.com", "ebay.com", "target.com",
    "bestbuy.com", "costco.com", "lowes.com",
    "macys.com", "kohls.com", "wayfair.com",
    "etsy.com", "overstock.com", "newegg.com",
    "zillow.com", "realtor.com", "bankofamerica.com",
    "chase.com", "wellsfargo.com", "usbank.com",
    "citi.com", "capitalone.com", "americanexpress.com",
    "hulu.com", "netflix.com", "disneyplus.com",
    "spotify.com", "pandora.com", "soundcloud.com",
    "dropbox.com", "box.com", "icloud.com",
    "adobe.com", "salesforce.com", "oracle.com",
    "ibm.com", "sap.com", "dell.com",
    "hp.com", "lenovo.com", "cisco.com",
    "verizon.com", "att.com", "t-mobile.com",
    "sprint.com", "vodafone.com", "honeywell.com",
    "ge.com", "siemens.com", "bosch.com",
    "philips.com", "samsung.com", "lg.com",
    "sony.com", "panasonic.com", "jpmorgan.com",
    "goldmansachs.com", "morganstanley.com", "deutschebank.com",
    "ubs.com", "barclays.com", "hsbc.com",
    "unilever.com", "nestle.com", "pepsico.com",
    "cocacola.com", "johnsonandjohnson.com", "pfizer.com",
    "merck.com", "glaxosmithkline.com", "novartis.com",
    "roche.com", "abbott.com", "bayer.com",
    "astrazeneca.com", "sanofi.com"
]

def deduplication():
    # Read existing emails and URLs from 'contact_log.csv' and return them as sets
    existing_entries = set()
    try:
        with open('contact_log.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_entries.add((row['email'], row['url']))
    except FileNotFoundError:
        pass
    return existing_entries

def google_search(driver, query, num_results, start=0):
    """Performs a Google search and returns a set of URLs from the search results."""
    search_url = f"https://www.google.com/search?q={query}&num={num_results}&start={start}"
    driver.get(search_url)
    urls = set()

    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g')))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        results = soup.select('div.g a')
        
        for result in results:
            url = result.get('href')
            if url and url.startswith('http'):
                if not any(domain in url for domain in filtered_domains):
                    urls.add(url)
        if not urls:
            print("No URLs found.")      
    except Exception as e:
        print(f"Error during Google search: {e}")
    return urls

def extract_contact_info(driver, url):
    """Extract email and contact info from the given URL."""
    # Filter URLs by file type and known unnecessary domains
    if any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.css', '.js', '.ico']):
        return {'email': None, 'url': url}

    if any(domain in url for domain in filtered_domains):
        return {'email': None, 'url': url}

    contact_info = {
        'email': None,
        'url': url
    }

    try:
        driver.get(url)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract text content from the page
        text_content = soup.get_text()
        
        # Find all email addresses
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
        emails = email_pattern.findall(text_content)
        
        if emails:
            contact_info['email'] = emails[0].strip()  # Take the first valid email
    except Exception as e:
        print(f"Error extracting contact info from {url}: {e}")

    return contact_info

def is_valid_email(email):
    """Validate the email format."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def write_to_csv(contact_infos):
    """Write contact info to a CSV file."""
    fieldnames = ['email', 'url']
    file_exists = os.path.isfile('contact_log.csv')
    existing_entries = deduplication()

    try:
        with open('contact_log.csv', 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()  # Write header only if file does not exist
            for info in contact_infos:
                if info['email'] and is_valid_email(info['email']):  # Only write rows where email is valid
                    if (info['email'], info['url']) not in existing_entries:
                        writer.writerow(info)
                        existing_entries.add((info['email'], info['url']))
    except Exception as e:
        print(f"Error writing to CSV: {e}")


def is_valid_email(email):
    """Validate the email format."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def send_emails(email_subject, email_body, recipients, sender_info):
    """Send emails using the provided sender info."""
    sender_email = sender_info.get('email')
    sender_password = sender_info.get('password')
    sender_type = sender_info.get('type')

    if not sender_email or not sender_password or not sender_type:
        print("Invalid sender information.")
        return

    for recipient in recipients:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = email_subject

        body = email_body
        msg.attach(MIMEText(body, 'plain'))

        try:
            if sender_type == 'Outlook':
                server = smtplib.SMTP('smtp.office365.com', 587)
            elif sender_type == 'Gmail':
                server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient, text)
            server.quit()
        except Exception as e:
            print(f"Error sending email to {recipient}: {e}")


def main(query, num_emails, email_subject, sender_info, update_dashboard):
    run_count = 0
    total_urls_scraped = 0
    total_emails_collected = 0
    total_emails_delivered = 0

    # Read the content of the email body file
    try:
        with open('message.txt', 'r') as file:
            email_body = file.read()
    except Exception as e:
        print(f"Error reading email body file: {e}")
        return

    existing_entries = deduplication()
    found_emails = set()
    contact_infos = []
    start = 0
    num_scrape_results = num_emails * 4
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver_path = 'chromedriver.exe'
    null_output = os.devnull
    service = Service(driver_path, log_path=null_output)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        while len(found_emails) < num_emails:
            urls = google_search(driver, query, num_scrape_results, start=start)
            if not urls:
                print("No URLs found. Exiting.")
                break
            else:
                for url in urls:
                    contact_info = extract_contact_info(driver, url)
                    if (contact_info['email'], contact_info['url']) not in existing_entries:
                        contact_infos.append(contact_info)
                        existing_entries.add((contact_info['email'], contact_info['url']))
                        total_urls_scraped += 1
                        if contact_info['email']:
                            found_emails.add(contact_info['email'])
                            total_emails_collected += 1
                            update_dashboard(num_emails, total_urls_scraped, total_emails_collected, total_emails_delivered)
                        if len(found_emails) >= num_emails:
                            break
                write_to_csv(contact_infos)
                contact_infos.clear()
                run_count += 1
                start = run_count * num_scrape_results

        driver.quit()
        print(f"\n[Scraping Complete].\nTotal emails found: {len(found_emails)}")
        print(f"\n[START Email Drip].\nSender Account: {sender_info['email']} ")

        for email in list(found_emails):
            send_emails(email_subject, email_body, [email], sender_info)
            total_emails_delivered += 1
            update_dashboard(num_emails, total_urls_scraped, total_emails_collected, total_emails_delivered)
        print("\nEmails Sent")
    except KeyError as e:
        print(f"KeyError: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise