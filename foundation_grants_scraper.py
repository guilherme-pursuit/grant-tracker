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
# Organized by category (major foundations, corporate foundations, grant aggregators)

# Major foundation websites
MAJOR_FOUNDATION_URLS = [
    "https://www.publicbenefitinnovationfund.org/",
    "https://www.fordfoundation.org/work/our-grants/",
    "https://www.macfound.org/grants",
    "https://www.rwjf.org/en/grants/funding-opportunities.html",
    "https://www.wkkf.org/grants",  # W.K. Kellogg Foundation
    "https://www.gatesfoundation.org/about/how-we-work/grant-opportunities",  # Bill & Melinda Gates Foundation
    "https://www.rockefellerfoundation.org/grants/",  # Rockefeller Foundation
    "https://www.hewlett.org/grants/",  # William and Flora Hewlett Foundation
    "https://www.carnegie.org/grants/",  # Carnegie Corporation of New York
    "https://www.opensocietyfoundations.org/grants",  # Open Society Foundations
    "https://www.kresge.org/our-work/grants-social-investments/",  # Kresge Foundation
    "https://www.irvine.org/grantmaking/",  # James Irvine Foundation
    "https://www.kauffman.org/grants/",  # Kauffman Foundation
    "https://sloan.org/grants/apply",  # Alfred P. Sloan Foundation
    "https://simonsfoundation.org/funding-opportunities/",  # Simons Foundation
    "https://www.arnoldventures.org/grants",  # Arnold Ventures
    "https://www.robinhood.org/programs/",  # Robin Hood Foundation
    "https://www.aecf.org/work/grant-making/",  # Annie E. Casey Foundation
    "https://www.emcf.org/grantees/",  # Edna McConnell Clark Foundation
    "https://www.luminafoundation.org/grants-opportunities/",  # Lumina Foundation
    "https://www.surdna.org/grants/",  # Surdna Foundation
    "https://www.kff.org/grants/",  # Kaiser Family Foundation
    "https://mmt.org/grants",  # Meyer Memorial Trust
    "https://www.aspeninstitute.org/programs/",  # Aspen Institute
    "https://www.joycefdn.org/grants",  # Joyce Foundation
    "https://www.schusterman.org/funding-opportunities",  # Schusterman Foundation
    "https://www.hfpg.org/apply-for-funding",  # Hartford Foundation for Public Giving
    "https://www.mcknight.org/grant-opportunities/",  # McKnight Foundation
    "https://www.mcarthurfdn.org/funding-opportunities",  # MacArthur Foundation
    "https://www.rbf.org/programs",  # Rockefeller Brothers Fund
    "https://www.blueshieldcafoundation.org/grants",  # Blue Shield of California Foundation
]

