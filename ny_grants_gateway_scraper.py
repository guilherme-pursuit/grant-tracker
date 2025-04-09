import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import logging
import time
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# NY State Grants Gateway URLs - multiple URLs to try in case the main one is down or has moved
NY_GRANTS_GATEWAY_URLS = [
    "https://grantsmanagement.ny.gov/opportunities",
    "https://grantsgateway.ny.gov/IntelliGrants_NYSGG/module/nysgg/goportal.aspx",
    "https://www.grants.ny.gov/portal/",
    "https://apps.cio.ny.gov/apps/cfa/",
    "https://regional-institute.buffalo.edu/nys-funding-opportunities/"
]

def fetch_ny_grants_gateway_opportunities():
    """
    Scrape grant opportunities from the New York State Grants Gateway website.
    Returns a DataFrame of relevant opportunities.
    """
    logging.info("Fetching grant opportunities from NY State Grants Gateway...")
    
    try:
        # Headers for requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive"
        }
        
        # Try each URL in the list
        response = None
        used_url = None
        
        for url in NY_GRANTS_GATEWAY_URLS:
            try:
                logging.info(f"Trying NY Grants URL: {url}")
                temp_response = requests.get(url, headers=headers, timeout=15)
                
                if temp_response.status_code == 200:
                    logging.info(f"Successfully connected to {url}")
                    response = temp_response
                    used_url = url
                    break
                else:
                    logging.warning(f"Failed to fetch from {url}: {temp_response.status_code}")
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request error when trying {url}: {str(e)}")
                continue
        
        # If all URLs failed
        if not response:
            logging.error("All NY Grants Gateway URLs failed")
            return create_empty_grants_df()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing grant opportunities
        opportunities = []
        grant_elements = []
        
        # Try different possible structures based on the URL we successfully accessed
        logging.info(f"Parsing content from {used_url}")
        
        # First try common class-based selectors
        selectors_to_try = [
            "div.views-row",
            "div.opportunity-item",
            "tr.opportunity-row",
            "tr.grant-listing",
            "div.grant-opportunity",
            "div.funding-item",
            "article.node--type-grant",
            "li.grant-item",
            "div.card"
        ]
        
        for selector in selectors_to_try:
            element_type, element_class = selector.split('.')
            elements = soup.find_all(element_type, class_=element_class)
            if elements:
                logging.info(f"Found {len(elements)} grant elements using selector: {selector}")
                grant_elements = elements
                break
        
        # If class-based selectors fail, try more generic approaches
        if not grant_elements:
            logging.warning("No elements found with class-based selectors. Trying more generic selectors.")
            
            # Look for tables that might contain grant data
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                if len(rows) > 1:  # Header + at least one data row
                    grant_elements = rows[1:]  # Skip header row
                    logging.info(f"Found potential grant data in table with {len(grant_elements)} rows")
                    break
        
        # If still no results, look for any divs or lists with titles that might be grants
        if not grant_elements:
            # Look for any divs with titles or headings
            for heading_tag in ["h2", "h3", "h4"]:
                headings = soup.find_all(heading_tag)
                if headings:
                    for heading in headings:
                        parent = heading.parent
                        if parent and parent.name in ["div", "article", "section", "li"]:
                            grant_elements.append(parent)
            
            if grant_elements:
                logging.info(f"Found {len(grant_elements)} potential grant elements from headings")
        
        # Process the found elements
        for grant_element in grant_elements:
            try:
                # Extract title - try multiple potential selectors
                title_element = (
                    grant_element.find("span", class_="field-content") or 
                    grant_element.find("h2") or
                    grant_element.find("h3") or
                    grant_element.find("h4") or
                    grant_element.find("a") or
                    grant_element.find("td", class_="title") or
                    grant_element.find("div", class_="title")
                )
                
                # If no specific title element found, use the element text itself if it's short enough
                if not title_element and len(grant_element.get_text(strip=True)) < 200:
                    title = grant_element.get_text(strip=True)
                elif title_element:
                    title = title_element.get_text(strip=True)
                else:
                    # No title found, skip this element
                    continue
                
                # Extract link
                link_element = (
                    grant_element.find("a") or
                    (title_element.find("a") if title_element and title_element.name != "a" else title_element)
                )
                
                link = ""
                if link_element and "href" in link_element.attrs:
                    link = link_element["href"]
                    # Fix relative URLs
                    if link and not link.startswith("http"):
                        if link.startswith("/"):
                            # Extract domain from used_url 
                            domain_match = re.match(r"https?://[^/]+", used_url)
                            domain = domain_match.group(0) if domain_match else "https://grantsmanagement.ny.gov"
                            link = f"{domain}{link}"
                        else:
                            # Assume it's relative to the current URL
                            link = f"{used_url.rstrip('/')}/{link.lstrip('/')}"
                
                # Extract other information
                info_elements = grant_element.find_all("div", class_="views-field") or grant_element.find_all("div", class_="field")
                
                grant_info = {
                    "Title": title,
                    "Link": link,
                    "Funder": "New York State",
                    "Source": "NY Grants Gateway",
                    "Description": "No description available.",
                    "Eligibility": "Contact New York State Grants Gateway for eligibility information."
                }
                
                for info in info_elements:
                    label = info.find("div", class_="views-label") or info.find("label") or info.find("strong")
                    if not label:
                        continue
                    
                    label_text = label.get_text(strip=True).replace(":", "")
                    value_element = info.find("div", class_="field-content") or info.find("span") or info
                    value = value_element.get_text(strip=True).replace(label_text, "") if value_element else ""
                    
                    if "Funding" in label_text or "Award" in label_text or "Amount" in label_text:
                        grant_info["Award Amount"] = parse_amount(value)
                    elif "Deadline" in label_text or "Due Date" in label_text or "Close" in label_text:
                        grant_info["Deadline"] = parse_date(value)
                    elif "Description" in label_text or "Summary" in label_text or "Overview" in label_text:
                        grant_info["Description"] = value
                    elif "Eligible" in label_text or "Eligibility" in label_text:
                        grant_info["Eligibility"] = value
                    elif "Issued" in label_text or "Posted" in label_text or "Start" in label_text or "Open" in label_text:
                        grant_info["Start Date"] = parse_date(value)
                    elif "Agency" in label_text or "Department" in label_text or "Issuer" in label_text:
                        grant_info["Funder"] = value
                
                opportunities.append(grant_info)
                
            except Exception as e:
                logging.warning(f"Error parsing grant element: {str(e)}")
        
        # Convert to DataFrame
        if not opportunities:
            logging.warning("No grant opportunities found on NY Grants Gateway")
            return create_empty_grants_df()
            
        df = pd.DataFrame(opportunities)
        
        # Ensure required columns exist
        required_columns = ["Title", "Funder", "Description", "Deadline", "Award Amount", "Eligibility", "Link", "Source"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        logging.info(f"Successfully scraped {len(df)} grant opportunities from NY Grants Gateway")
        return df
        
    except Exception as e:
        logging.error(f"Error in fetch_ny_grants_gateway_opportunities: {str(e)}")
        return create_empty_grants_df()


def create_empty_grants_df():
    """Create an empty DataFrame with the proper grant structure."""
    df = pd.DataFrame(columns=[
        "Title", "Funder", "Description", "Deadline", "Award Amount", 
        "Eligibility", "Link", "Source", "Grant ID", "Start Date"
    ])
    return df


def parse_date(date_str):
    """Parse a date string into a datetime object."""
    if not date_str:
        return None
    
    try:
        # Try common date formats
        for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"]:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try to extract date with regex
        date_pattern = r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})"
        match = re.search(date_pattern, date_str)
        if match:
            month, day, year = match.groups()
            if len(year) == 2:
                year = f"20{year}"
            return datetime.datetime(int(year), int(month), int(day))
        
        return None
    except:
        return None


def parse_amount(amount_str):
    """Parse a monetary amount from a string."""
    if not amount_str:
        return None
    
    try:
        # Remove non-numeric characters except for decimal points
        amount_str = re.sub(r'[^\d.]', '', amount_str)
        return float(amount_str) if amount_str else None
    except:
        return None
