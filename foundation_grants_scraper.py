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

# Major foundation websites
MAJOR_FOUNDATION_URLS = [
    "https://www.publicbenefitinnovationfund.org/",
    "https://www.fordfoundation.org/work/our-grants/",
    "https://www.macfound.org/grants",
    "https://www.rwjf.org/en/grants/funding-opportunities.html",
    "https://www.wkkf.org/grants",
    "https://www.gatesfoundation.org/about/how-we-work/grant-opportunities",
    "https://www.rockefellerfoundation.org/grants/",
    "https://www.hewlett.org/grants/",
    "https://www.carnegie.org/grants/",
    "https://www.opensocietyfoundations.org/grants",
    "https://www.kresge.org/our-work/grants-social-investments/",
    "https://www.irvine.org/grantmaking/",
    "https://www.kauffman.org/grants/",
    "https://sloan.org/grants/apply",
    "https://simonsfoundation.org/funding-opportunities/",
    "https://www.arnoldventures.org/grants",
    "https://www.robinhood.org/programs/",
    "https://www.aecf.org/work/grant-making/",
    "https://www.emcf.org/grantees/",
    "https://www.luminafoundation.org/grants-opportunities/",
    "https://www.surdna.org/grants/",
    "https://www.kff.org/grants/",
    "https://mmt.org/grants",
    "https://www.aspeninstitute.org/programs/",
    "https://www.joycefdn.org/grants",
    "https://www.schusterman.org/funding-opportunities",
    "https://www.hfpg.org/apply-for-funding",
    "https://www.mcknight.org/grant-opportunities/",
    "https://www.mcarthurfdn.org/funding-opportunities",
    "https://www.rbf.org/programs",
    "https://www.blueshieldcafoundation.org/grants",
]

# You can add more URLs here (corporate, community, etc.)
CORPORATE_FOUNDATION_URLS = []
GRANT_AGGREGATOR_URLS = []
COMMUNITY_FOUNDATION_URLS = []
ADDITIONAL_FOUNDATION_URLS = []

# Combine all URLs
FOUNDATION_GRANT_URLS = (
    MAJOR_FOUNDATION_URLS +
    CORPORATE_FOUNDATION_URLS +
    GRANT_AGGREGATOR_URLS +
    COMMUNITY_FOUNDATION_URLS +
    ADDITIONAL_FOUNDATION_URLS
)

# Dummy scraper for now
def fetch_foundation_grants():
    # This returns a sample DataFrame — replace with real scraping logic later
    return pd.DataFrame([
        {"Funder": "Example Foundation", "Title": "Example Grant", "Deadline": "2025-12-31", "Link": "https://example.org"}
    ])

if __name__ == "__main__":
    df = fetch_foundation_grants()
    print(f"\nTotal grants found: {len(df)}\n")
    print(
        df[["Funder", "Title", "Deadline", "Link"]]
        .head(20)
        .to_string(index=False)
    )