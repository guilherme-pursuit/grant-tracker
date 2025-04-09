import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import logging
import time
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# NY State Grants Gateway URL
NY_GRANTS_GATEWAY_URL = "https://grantsmanagement.ny.gov/opportunities"

def fetch_ny_grants_gateway_opportunities():
    """
    Scrape grant opportunities from the New York State Grants Gateway website.
    Returns a DataFrame of relevant opportunities.
    """
    logging.info("Fetching grant opportunities from NY State Grants Gateway...")
    
    try:
        # Fetch the main opportunities page
        response = requests.get(NY_GRANTS_GATEWAY_URL, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch NY Grants Gateway page: {response.status_code}")
            return pd.DataFrame()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing grant opportunities
        opportunities = []
        
        # The structure of the page might vary, so we're looking for key elements
        # This is a simplified approach - actual implementation may need to be more robust
        grant_elements = soup.find_all("div", class_="views-row")
        
        for grant_element in grant_elements:
            try:
                # Extract title and link
                title_element = grant_element.find("span", class_="field-content")
                if not title_element:
                    continue
                
                title = title_element.get_text(strip=True)
                link_element = title_element.find("a")
                link = link_element["href"] if link_element else ""
                
                if link and not link.startswith("http"):
                    link = f"https://grantsmanagement.ny.gov{link}"
                
                # Extract other information
                info_elements = grant_element.find_all("div", class_="views-field")
                
                grant_info = {
                    "Title": title,
                    "Link": link,
                    "Funder": "New York State",
                    "Source": "NY Grants Gateway"
                }
                
                for info in info_elements:
                    label = info.find("div", class_="views-label")
                    if not label:
                        continue
                    
                    label_text = label.get_text(strip=True).replace(":", "")
                    value_element = info.find("div", class_="field-content")
                    value = value_element.get_text(strip=True) if value_element else ""
                    
                    if "Funding" in label_text or "Award" in label_text:
                        grant_info["Award Amount"] = parse_amount(value)
                    elif "Deadline" in label_text or "Due Date" in label_text:
                        grant_info["Deadline"] = parse_date(value)
                    elif "Description" in label_text:
                        grant_info["Description"] = value
                    elif "Eligible" in label_text or "Eligibility" in label_text:
                        grant_info["Eligibility"] = value
                    elif "Issued" in label_text or "Posted" in label_text:
                        grant_info["Start Date"] = parse_date(value)
                    elif "Agency" in label_text or "Department" in label_text:
                        grant_info["Funder"] = value
                
                opportunities.append(grant_info)
                
            except Exception as e:
                logging.warning(f"Error parsing grant element: {str(e)}")
        
        # Convert to DataFrame
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
        return pd.DataFrame()  # Return empty DataFrame on error


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
