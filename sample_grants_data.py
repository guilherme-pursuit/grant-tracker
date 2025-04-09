import pandas as pd
import datetime
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_sample_grants():
    """
    Generate sample grant data when API sources are unavailable.
    This provides realistic examples for demonstration purposes.
    
    Returns:
    - DataFrame with sample grants matching our expected structure
    """
    logging.info("Generating sample grant data for demonstration purposes...")
    
    # Sample grant opportunities
    grants = [
        {
            "Title": "Tech Skills Training for Underserved Communities",
            "Funder": "National Science Foundation",
            "Description": "Funding to support technology skills training programs for underserved adult populations, with a focus on software engineering and digital literacy.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=60),
            "Award Amount": 250000.0,
            "Eligibility": "Non-profit organizations with experience in workforce development and technology training.",
            "Link": "https://www.nsf.gov/funding/",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-001",
            "Geography": "National",
            "Topic": "Tech",
            "Audience": "Adults 24+",
            "Funder Type": "Government"
        },
        {
            "Title": "NYC Workforce Innovation Fund",
            "Funder": "NYC Department of Small Business Services",
            "Description": "Grants to support innovative workforce development initiatives in New York City, with priority for programs serving low-income adults.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=45),
            "Award Amount": 150000.0,
            "Eligibility": "Non-profit organizations operating in NYC with a track record of workforce development programs.",
            "Link": "https://www1.nyc.gov/site/sbs/index.page",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-002",
            "Geography": "NY",
            "Topic": "Workforce",
            "Audience": "Low-income",
            "Funder Type": "Government"
        },
        {
            "Title": "Economic Mobility Initiative",
            "Funder": "Ford Foundation",
            "Description": "Support for programs that create pathways to economic opportunity through skills training and career advancement for adults from disadvantaged backgrounds.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=90),
            "Award Amount": 200000.0,
            "Eligibility": "501(c)(3) organizations with programs focused on economic mobility and workforce development.",
            "Link": "https://www.fordfoundation.org/work/our-grants/",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-003",
            "Geography": "National",
            "Topic": "Economic Mobility",
            "Audience": "Low-income",
            "Funder Type": "Foundation"
        },
        {
            "Title": "Digital Skills for the Future Workforce",
            "Funder": "Microsoft",
            "Description": "Funding to support programs that teach coding, software development, and other digital skills to prepare adults for careers in technology.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=75),
            "Award Amount": 175000.0,
            "Eligibility": "Non-profit organizations and educational institutions with experience in technology education.",
            "Link": "https://www.microsoft.com/en-us/corporate-responsibility/philanthropies",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-004",
            "Geography": "National",
            "Topic": "Tech",
            "Audience": "Adults 24+",
            "Funder Type": "Corporate"
        },
        {
            "Title": "NY State Workforce Development Initiative",
            "Funder": "Empire State Development",
            "Description": "Grants to support workforce training programs that prepare New Yorkers for in-demand jobs in growing sectors including technology.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=30),
            "Award Amount": 300000.0,
            "Eligibility": "Organizations operating in New York State with a focus on workforce development programs.",
            "Link": "https://esd.ny.gov/",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-005",
            "Geography": "NY",
            "Topic": "Workforce",
            "Audience": "Adults 24+",
            "Funder Type": "Government"
        },
        {
            "Title": "Tech Equity and Inclusion Fund",
            "Funder": "Google.org",
            "Description": "Support for programs that increase diversity in the technology sector through skills training and career development for underrepresented populations.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=120),
            "Award Amount": 225000.0,
            "Eligibility": "Non-profit organizations with a focus on diversity and inclusion in the technology sector.",
            "Link": "https://www.google.org/",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-006",
            "Geography": "National",
            "Topic": "Tech",
            "Audience": "Low-income",
            "Funder Type": "Corporate"
        },
        {
            "Title": "Urban Economic Opportunity Grant",
            "Funder": "JPMorgan Chase Foundation",
            "Description": "Funding for programs that create economic opportunity in urban areas through skills training and job placement services.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=85),
            "Award Amount": 275000.0,
            "Eligibility": "Non-profit organizations serving urban populations with a focus on economic mobility.",
            "Link": "https://www.jpmorganchase.com/impact/global-philanthropy",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-007",
            "Geography": "National",
            "Topic": "Economic Mobility",
            "Audience": "Low-income",
            "Funder Type": "Corporate"
        },
        {
            "Title": "Brooklyn Tech Training Initiative",
            "Funder": "Brooklyn Community Foundation",
            "Description": "Support for organizations providing technology skills training to Brooklyn residents, with a focus on adults from low-income communities.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=50),
            "Award Amount": 125000.0,
            "Eligibility": "Non-profit organizations serving Brooklyn communities with experience in technology education.",
            "Link": "https://www.brooklyncommunityfoundation.org/grants",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-008",
            "Geography": "NY",
            "Topic": "Tech",
            "Audience": "Low-income",
            "Funder Type": "Foundation"
        },
        {
            "Title": "Adult Workforce Transition Fund",
            "Funder": "U.S. Department of Labor",
            "Description": "Grants to support programs that help adults transition to new careers through skills training and education, with a focus on growing sectors.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=100),
            "Award Amount": 350000.0,
            "Eligibility": "Organizations with experience in workforce development and adult education.",
            "Link": "https://www.dol.gov/general/grants",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-009",
            "Geography": "National",
            "Topic": "Workforce",
            "Audience": "Adults 24+",
            "Funder Type": "Government"
        },
        {
            "Title": "Technology Career Pathways Grant",
            "Funder": "Amazon",
            "Description": "Funding for programs that create clear pathways to careers in technology for adults from diverse backgrounds, including training and job placement services.",
            "Deadline": datetime.datetime.now() + datetime.timedelta(days=70),
            "Award Amount": 200000.0,
            "Eligibility": "Non-profit organizations with a track record of success in technology training and career development.",
            "Link": "https://www.aboutamazon.com/impact",
            "Source": "Sample Data",
            "Grant ID": "SAMPLE-010",
            "Geography": "National",
            "Topic": "Tech",
            "Audience": "Adults 24+",
            "Funder Type": "Corporate"
        }
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(grants)
    
    logging.info(f"Generated {len(df)} sample grant opportunities")
    return df

def fetch_sample_grants():
    """
    Fetch sample grants data when API sources are unavailable.
    This ensures the app has data to display for demonstration purposes.
    """
    return generate_sample_grants()