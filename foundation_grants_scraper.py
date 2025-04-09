import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import logging
import time
import re
import random
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URLs for foundation grant sources
FOUNDATION_GRANT_URLS = [
    "https://candid.org/find-funding",
    "https://www.grantwatch.com/cat/41/workforce-grants.html",
    "https://philanthropynewyork.org/rfps-member-updates",
    "https://www.macfound.org/grants",
    "https://www.fordfoundation.org/work/our-grants/",
    "https://www.rwjf.org/en/grants/funding-opportunities.html",
    "https://www.wkkf.org/grants"
]

# Keywords relevant to Pursuit's mission for filtering
PURSUIT_KEYWORDS = [
    "workforce development", 
    "tech training", 
    "software engineering", 
    "economic mobility",
    "adult education",
    "technology education",
    "job training",
    "career development",
    "low income",
    "underserved",
    "equity",
    "computer science",
    "coding"
]

def fetch_foundation_grants():
    """
    Scrape grant opportunities from foundation websites.
    Returns a DataFrame of relevant opportunities.
    """
    logging.info("Fetching grant opportunities from foundation sources...")
    
    all_opportunities = []
    successful_sources = []
    
    try:
        # Headers for requests to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Try each foundation URL
        for url in FOUNDATION_GRANT_URLS:
            try:
                logging.info(f"Trying foundation grants URL: {url}")
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    logging.warning(f"Failed to fetch from {url}: Status {response.status_code}")
                    continue
                    
                logging.info(f"Successfully connected to {url}")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract foundation name from URL
                foundation_name = url.split('/')[2].replace('www.', '').replace('.org', '').replace('.com', '')
                foundation_name = ' '.join(word.capitalize() for word in foundation_name.split('.'))
                
                # Extract grants based on common patterns
                grants_found = extract_grants_from_page(soup, url, foundation_name)
                
                if grants_found:
                    all_opportunities.extend(grants_found)
                    successful_sources.append(foundation_name)
                    logging.info(f"Found {len(grants_found)} potential grants from {foundation_name}")
                
                # Don't hammer servers with requests
                time.sleep(2)
                
            except Exception as e:
                logging.warning(f"Error processing {url}: {str(e)}")
                continue
        
        # Convert results to DataFrame
        if not all_opportunities:
            logging.warning("No foundation grant opportunities found")
            return pd.DataFrame()
            
        grants_df = pd.DataFrame(all_opportunities)
        
        # Ensure required columns exist
        required_columns = ["Title", "Funder", "Description", "Deadline", "Award Amount", "Eligibility", "Link", "Source"]
        for col in required_columns:
            if col not in grants_df.columns:
                grants_df[col] = None
                
        # Add Source column if not already present
        if "Source" not in grants_df.columns:
            grants_df["Source"] = "Foundation Grants"
        
        # Convert date columns to datetime
        for date_col in ["Start Date", "Deadline"]:
            if date_col in grants_df.columns:
                grants_df[date_col] = pd.to_datetime(grants_df[date_col], errors='coerce')
        
        logging.info(f"Successfully processed {len(grants_df)} foundation grant opportunities from {', '.join(successful_sources)}")
        return grants_df
        
    except Exception as e:
        logging.error(f"Error in fetch_foundation_grants: {str(e)}")
        return pd.DataFrame()

