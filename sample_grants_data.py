import pandas as pd
from datetime import datetime, timedelta

def fetch_sample_grants():
    today = datetime.today()
    return pd.DataFrame([
        {
            "Title": "Workforce Development Grant",
            "Funder": "Ford Foundation",
            "Description": "Funding for workforce training programs targeting underrepresented groups.",
            "Eligibility": "501(c)(3) nonprofits based in the U.S.",
            "Award Amount": 250000,
            "Deadline": today + timedelta(days=30),
            "Geography": "National",
            "Topic": "Workforce",
            "Audience": "Adults",
            "Funder Type": "Foundation",
            "Link": "https://www.fordfoundation.org/work/our-grants/"
        },
        {
            "Title": "Corporate Tech Reskilling Fund",
            "Funder": "Google.org",
            "Description": "Grants to train low-income adults in digital skills and software engineering.",
            "Eligibility": "Nonprofits with a focus on adult education.",
            "Award Amount": 500000,
            "Deadline": today + timedelta(days=45),
            "Geography": "New York",
            "Topic": "Tech Training",
            "Audience": "Adults",
            "Funder Type": "Corporate",
            "Link": "https://google.org"
        },
        {
            "Title": "Infrastructure Job Training",
            "Funder": "Grants.gov – Dept. of Labor",
            "Description": "Federal funding to support infrastructure job programs.",
            "Eligibility": "State/local government or nonprofit intermediaries.",
            "Award Amount": 1000000,
            "Deadline": today + timedelta(days=20),
            "Geography": "U.S.",
            "Topic": "Economic Mobility",
            "Audience": "Low‑income workers",
            "Funder Type": "Government",
            "Link": "https://www.grants.gov"
        }
    ])
    