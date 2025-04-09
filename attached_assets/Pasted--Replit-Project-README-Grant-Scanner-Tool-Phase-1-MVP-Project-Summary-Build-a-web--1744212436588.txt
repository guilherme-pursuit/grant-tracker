## 🟣 Replit Project README: Grant Scanner Tool (Phase 1 MVP)

### 🧠 Project Summary
Build a **web-based grant scanner** that displays active funding opportunities Pursuit may be eligible for. It will pull data from **government, corporate, and foundation sources**, filtered to match our criteria: workforce development, adult learners, tech training, economic mobility, and New York/U.S. geography.

---

### 🎯 Key Features
- Scan top grant websites to pull **current open calls**
- Display in a **searchable, filterable, interactive dashboard**
- Tag each grant by:
  - Geography: NY / National
  - Topic: Workforce / Tech / Economic Mobility
  - Audience: Adults (24+), low-income
  - Funder type: Government / Corporate / Foundation
- Sort and filter by tag or deadline
- One-click **CSV export**

---

### 🧩 Data Sources to Scrape/API

#### 🟦 Government (via API/scraping)
- [Grants.gov](https://www.grants.gov) → use `search2` API
- [New York State Grants Gateway](https://grantsmanagement.ny.gov/) → scrape with Playwright/Selenium

#### 🟨 Corporate (scrape sites / monitor for calls)
- [Google.org](https://www.google.org/)
- [Microsoft Philanthropies](https://www.microsoft.com/en-us/philanthropies)
- [GitLab Foundation](https://foundation.gitlab.com/)
- [Salesforce Foundation](https://www.salesforce.org/)
- [Zoom Cares](https://zoom.us/zoomcares)
- [LinkedIn for Good](https://linkedinforgood.linkedin.com/)
- [Meta for Good](https://about.meta.com/social-impact/)
- [AT&T Foundation](https://about.att.com/csr)
- [Wells Fargo Foundation](https://www.wellsfargo.com/about/corporate-responsibility/community-giving/)
- [JPMorgan Chase Foundation](https://www.jpmorganchase.com/impact)
- [Robin Hood Foundation](https://www.robinhood.org/)

#### 🟥 Foundations (via RFP listings / site scrape)
- [Philanthropy News Digest (Candid)](https://philanthropynewsdigest.org/rfps)
- [Ford Foundation](https://www.fordfoundation.org/)
- [Siegel Family Endowment](https://www.siegelendowment.org/)
- [Patrick J. McGovern Foundation](https://www.mcgovern.org/)
- [New York Community Trust](https://www.nycommunitytrust.org/)
- [MacArthur Foundation](https://www.macfound.org/)

---

### 🛠️ Tech Stack
- **Backend**: Python (Flask or FastAPI)
- **Scraping**: BeautifulSoup for static, Playwright/Selenium for dynamic sites
- **Frontend**: HTML + DataTables.js or Bootstrap
- **Output**: CSV file for export

---

### 🗂️ Core Data Schema
```json
{
  "grant_name": "Google.org Impact Challenge",
  "funder": "Google.org",
  "deadline": "2025-02-10",
  "summary": "Funding nonprofits using AI for public benefit...",
  "url": "https://www.google.org/impactchallenge",
  "tags": ["National", "Tech Training", "Adults", "Corporate"]
}
```

---

### 🧪 Optional Enhancements
- Highlight grants due in next 2 weeks
- Auto-refresh scraper daily or weekly
- Add “last updated” timestamp
- Future Phase: Add contact info / decision makers

---

### 📦 Output
- Web-based interactive table
- Filters and tag search
- Export to CSV button

---

Let’s get started with the MVP!