# Corporate foundation and tech company grants
CORPORATE_FOUNDATION_URLS = [
    "https://www.microsoft.com/en-us/corporate-responsibility/philanthropies/applying-for-a-grant",  # Microsoft
    "https://www.google.org/our-work/",  # Google.org
    "https://www.salesforce.org/grants/",  # Salesforce
    "https://foundation.walmart.org/grant-applicants/",  # Walmart Foundation
    "https://corporate.comcast.com/impact/philanthropy",  # Comcast NBCUniversal Foundation
    "https://about.bankofamerica.com/en/making-an-impact/charitable-foundation-funding",  # Bank of America Charitable Foundation
    "https://www.jpmorganchase.com/impact/our-approach/global-philanthropy",  # JPMorgan Chase Foundation
    "https://www.wellsfargo.com/about/corporate-responsibility/community-giving/",  # Wells Fargo Foundation
    "https://corporate.target.com/corporate-responsibility/philanthropy/corporate-giving/grant-guidelines",  # Target
    "https://www.att.com/foundation/",  # AT&T Foundation
    "https://corporate.verizon.com/responsibility/foundation/",  # Verizon Foundation
    "https://www.coca-colacompany.com/shared-future/coca-cola-foundation",  # Coca-Cola Foundation
    "https://www.ibm.org/initiatives/ibm-foundation",  # IBM Foundation
    "https://www.cigna.com/about-us/corporate-responsibility/cigna-foundation",  # Cigna Foundation
    "https://www.intel.com/content/www/us/en/corporate-responsibility/intel-foundation.html",  # Intel Foundation
    "https://www.prudential.com/links/about/corporate-social-responsibility",  # Prudential Foundation
    "https://www.oracle.com/corporate/citizenship/",  # Oracle
    "https://www.accenture.com/us-en/about/corporate-citizenship/corporate-citizenship",  # Accenture
    "https://www.adobe.com/corporate-responsibility.html",  # Adobe
    "https://corporate.delltechnologies.com/en-us/social-impact/transforming-lives/grants.htm",  # Dell Technologies
    "https://www.boeing.com/principles/community-engagement.page",  # Boeing
    "https://www.mastercard.us/en-us/about-mastercard/corporate-sustainability/social-sustainability/the-mastercard-impact-fund.html",  # Mastercard
    "https://www.uber.com/us/en/community/giving-back/",  # Uber
    "https://www.airbnb.org/",  # Airbnb.org
    "https://slack.com/social-impact",  # Slack
    "https://www.workday.com/en-us/company/foundation.html",  # Workday Foundation
    "https://www.linkedin.com/legal/linkedin-for-nonprofits",  # LinkedIn
    "https://corporate.walmart.com/c/us-foundation",  # Walmart Foundation
    "https://www.redhat.com/en/about/open-source-program-office",  # Red Hat
    "https://foundation.nvidia.com/",  # NVIDIA Foundation
]

# Grant aggregator sites and grant finding resources
GRANT_AGGREGATOR_URLS = [
    "https://candid.org/find-funding",  # Candid (formerly Foundation Center)
    "https://www.grantwatch.com/cat/41/workforce-grants.html",  # Grantwatch
    "https://philanthropynewyork.org/rfps-member-updates",  # Philanthropy New York
    "https://www.grants.gov/web/grants/search-grants.html",  # Grants.gov
    "https://www.instrumentl.com/nonprofit-grants",  # Instrumentl
    "https://grantstation.com/search/funding-resources",  # GrantStation
    "https://www.insidephilanthropy.com/grants-for-nonprofits",  # Inside Philanthropy
    "https://www.philanthropy.com/grants",  # Chronicle of Philanthropy
    "https://ssir.org/topics/category/funders",  # Stanford Social Innovation Review
    "https://www.grantforward.com/index",  # GrantForward
    "https://www.foundationcenter.org/",  # Foundation Center
    "https://www.charitynavigator.org/",  # Charity Navigator
    "https://www.councilofnonprofits.org/tools-resources/finding-funds",  # National Council of Nonprofits
    "https://www.tgci.com/funding-sources",  # The Grantsmanship Center
    "https://philanthropynewsdigest.org/rfps",  # Philanthropy News Digest
    "https://www.devex.com/funding",  # Devex Pro Funding
    "https://www.pivotdb.com",  # Pivot
    "https://grantselect.com/",  # GrantSelect
]

# Community foundation websites (often have local workforce development grants)
COMMUNITY_FOUNDATION_URLS = [
    "https://www.nycommunitytrust.org/information-for/for-nonprofits/",  # New York Community Trust
    "https://www.siliconvalleycf.org/grantmaking",  # Silicon Valley Community Foundation
    "https://www.cct.org/nonprofits/",  # Chicago Community Trust
    "https://www.calfund.org/nonprofits/grant-opportunities/",  # California Community Foundation
    "https://www.cfgreateratlanta.org/nonprofits/",  # Community Foundation for Greater Atlanta
    "https://www.clevelandfoundation.org/grants/apply-for-a-grant/",  # Cleveland Foundation
    "https://www.pittsburghfoundation.org/apply",  # Pittsburgh Foundation
    "https://www.siliconvalleycf.org/grants",  # Silicon Valley Community Foundation
    "https://www.cof.org/community-foundation-locator",  # Community Foundation Locator
]

