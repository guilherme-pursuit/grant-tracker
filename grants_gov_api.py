import requests
import pandas as pd
import datetime
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Grants.gov API URLs - Try multiple endpoints as the API structure might change
# If one endpoint fails, we'll try the others
GRANTS_GOV_API_ENDPOINTS = [
    "https://www.grants.gov/grantsws/rest/opportunities/search/",
    "https://www.grants.gov/grantsws/rest/search/opportunities/",
    "https://www.grants.gov/grantsws/rest/opportunities/", 
    "https://www.grants.gov/rest/opportunities/search/"
]

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
    Fetch grant opportunities from Grants.gov using multiple possible API endpoints.
    Returns a DataFrame of relevant opportunities.
    """
    logging.info("Fetching grant opportunities from Grants.gov...")
    
    all_results = []
    
    try:
        # For each keyword, perform a search
        for keyword in PURSUIT_KEYWORDS:
            logging.info(f"Searching for keyword: {keyword}")
            
            # Base search parameters - try different formats for the API
            params_options = [
                # Standard JSON format
                {
                    "keyword": keyword,
                    "oppStatuses": "forecasted,posted",
                    "sortBy": "openDate|desc",
                    "rows": 100
                },
                # Alternative format with different parameter names
                {
                    "searchText": keyword,
                    "status": "forecasted,posted",
                    "sort": "openDate|desc",
                    "maxResults": 100
                }
            ]
            
            # Try different headers
            headers_options = [
                {"Content-Type": "application/json"},
                {"Content-Type": "application/json", "Accept": "application/json"},
                {"Content-Type": "application/json; charset=utf-8"}
            ]
            
            # Keep track if we had success with any endpoint
            endpoint_success = False
            
            # Try each endpoint until one succeeds
            for endpoint in GRANTS_GOV_API_ENDPOINTS:
                if endpoint_success:
                    break
                    
                # Try each parameter format
                for params in params_options:
                    if endpoint_success:
                        break
                        
                    # Try each header format
                    for headers in headers_options:
                        try:
                            logging.info(f"Trying endpoint: {endpoint}")
                            
                            # Make API request
                            response = requests.post(
                                endpoint,
                                json=params,
                                headers=headers,
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                    
                                    # Different response formats to check
                                    if "oppHits" in data:
                                        opportunities = data["oppHits"]
                                        logging.info(f"Found {len(opportunities)} opportunities for keyword '{keyword}'")
                                        all_results.extend(opportunities)
                                        endpoint_success = True
                                        break
                                    elif "opportunities" in data:
                                        opportunities = data["opportunities"]
                                        logging.info(f"Found {len(opportunities)} opportunities for keyword '{keyword}'")
                                        all_results.extend(opportunities)
                                        endpoint_success = True
                                        break
                                    elif "searchHits" in data:
                                        opportunities = data["searchHits"]
                                        logging.info(f"Found {len(opportunities)} opportunities for keyword '{keyword}'")
                                        all_results.extend(opportunities)
                                        endpoint_success = True
                                        break
                                    else:
                                        # Try to find any array in the response
                                        for key, value in data.items():
                                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                                logging.info(f"Found {len(value)} opportunities in '{key}' for keyword '{keyword}'")
                                                all_results.extend(value)
                                                endpoint_success = True
                                                break
                                        
                                        if not endpoint_success:
                                            logging.warning(f"No opportunities found in response for keyword '{keyword}'")
                                except json.JSONDecodeError:
                                    logging.warning(f"Invalid JSON response from endpoint {endpoint}")
                            else:
                                logging.warning(f"Error response from endpoint {endpoint}: {response.status_code}")
                                
                        except requests.RequestException as e:
                            logging.warning(f"Request failed for endpoint {endpoint}: {str(e)}")
                
            # Rate limiting to avoid overwhelming the API
            time.sleep(1)
        
        # Handle empty results
        if not all_results:
            logging.warning("No grant opportunities found from Grants.gov")
            return pd.DataFrame()
            
        # Try to remove duplicates based on opportunity number
        try:
            # Check if all items in all_results have 'oppNum'
            if all("oppNum" in result for result in all_results):
                unique_results = {result["oppNum"]: result for result in all_results}.values()
            else:
                # If some don't have oppNum, find another common key to use as ID
                for possible_key in ["id", "opportunityId", "opportunityNumber", "number"]:
                    if all(possible_key in result for result in all_results):
                        unique_results = {result[possible_key]: result for result in all_results}.values()
                        break
                else:
                    # If no common ID field, just use the list as is
                    unique_results = all_results
        except (KeyError, TypeError) as e:
            # If there's an error with key access, just use the list as is
            logging.warning(f"Error deduplicating results: {str(e)}. Using full result set.")
            unique_results = all_results
        
        # Convert to DataFrame and extract relevant fields
        if not all_results:
            logging.warning("No grant opportunities found from Grants.gov")
            return pd.DataFrame()
            
        df = pd.DataFrame(list(unique_results))
        
        if df.empty:
            logging.warning("No grant opportunities found from Grants.gov after removing duplicates")
            return pd.DataFrame()
        
        # Select and rename relevant columns - try different field names that might be in the response
        possible_fields = {
            # Standard fields
            "oppNum": "Grant ID",
            "opportunityNumber": "Grant ID",
            "title": "Title",
            "opportunityTitle": "Title",
            "agency": "Funder",
            "agencyName": "Funder",
            "description": "Description",
            "opportunityDescription": "Description",
            "openDate": "Start Date",
            "postDate": "Start Date",
            "closeDate": "Deadline",
            "closeDate": "Deadline",
            "dueDate": "Deadline",
            "awardCeiling": "Award Amount",
            "awardAmount": "Award Amount",
            "opportunityCategory": "Category",
            "eligibleApplicants": "Eligibility",
            "eligibility": "Eligibility",
            "fundingActivityCategory": "Activity Category",
            "oppStatus": "Status",
            "status": "Status"
        }
        
        # Only keep columns that exist in the DataFrame
        columns_to_keep = {k: v for k, v in possible_fields.items() if k in df.columns}
        
        # If no matching columns found, try to identify any usable columns
        if not columns_to_keep:
            logging.warning("No standard column names found in API response. Attempting to auto-detect columns.")
            # Try to identify columns based on content patterns
            for col in df.columns:
                if 'id' in col.lower() or 'num' in col.lower():
                    columns_to_keep[col] = "Grant ID"
                elif 'title' in col.lower() or 'name' in col.lower():
                    columns_to_keep[col] = "Title"
                elif 'agency' in col.lower() or 'funder' in col.lower():
                    columns_to_keep[col] = "Funder"
                elif 'desc' in col.lower() or 'summary' in col.lower():
                    columns_to_keep[col] = "Description"
                elif 'date' in col.lower() and ('open' in col.lower() or 'start' in col.lower() or 'post' in col.lower()):
                    columns_to_keep[col] = "Start Date"
                elif 'date' in col.lower() and ('close' in col.lower() or 'end' in col.lower() or 'due' in col.lower()):
                    columns_to_keep[col] = "Deadline"
                elif 'award' in col.lower() or 'amount' in col.lower() or 'funding' in col.lower():
                    columns_to_keep[col] = "Award Amount"
                elif 'elig' in col.lower():
                    columns_to_keep[col] = "Eligibility"
        
        # We need at least Title and some identifier to proceed
        required_output_cols = ["Title", "Grant ID"]
        available_output_cols = set(columns_to_keep.values())
        
        if not all(col in available_output_cols for col in required_output_cols):
            # If we don't have the minimum required columns, create default ones
            if "Title" not in available_output_cols:
                # Use the first text column as Title if available
                for col in df.columns:
                    if df[col].dtype == 'object' and not all(df[col].isna()):
                        columns_to_keep[col] = "Title"
                        break
                else:
                    # If no suitable column found, use a placeholder
                    df["generated_title"] = "Grants.gov Opportunity"
                    columns_to_keep["generated_title"] = "Title"
            
            if "Grant ID" not in available_output_cols:
                # Create a unique ID for each row
                df["generated_id"] = [f"GRANTS-{i+1:04d}" for i in range(len(df))]
                columns_to_keep["generated_id"] = "Grant ID"
        
        grants_df = df[columns_to_keep.keys()].rename(columns=columns_to_keep)
        
        # Add source column
        grants_df["Source"] = "Grants.gov"
        
        # Add link column if possible
        if "Grant ID" in grants_df.columns:
            grants_df["Link"] = "https://www.grants.gov/web/grants/view-opportunity.html?oppId=" + grants_df["Grant ID"]
        else:
            grants_df["Link"] = "https://www.grants.gov"
            
        # Add Funder if missing
        if "Funder" not in grants_df.columns:
            grants_df["Funder"] = "Federal Government"
        
        # Convert date columns to datetime
        for date_col in ["Start Date", "Deadline"]:
            if date_col in grants_df.columns:
                grants_df[date_col] = pd.to_datetime(grants_df[date_col], errors='coerce')
        
        logging.info(f"Successfully processed {len(grants_df)} unique grant opportunities from Grants.gov")
        return grants_df
        
    except Exception as e:
        logging.error(f"Error in fetch_grants_gov_opportunities: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error