def extract_grants_from_page(soup, base_url, foundation_name):
    """
    Extract grant opportunities from a parsed HTML page.
    Uses various selectors to find grant information based on common foundation website patterns.
    """
    grants = []
    
    # Common CSS patterns for grant listings
    grant_container_selectors = [
        "div.grant-opportunity", "div.funding-opportunity", "div.grant", 
        "div.card", "div.opportunity", "div.program", "article", 
        "div.grant-listing", "li.grant-item", "div.rfp-item"
    ]
    
    # Try each selector to find grant containers
    containers = []
    for selector in grant_container_selectors:
        try:
            element_type, element_class = selector.split('.')
            elements = soup.find_all(element_type, class_=element_class)
            if elements:
                containers.extend(elements)
                logging.info(f"Found {len(elements)} grant elements using selector: {selector}")
        except Exception:
            continue
    
    # If no specific containers found, look for headings that might indicate grants
    if not containers:
        for heading_tag in ["h2", "h3", "h4", "h5"]:
            headings = soup.find_all(heading_tag)
            for heading in headings:
                # Check if heading text contains relevant keywords
                heading_text = heading.get_text(strip=True).lower()
                if any(keyword.lower() in heading_text for keyword in [
                    "grant", "funding", "opportunity", "award", "application", 
                    "program", "initiative", "rfp", "request for proposal"
                ]):
                    # Get parent container for this grant heading
                    parent = heading.parent
                    if parent and parent.name in ["div", "article", "section", "li"]:
                        containers.append(parent)
    
    # Process each container
    for container in containers:
        try:
            # Extract title
            title_element = (
                container.find("h2") or container.find("h3") or container.find("h4") or
                container.find("h5") or container.find("strong") or container.find("b") or
                container.find(class_=re.compile(r"title|heading|name", re.I))
            )
            
            if title_element:
                title = title_element.get_text(strip=True)
            else:
                # No clear title element, try to extract from first paragraph or similar
                title = next((
                    el.get_text(strip=True) for el in 
                    [container.find("p"), container.find("div")] 
                    if el and len(el.get_text(strip=True)) < 200
                ), "Untitled Grant Opportunity")
            
            # Skip if title is too generic
            if title.lower() in ["untitled", "grant", "opportunity", "program", "initiative"]:
                continue
                
            # Extract link
            link_element = container.find("a")
            link = ""
            if link_element and "href" in link_element.attrs:
                link = link_element["href"]
                # Fix relative URLs
                if link and not link.startswith(("http://", "https://")):
                    link = urljoin(base_url, link)
            else:
                # If no link found, use base URL
                link = base_url
            
            # Extract description
            description_element = (
                container.find("p") or 
                container.find(class_=re.compile(r"desc|summary|excerpt|content", re.I))
            )
            description = (
                description_element.get_text(strip=True) if description_element 
                else "No description available. Please visit the website for more information."
            )
            
            # Extract deadline if available
            deadline = None
            deadline_patterns = [
                r"deadline:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                r"due:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                r"close:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
                r"(\d{1,2}/\d{1,2}/\d{2,4})",
                r"(\d{4}-\d{1,2}-\d{1,2})"
            ]
            
            for pattern in deadline_patterns:
                deadline_match = re.search(pattern, container.get_text(), re.I)
                if deadline_match:
                    deadline_str = deadline_match.group(1)
                    try:
                        # Try multiple date formats
                        for fmt in ["%B %d, %Y", "%B %d %Y", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"]:
                            try:
                                deadline = datetime.datetime.strptime(deadline_str, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                    
                    if deadline:
                        break
            
            # Extract award amount if available
            award_amount = None
            amount_patterns = [
                r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                r"(\d{1,3}(?:,\d{3})*) dollars",
                r"award:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                r"grant:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                r"funding:?\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            ]
            
            for pattern in amount_patterns:
                amount_match = re.search(pattern, container.get_text(), re.I)
                if amount_match:
                    amount_str = amount_match.group(1)
                    try:
                        award_amount = float(amount_str.replace(",", ""))
                        break
                    except ValueError:
                        pass
            
            # Create grant record
            grant = {
                "Title": title,
                "Funder": foundation_name,
                "Description": description,
                "Deadline": deadline,
                "Award Amount": award_amount,
                "Eligibility": "Please check the foundation website for eligibility criteria.",
                "Link": link,
                "Source": "Foundation Grants",
                "Grant ID": f"FDN-{len(grants) + 1}"
            }
            
            # Check if grant is relevant to Pursuit's mission
            is_relevant = any(
                keyword.lower() in title.lower() or keyword.lower() in description.lower()
                for keyword in PURSUIT_KEYWORDS
            )
            
            if is_relevant:
                grants.append(grant)
                
        except Exception as e:
            logging.warning(f"Error extracting grant details: {str(e)}")
            continue
    
    return grants