# Special foundation URLs based on the user-provided list
# This dictionary maps foundation names to their website URLs
SPECIFIC_FOUNDATION_URLS = {
    # Major Foundations
    "AARP Foundation": "https://www.aarp.org/aarp-foundation/grants/",
    "Abbvie Foundation": "https://www.abbvie.com/responsibility/abbvie-foundation.html",
    "Alfred P. Sloan Foundation": "https://sloan.org/grants/apply",
    "Anna E. Casey Foundation": "https://www.aecf.org/work/grant-making/",
    "Arnold Ventures": "https://www.arnoldventures.org/grants",
    "Ascendium Education Group": "https://www.ascendiumphilanthropy.org/our-grantmaking/",
    "Bill & Melinda Gates Foundation": "https://www.gatesfoundation.org/about/how-we-work/grant-opportunities",
    "Bloomberg Philanthropies": "https://www.bloomberg.org/about/annual-report/",
    "Carnegie Corporation of New York": "https://www.carnegie.org/grants/",
    "Ford Foundation": "https://www.fordfoundation.org/work/our-grants/",
    "Hewlett Foundation": "https://hewlett.org/grants/",
    "Knight Foundation": "https://knightfoundation.org/funding-opp-special/",
    "Kresge Foundation": "https://kresge.org/grants-social-investments/current-funding-opportunities/",
    "Lumina Foundation": "https://www.luminafoundation.org/grants-opportunities/",
    "MacArthur Foundation": "https://www.macfound.org/grants",
    "Mellon Foundation": "https://mellon.org/grants/grantmaking-policies-and-guidelines/",
    "Robin Hood Foundation": "https://www.robinhood.org/programs/",
    "Rockefeller Foundation": "https://www.rockefellerfoundation.org/grants/",
    "W.K. Kellogg Foundation": "https://www.wkkf.org/grants",
    
    # Corporate Foundations
    "Amazon": "https://www.aboutamazon.com/impact/community/", 
    "AT&T Foundation": "https://www.att.com/foundation/",
    "Adobe": "https://www.adobe.com/corporate-responsibility/community.html",
    "Bank of America Charitable Foundation": "https://about.bankofamerica.com/en/making-an-impact/charitable-foundation-funding",
    "Cisco Foundation": "https://www.cisco.com/c/en/us/about/csr/community/nonprofits.html",
    "Comcast Foundation": "https://corporate.comcast.com/impact/philanthropy",
    "Google.org": "https://www.google.org/our-work/",
    "IBM Foundation": "https://www.ibm.org/initiatives/ibm-foundation",
    "JPMorgan Chase Foundation": "https://www.jpmorganchase.com/impact/our-approach/global-philanthropy",
    "Meta": "https://about.facebook.com/meta/impact/",
    "Microsoft Philanthropies": "https://www.microsoft.com/en-us/corporate-responsibility/philanthropies/",
    "Oracle": "https://www.oracle.com/corporate/citizenship/",
    "Salesforce Foundation": "https://www.salesforce.org/grants/",
    "Verizon Foundation": "https://www.verizon.com/about/responsibility/giving-and-grants",
    "Walmart Foundation": "https://walmart.org/how-we-give/walmart-foundation",
    "Wells Fargo Foundation": "https://www.wellsfargo.com/about/corporate-responsibility/community-giving/",
    
    # NY-Focused Foundations
    "New York Community Trust": "https://www.nycommunitytrust.org/information-for/for-nonprofits/",
    "Brooklyn Foundation": "https://www.brooklyncommunityfoundation.org/for-nonprofits/",
    "Tiger Foundation": "https://www.tigerfoundation.org/how-we-fund/",
    "Robin Hood Foundation": "https://www.robinhood.org/programs/",
    "Altman Foundation": "https://www.altmanfoundation.org/our-grantmaking/",
    "The Pinkerton Foundation": "https://www.thepinkertonfoundation.org/grant-seekers/guidelines",
    "The New York Women's Foundation": "https://www.nywf.org/fund-for-womens-equality/apply/"
}

