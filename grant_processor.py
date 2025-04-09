import pandas as pd
import numpy as np
import re
from funder_data import FUNDER_CATEGORIES
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Keywords for tagging
GEOGRAPHY_KEYWORDS = {
    "NY": ["new york", "ny state", "nyc", "brooklyn", "bronx", "manhattan", "queens", "staten island"],
    "National": ["national", "united states", "nationwide", "all states", "u.s.", "us", "usa"]
}

TOPIC_KEYWORDS = {
    "Workforce": ["workforce", "job training", "employment", "career", "job skills", "vocational"],
    "Tech": ["tech", "technology", "software", "programming", "coding", "computer science", "digital", "it"],
    "Economic Mobility": ["economic mobility", "economic opportunity", "poverty reduction", "income", "financial", "economic development"]
}

AUDIENCE_KEYWORDS = {
    "Adults 24+": ["adult", "24+", "adult education", "adult learning", "mature", "working age"],
    "Low-income": ["low-income", "disadvantaged", "underserved", "poverty", "low income", "poor", "vulnerable", "equity", "equality", "marginalized"]
}

def process_grants(grants_df):
    """
    Process the raw grants DataFrame to standardize columns and formats.
    """
    logging.info("Processing grants data...")
    
    try:
        if grants_df.empty:
            logging.warning("Empty grants DataFrame provided to process_grants")
            return pd.DataFrame()
        
        # Create a copy to avoid modifying the original
        df = grants_df.copy()
        
        # Standardize column names
        std_columns = {
            "Grant ID": "Grant ID",
            "Title": "Title",
            "Funder": "Funder",
            "Description": "Description",
            "Start Date": "Start Date",
            "Deadline": "Deadline",
            "Award Amount": "Award Amount",
            "Eligibility": "Eligibility",
            "Link": "Link",
            "Source": "Source"
        }
        
        # Ensure all necessary columns exist
        for col in std_columns.values():
            if col not in df.columns:
                df[col] = None
        
        # Convert date columns to datetime
        for date_col in ["Start Date", "Deadline"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Convert award amount to numeric
        if "Award Amount" in df.columns:
            df["Award Amount"] = pd.to_numeric(df["Award Amount"], errors='coerce')
        
        # Fill missing values with appropriate defaults
        df["Description"] = df["Description"].fillna("No description provided.")
        df["Eligibility"] = df["Eligibility"].fillna("Eligibility information not available.")
        
        # Create a unique identifier if not present
        if "Grant ID" not in df.columns or df["Grant ID"].isna().any():
            # Generate IDs for rows with missing Grant ID
            mask = df["Grant ID"].isna() if "Grant ID" in df.columns else pd.Series(True, index=df.index)
            df.loc[mask, "Grant ID"] = [f"GRANT-{i}" for i in range(sum(mask))]
        
        logging.info(f"Processed {len(df)} grants successfully")
        return df
        
    except Exception as e:
        logging.error(f"Error in process_grants: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error


def tag_grants(grants_df):
    """
    Tag grants with geography, topic, audience, and funder type.
    """
    logging.info("Tagging grants...")
    
    try:
        if grants_df.empty:
            logging.warning("Empty grants DataFrame provided to tag_grants")
            return pd.DataFrame()
        
        # Create a copy to avoid modifying the original
        df = grants_df.copy()
        
        # Initialize tag columns
        df["Geography"] = "National"  # Default
        df["Topic"] = "Other"
        df["Audience"] = "Other"
        df["Funder Type"] = "Other"
        
        # Tag by geography
        for geo, keywords in GEOGRAPHY_KEYWORDS.items():
            pattern = "|".join(keywords)
            mask = df["Description"].str.lower().str.contains(pattern, na=False, regex=True)
            mask |= df["Title"].str.lower().str.contains(pattern, na=False, regex=True)
            if "Eligibility" in df.columns:
                mask |= df["Eligibility"].str.lower().str.contains(pattern, na=False, regex=True)
            df.loc[mask, "Geography"] = geo
        
        # Tag by topic
        for topic, keywords in TOPIC_KEYWORDS.items():
            pattern = "|".join(keywords)
            mask = df["Description"].str.lower().str.contains(pattern, na=False, regex=True)
            mask |= df["Title"].str.lower().str.contains(pattern, na=False, regex=True)
            df.loc[mask, "Topic"] = topic
        
        # Tag by audience
        for audience, keywords in AUDIENCE_KEYWORDS.items():
            pattern = "|".join(keywords)
            mask = df["Description"].str.lower().str.contains(pattern, na=False, regex=True)
            mask |= df["Title"].str.lower().str.contains(pattern, na=False, regex=True)
            if "Eligibility" in df.columns:
                mask |= df["Eligibility"].str.lower().str.contains(pattern, na=False, regex=True)
            df.loc[mask, "Audience"] = audience
        
        # Tag by funder type
        df["Funder Type"] = df["Funder"].apply(determine_funder_type)
        
        # For government sources, we can directly assign
        gov_sources = ["Grants.gov", "NY Grants Gateway"]
        df.loc[df["Source"].isin(gov_sources), "Funder Type"] = "Government"
        
        logging.info(f"Successfully tagged {len(df)} grants")
        return df
        
    except Exception as e:
        logging.error(f"Error in tag_grants: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error


def determine_funder_type(funder_name):
    """
    Determine the type of funder based on the funder name.
    """
    if not isinstance(funder_name, str):
        return "Other"
    
    funder_lower = funder_name.lower()
    
    # Check if it's a government entity
    gov_keywords = ["department", "agency", "administration", "bureau", "office of", "federal", "state of", "county", "city of"]
    for keyword in gov_keywords:
        if keyword in funder_lower:
            return "Government"
    
    # Check in our categorized funders
    for funder_type, funders in FUNDER_CATEGORIES.items():
        for known_funder in funders:
            if known_funder.lower() in funder_lower or funder_lower in known_funder.lower():
                return funder_type
    
    # Default to Other if no match found
    return "Other"
