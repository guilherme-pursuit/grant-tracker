import requests
import pandas as pd
import datetime
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Grants.gov API base URL
# Note: This API URL might need to be updated as Grants.gov changes their API structure
GRANTS_GOV_API_BASE = "https://www.grants.gov/grantsws/rest/opportunities/search/"

# Keywords relevant to Pursuit's mission
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

def fetch_grants_gov_opportunities():
    """
    Fetch grant opportunities from Grants.gov using the search2 API.
    Returns a DataFrame of relevant opportunities.
    """
    logging.info("Fetching grant opportunities from Grants.gov...")
    
    all_results = []
    
    try:
        # For each keyword, perform a search
        for keyword in PURSUIT_KEYWORDS:
            logging.info(f"Searching for keyword: {keyword}")
            
            # Base search parameters
            params = {
                "keyword": keyword,
                "oppStatuses": "forecasted,posted",  # Active opportunities
                "sortBy": "openDate|desc",
                "rows": 100  # Maximum number of results per page
            }
            
            # Make API request
            response = requests.post(
                GRANTS_GOV_API_BASE,
                json=params,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "oppHits" in data:
                    opportunities = data["oppHits"]
                    logging.info(f"Found {len(opportunities)} opportunities for keyword '{keyword}'")
                    all_results.extend(opportunities)
                else:
                    logging.warning(f"No 'oppHits' found in response for keyword '{keyword}'")
            else:
                logging.error(f"Error fetching data from Grants.gov: {response.status_code} - {response.text}")
            
            # Rate limiting to avoid overwhelming the API
            time.sleep(1)
        
        # Remove duplicates based on opportunity number
        unique_results = {result["oppNum"]: result for result in all_results}.values()
        
        # Convert to DataFrame and extract relevant fields
        df = pd.DataFrame(list(unique_results))
        
        if df.empty:
            logging.warning("No grant opportunities found from Grants.gov")
            return pd.DataFrame()
        
        # Select and rename relevant columns
        relevant_columns = {
            "oppNum": "Grant ID",
            "title": "Title",
            "agency": "Funder",
            "description": "Description",
            "openDate": "Start Date",
            "closeDate": "Deadline",
            "awardCeiling": "Award Amount",
            "opportunityCategory": "Category",
            "eligibleApplicants": "Eligibility",
            "fundingActivityCategory": "Activity Category",
            "oppStatus": "Status"
        }
        
        # Only keep columns that exist in the DataFrame
        columns_to_keep = {k: v for k, v in relevant_columns.items() if k in df.columns}
        
        grants_df = df[columns_to_keep.keys()].rename(columns=columns_to_keep)
        
        # Add source and link columns
        grants_df["Source"] = "Grants.gov"
        grants_df["Link"] = "https://www.grants.gov/web/grants/view-opportunity.html?oppId=" + df["oppNum"]
        
        # Convert date columns to datetime
        for date_col in ["Start Date", "Deadline"]:
            if date_col in grants_df.columns:
                grants_df[date_col] = pd.to_datetime(grants_df[date_col], errors='coerce')
        
        logging.info(f"Successfully processed {len(grants_df)} unique grant opportunities from Grants.gov")
        return grants_df
        
    except Exception as e:
        logging.error(f"Error in fetch_grants_gov_opportunities: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error