# Add specific foundation URLs to the major foundations list
for foundation, url in SPECIFIC_FOUNDATION_URLS.items():
    if url not in MAJOR_FOUNDATION_URLS and url not in CORPORATE_FOUNDATION_URLS:
        # Check if URL is not already in our lists
        if url not in [u for u in MAJOR_FOUNDATION_URLS] and url not in [u for u in CORPORATE_FOUNDATION_URLS]:
            if "foundation" in foundation.lower() or "philanthrop" in foundation.lower() or "trust" in foundation.lower():
                MAJOR_FOUNDATION_URLS.append(url)
            else:
                CORPORATE_FOUNDATION_URLS.append(url)

# Combined list of all foundation grant URLs
FOUNDATION_GRANT_URLS = (
    MAJOR_FOUNDATION_URLS +
    CORPORATE_FOUNDATION_URLS +
    GRANT_AGGREGATOR_URLS +
    COMMUNITY_FOUNDATION_URLS
)

# Keywords relevant to Pursuit's mission for filtering
PURSUIT_KEYWORDS = [
    # Workforce and employment terms
    "workforce development", 
    "job training",
    "career development",
    "vocational training",
    "reskilling",
    "upskilling",
    "employment opportunities",
    "job placement",
    "career pathways",
    "career readiness",
    "professional development",
    
    # Tech and digital skills terms
    "tech training", 
    "software engineering",
    "tech education",
    "technology education",
    "computer science",
    "digital skills",
    "coding",
    "programming",
    "IT training",
    "web development",
    "data science",
    "technology workforce",
    "tech talent",
    "digital literacy",
    "STEM education",
    "developer training",
    
    # Economic terms
    "economic mobility",
    "economic opportunity",
    "economic empowerment",
    "economic inclusion",
    "economic equity",
    "income mobility",
    "financial inclusion",
    "financial literacy",
    "poverty reduction",
    "wealth building",
    
    # Educational terms
    "adult education",
    "continuing education",
    "lifelong learning",
    "post-secondary education",
    "certificate programs",
    "educational access",
    "skill development",
    "technical education",
    
    # Target population terms
    "low income",
    "underserved",
    "underrepresented",
    "equity",
    "diversity",
    "inclusion",
    "DEI",
    "marginalized",
    "disadvantaged",
    "opportunity youth",
    "non-traditional students",
    "adult learners",
    "immigrants",
    "refugees",
    "communities of color",
    "BIPOC",
    "justice-involved individuals",
    "formerly incarcerated",
    "persons with disabilities",
    "workforce barriers",
    
    # Geographic focus for NY
    "new york city",
    "NYC",
    "urban workforce",
    "urban communities",
    
    # Other relevant terms
    "nonprofit capacity building",
    "social innovation",
    "future of work",
    "human capital",
    "socioeconomic advancement",
    "workforce equity",
    "apprenticeship",
    "mentorship",
    "social mobility"
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
                
                # Get foundation name from our mapping if available
                foundation_name = None
                
                # First check if this URL is in our specific foundation list
                for fdn_name, fdn_url in SPECIFIC_FOUNDATION_URLS.items():
                    if fdn_url == url or url.startswith(fdn_url):
                        foundation_name = fdn_name
                        break
                
                # If not found, extract from URL
                if not foundation_name:
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
        "div.grant-listing", "li.grant-item", "div.rfp-item",
        "div.wp-block-columns", "div.wp-block-column",
        "li.listing", "div.grant-card", "div.funding", "div.grant-item",
        "div.funding-item", "div.opportunity-item", "div.grant-container",
        "div.accordion-item", "div.fund"
    ]
    
    # Initialize containers list
    containers = []
    
    # Special case handling for specific foundation websites
    
    # Special case for Public Benefit Innovation Fund
    if "publicbenefitinnovationfund" in base_url:
        # Try to find their grant information which is in WordPress blocks
        program_blocks = soup.find_all("div", class_="wp-block-columns")
        if program_blocks:
            containers.extend(program_blocks)
            logging.info(f"Found {len(program_blocks)} potential grant blocks from Public Benefit Innovation Fund")
            
    # Special case for Robin Hood Foundation
    elif "robinhood.org" in base_url:
        program_blocks = soup.find_all("div", class_="program")
        if program_blocks:
            containers.extend(program_blocks)
            logging.info(f"Found {len(program_blocks)} potential grant blocks from Robin Hood Foundation")
            
    # Special case for Gates Foundation
    elif "gatesfoundation.org" in base_url:
        grant_blocks = soup.find_all("div", class_="opportunity")
        if grant_blocks:
            containers.extend(grant_blocks)
            logging.info(f"Found {len(grant_blocks)} potential grant blocks from Gates Foundation")
            
    # Special case for Ford Foundation
    elif "fordfoundation.org" in base_url:
        grant_items = soup.find_all("div", class_="card")
        if grant_items:
            containers.extend(grant_items)
            logging.info(f"Found {len(grant_items)} potential grant blocks from Ford Foundation")
            
    # Special case for MacArthur Foundation
    elif "macfound.org" in base_url:
        grant_items = soup.find_all("article", class_="card")
        if grant_items:
            containers.extend(grant_items)
            logging.info(f"Found {len(grant_items)} potential grant blocks from MacArthur Foundation")
    
    # Special case for Rockefeller Foundation
    elif "rockefellerfoundation.org" in base_url:
        grant_items = soup.find_all("div", class_="card")
        if grant_items:
            containers.extend(grant_items)
            logging.info(f"Found {len(grant_items)} potential grant blocks from Rockefeller Foundation")
            
    # Special case for Lumina Foundation
    elif "luminafoundation.org" in base_url:
        grant_items = soup.find_all(["div", "article"], class_=re.compile(r"(grant|funding)"))
        if grant_items:
            containers.extend(grant_items)
            logging.info(f"Found {len(grant_items)} potential grant blocks from Lumina Foundation")
            
    # Special case for JPMorgan Chase
    elif "jpmorganchase.com" in base_url:
        grant_items = soup.find_all("div", class_=re.compile(r"(card|grid-item|program)"))
        if grant_items:
            containers.extend(grant_items)
            logging.info(f"Found {len(grant_items)} potential grant blocks from JPMorgan Chase Foundation")
            
    # Special case for Google.org
    elif "google.org" in base_url:
        grant_items = soup.find_all("div", class_=re.compile(r"(card|initiative|program)"))
        if grant_items:
            containers.extend(grant_items)
            logging.info(f"Found {len(grant_items)} potential grant blocks from Google.org")
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
            
            # Skip if title is too generic or too short
            if (title.lower() in ["untitled", "grant", "opportunity", "program", "initiative"]) or len(title) < 15:
                continue
                
            # Skip entries with generic or helper-text titles
            skip_titles = [
                "click here", "page help", "tutorial", "help", "login", "register", 
                "pdf", "manual", "learn more", "home", "back", "next",
                "apply now", "submit", "contact", "about", "mission"
            ]
            
            if any(skip_word in title.lower() for skip_word in skip_titles):
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
                
            # Skip entries with links to non-grant pages
            skip_links = ['help', 'tutorial', 'manual', '.pdf', 'about', 'contact', 'login']
            if any(skip_item in link.lower() for skip_item in skip_links):
                continue
                
            # If link is just the homepage, it's probably not a specific grant
            if link == base_url:
                # Only accept if title is very specific
                if len(title) < 30:
                    continue
            
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
            
            # Skip entries with inadequate descriptions
            if description == "No description available. Please visit the website for more information." or len(description) < 30:
                # Only keep if we have a good title, deadline AND award amount
                if not (len(title) > 40 and deadline and award_amount):
                    continue
            
            # Check if grant is relevant to Pursuit's mission
            is_relevant = any(
                keyword.lower() in title.lower() or keyword.lower() in description.lower()
                for keyword in PURSUIT_KEYWORDS
            )
            
            # Quality check - make sure we have at least some meaningful information
            has_quality_data = False
            
            # Grant must have either deadline or award amount to be considered complete enough
            if deadline or award_amount:
                has_quality_data = True
                
            # Grant with very specific title and good description is also acceptable
            if len(title) > 30 and len(description) > 100:
                has_quality_data = True
                
            if is_relevant and has_quality_data:
                grants.append(grant)
                
        except Exception as e:
            logging.warning(f"Error extracting grant details: {str(e)}")
            continue
    
    return grants