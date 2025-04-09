import streamlit as st
import pandas as pd
import datetime
import io
import base64
import time
from grants_gov_api import fetch_grants_gov_opportunities
from ny_grants_gateway_scraper import fetch_ny_grants_gateway_opportunities
from foundation_grants_scraper import fetch_foundation_grants
from grant_processor import process_grants, tag_grants
from utils import send_email, send_slack
from funder_data import FUNDER_CATEGORIES
from sample_grants_data import fetch_sample_grants
from database import save_grants_to_db, load_grants_from_db, check_db_connection, clean_low_quality_grants

# Set page configuration
st.set_page_config(
    page_title="Pursuit Grant Scanner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Pursuit branding and mobile responsiveness
st.markdown("""
<style>
    /* Pursuit purple color for buttons and accents - matching Pursuit.org */
    .stButton>button {
        background-color: #4B46E9;
        color: white;
        border-radius: 4px;
        padding: 0.75rem 1.5rem;
        border: none;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 14px;
    }
    .stButton>button:hover {
        background-color: #3f3ac1;
    }
    
    /* Container formatting */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Heading colors and fonts to match Pursuit.org */
    h1, h2, h3 {
        color: #4B46E9;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 700;
    }
    
    h1 {
        font-size: 2.5rem;
        letter-spacing: -0.5px;
    }
    
    h2 {
        font-size: 2rem;
        letter-spacing: -0.3px;
    }
    
    h3 {
        font-size: 1.5rem;
        letter-spacing: -0.2px;
    }
    
    /* Link styling */
    a {
        color: #4B46E9;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eee;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-top: 10px;
        padding-bottom: 10px;
        border-radius: 4px 4px 0 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4B46E9 !important;
        color: white !important;
        font-weight: bold;
    }
    
    /* Responsive styling for mobile */
    @media (max-width: 768px) {
        .row-widget.stButton {
            width: 100%;
        }
        
        /* Make columns stack on mobile */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 1rem;
        }
        
        /* Make the grant cards more readable on mobile */
        .stExpander {
            padding: 0.5rem 0;
        }
        
        /* Add spacing between elements */
        .css-ocqkz7, .css-1lcbmhc {
            margin-bottom: 1rem;
        }
        
        h1 {
            font-size: 1.8rem;
        }
        
        h2 {
            font-size: 1.5rem;
        }
    }
    
    /* Grant cards styling */
    div[data-testid="stExpander"] {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    
    div[data-testid="stExpander"]:hover {
        border-color: #4B46E9;
        box-shadow: 0 2px 5px rgba(75, 70, 233, 0.1);
    }
    
    /* Status indicators */
    .status-open {
        color: #00C853;
        font-weight: bold;
    }
    .status-closed {
        color: #F44336;
        font-weight: bold;
    }
    .status-closing-soon {
        color: #FF9800;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Page title with Pursuit Wordmark and branding
# Load images properly using Streamlit's image function
from PIL import Image
import os

# Load the Pursuit Wordmark image
try:
    wordmark_path = os.path.join('attached_assets', 'Pursuit Wordmark White on Purple.png')
    wordmark_img = Image.open(wordmark_path)
    
    # Create a container with purple background for the wordmark
    wordmark_container = st.container()
    with wordmark_container:
        st.markdown("""
        <div style="background-color: #4B46E9; padding: 24px 0; margin-bottom: 30px; display: flex; justify-content: center;">
        </div>
        """, unsafe_allow_html=True)
        # Place the image in the center of the container
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.image(wordmark_img, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load Pursuit Wordmark image: {e}")
    # Fallback header if image can't be loaded
    st.markdown("""
    <div style="background-color: #4B46E9; padding: 24px 0; margin-bottom: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">PURSUIT</h1>
    </div>
    """, unsafe_allow_html=True)

# Load the Pursuit Logo image
try:
    logo_path = os.path.join('attached_assets', 'Pursuit Logo Purple.png')
    logo_img = Image.open(logo_path)
    
    # Create header with logo and text
    header_cols = st.columns([1, 5])
    with header_cols[0]:
        st.image(logo_img, width=80)
    with header_cols[1]:
        st.markdown("""
        <h1 style="color: #4B46E9; margin-bottom: 5px; font-size: 2.5rem; font-weight: 700;">Grant Scanner</h1>
        <p style="margin-top: 0; color: #333; font-size: 1.1rem;">This tool scans and displays active grant opportunities that Pursuit may be eligible for, 
        filtered by criteria that match our mission: workforce development, tech training, 
        economic mobility, and geographic focus.</p>
        """, unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Could not load Pursuit Logo image: {e}")
    # Fallback header without logo
    st.markdown("""
    <h1 style="color: #4B46E9; margin-bottom: 5px; font-size: 2.5rem; font-weight: 700;">Grant Scanner</h1>
    <p style="margin-top: 0; color: #333; font-size: 1.1rem;">This tool scans and displays active grant opportunities that Pursuit may be eligible for, 
    filtered by criteria that match our mission: workforce development, tech training, 
    economic mobility, and geographic focus.</p>
    """, unsafe_allow_html=True)

# Navigation - Add button-based navigation instead of tabs
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Grant Listings"

# Navigation is now handled by the custom-nav-container below

# Use a simpler navigation approach with radio buttons styled as tabs
selected_tab = st.radio("View", ["GRANT LISTINGS", "DASHBOARD"], horizontal=True, label_visibility="collapsed")

# Map the selected tab to our session state view
if selected_tab == "GRANT LISTINGS":
    st.session_state.current_view = "Grant Listings"
else:
    st.session_state.current_view = "Dashboard"

# Style the radio buttons to look like tabs
st.markdown("""
<style>
    /* Style the radio buttons to look like tabs */
    div.row-widget.stRadio > div {
        flex-direction: row;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    
    div.row-widget.stRadio > div > label {
        background-color: #f5f5f5;
        color: #333;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 1;
        min-width: 150px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    div.row-widget.stRadio > div > label:hover {
        background-color: #e9e9e9;
    }
    
    div.row-widget.stRadio > div [data-baseweb="radio"] > div:first-child {
        display: none;
    }
    
    div.row-widget.stRadio > div [data-testid="stMarkdownContainer"] {
        font-size: 16px;
    }
    
    /* Style the selected tab */
    div.row-widget.stRadio > div [data-baseweb="radio"][aria-checked="true"] + label {
        background-color: #4B46E9;
        color: white;
        border-color: #4B46E9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for storing the grants data
if 'grants_data' not in st.session_state:
    st.session_state.grants_data = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None


# Function to load grants from database
def load_grants():
    with st.spinner("Loading grants from database..."):
        # Check database connection
        if not check_db_connection():
            st.error("Database connection failed. Unable to load saved grants.")
            return None
        
        # Clean database of low-quality grants first
        cleaned = clean_low_quality_grants()
        if cleaned:
            st.success("Cleaned database of low-quality grants")
        
        # Load grants from database
        grants_df = load_grants_from_db()
        
        if grants_df.empty:
            st.info("No grants found in database. Fetching from external sources.")
            return None
        
        st.success(f"Loaded {len(grants_df)} grants from database.")
        st.session_state.grants_data = grants_df
        st.session_state.last_refresh = datetime.datetime.now()
        
        return grants_df


# Function to fetch all grant opportunities
def fetch_all_grants():
    with st.spinner("Fetching grant opportunities..."):
        # Clean database of low-quality grants first
        if check_db_connection():
            cleaned = clean_low_quality_grants()
            if cleaned:
                st.success("Cleaned database of low-quality grants")
                
        # Fetch grants from all sources - prioritize foundation and corporate
        foundation_grants = fetch_foundation_grants()
        ny_grants = fetch_ny_grants_gateway_opportunities()
        govt_grants = fetch_grants_gov_opportunities()
        
        # Track data sources
        sources = []
        if not foundation_grants.empty:
            sources.append("Foundation Grants")
        if not ny_grants.empty:
            sources.append("NY Grants Gateway")
        if not govt_grants.empty:
            sources.append("Grants.gov")
            
        # Combine all grants from actual sources - prioritize foundation and corporate by listing them first
        all_grants = pd.concat([foundation_grants, ny_grants, govt_grants], ignore_index=True)
        
        # If we have data from external sources, process and display it
        if not all_grants.empty:
            st.success(f"Successfully retrieved grant data from: {', '.join(sources)}")
            
            # Process and tag the grants
            processed_grants = process_grants(all_grants)
            tagged_grants = tag_grants(processed_grants)
            
            # Save to database
            if check_db_connection():
                save_success = save_grants_to_db(tagged_grants)
                if save_success:
                    st.success(f"Saved {len(tagged_grants)} grants to database.")
                else:
                    st.warning("Failed to save grants to database.")
            else:
                st.warning("Database connection failed. Grants will not be saved.")
            
            st.session_state.grants_data = tagged_grants
            st.session_state.last_refresh = datetime.datetime.now()
            
            return tagged_grants
        else:
            # If no external data is available, show an error message
            st.error("No grant data could be retrieved from external sources at this time.")
            
            # Check if we have data in the database as a fallback
            if check_db_connection():
                db_grants = load_grants_from_db()
                if not db_grants.empty:
                    st.info(f"Displaying {len(db_grants)} previously saved grants from database.")
                    st.session_state.grants_data = db_grants
                    st.session_state.last_refresh = datetime.datetime.now()
                    return db_grants
            
            # Return empty DataFrame if no data is available
            return pd.DataFrame()


# Sidebar for filters and controls
st.sidebar.header("Grant Scanner Controls")

# Refresh button
if st.sidebar.button("Refresh Grant Data"):
    fetch_all_grants()
    st.success("Grant data refreshed successfully!")

# Display last refresh time if available
if st.session_state.last_refresh:
    st.sidebar.info(f"Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Filter options in sidebar
st.sidebar.header("Filter Options")

# Initialize filtered_df to ensure it's defined regardless of condition outcomes
filtered_df = pd.DataFrame()

# Only show filters if we have data
if st.session_state.grants_data is not None:
    df = st.session_state.grants_data
    
    # Check if DataFrame is empty or missing columns
    if df.empty:
        st.sidebar.warning("No grant data available. Please try refreshing the data.")
    else:
        try:
            # Geography filter
            geography_options = ["All"] + sorted(df["Geography"].unique().tolist())
            selected_geography = st.sidebar.selectbox("Geography", geography_options)
            
            # Topic filter
            topic_options = ["All"] + sorted(df["Topic"].unique().tolist())
            selected_topic = st.sidebar.selectbox("Topic", topic_options)
            
            # Audience filter
            audience_options = ["All"] + sorted(df["Audience"].unique().tolist())
            selected_audience = st.sidebar.selectbox("Audience", audience_options)
            
            # Funder type filter
            funder_options = ["All"] + sorted(df["Funder Type"].unique().tolist())
            selected_funder = st.sidebar.selectbox("Funder Type", funder_options)
            
            # Grant status filter
            today = datetime.datetime.now().date()
            status_options = ["All", "Open", "Closing Soon", "Closed"]
            selected_status = st.sidebar.selectbox("Grant Status", status_options)
            
            # Date range filter for deadlines
            non_null_deadlines = df["Deadline"].dropna()
            if len(non_null_deadlines) > 0:
                min_date = non_null_deadlines.min() if not pd.isna(non_null_deadlines.min()) else datetime.datetime.now()
                max_date = non_null_deadlines.max() if not pd.isna(non_null_deadlines.max()) else (datetime.datetime.now() + datetime.timedelta(days=365))
            else:
                min_date = datetime.datetime.now()
                max_date = datetime.datetime.now() + datetime.timedelta(days=365)
            
            date_range = st.sidebar.date_input(
                "Deadline Range",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date()
            )
            
            # Apply filters
            filtered_df = df.copy()
            
            if selected_geography != "All":
                filtered_df = filtered_df[filtered_df["Geography"] == selected_geography]
            
            if selected_topic != "All":
                filtered_df = filtered_df[filtered_df["Topic"] == selected_topic]
            
            if selected_audience != "All":
                filtered_df = filtered_df[filtered_df["Audience"] == selected_audience]
            
            if selected_funder != "All":
                filtered_df = filtered_df[filtered_df["Funder Type"] == selected_funder]
            
            # Apply status filter
            if selected_status != "All":
                today = datetime.datetime.now().date()
                two_weeks_later = today + datetime.timedelta(days=14)
                
                # First check if "Deadline" column exists to avoid KeyError
                if "Deadline" not in filtered_df.columns:
                    st.sidebar.warning("Missing 'Deadline' column. Cannot filter by status.")
                else:
                    try:
                        if selected_status == "Open":
                            # Show only grants with deadlines in the future or no deadline
                            today_pd = pd.to_datetime(today)
                            
                            # Convert dates safely for comparison
                            open_filter = filtered_df["Deadline"].apply(lambda x: 
                                pd.Timestamp(x.date()) >= today_pd if not pd.isna(x) else True)
                            
                            filtered_df = filtered_df[open_filter]
                        elif selected_status == "Closing Soon":
                            # Show only grants with deadlines in the next two weeks
                            today_pd = pd.to_datetime(today)
                            two_weeks_later_pd = pd.to_datetime(two_weeks_later)
                            
                            # Convert dates safely for comparison
                            closing_soon_filter = filtered_df["Deadline"].apply(lambda x: 
                                pd.Timestamp(x.date()) >= today_pd and pd.Timestamp(x.date()) <= two_weeks_later_pd
                                if not pd.isna(x) else False)
                            
                            filtered_df = filtered_df[closing_soon_filter]
                        elif selected_status == "Closed":
                            # Show only grants with deadlines in the past
                            today_pd = pd.to_datetime(today)
                            
                            # Convert dates safely for comparison
                            closed_filter = filtered_df["Deadline"].apply(lambda x: 
                                pd.Timestamp(x.date()) < today_pd if not pd.isna(x) else False)
                            
                            filtered_df = filtered_df[closed_filter]
                    except Exception as e:
                        st.sidebar.error(f"Error filtering by status: {str(e)}")
                        st.sidebar.info("Some grants may not have deadline information.")
            
            if len(date_range) == 2:
                # First check if the Deadline column exists
                if "Deadline" not in filtered_df.columns:
                    st.sidebar.warning("Missing 'Deadline' column. Cannot filter by date range.")
                else:
                    try:
                        start_date, end_date = date_range
                        # Only apply date filter to grants with deadlines
                        has_deadline = ~filtered_df["Deadline"].isna()
                        
                        # Convert dates to pandas datetime objects for comparison
                        start_date_pd = pd.to_datetime(start_date)
                        end_date_pd = pd.to_datetime(end_date)
                        
                        # Convert Deadline column to date format for comparison
                        # This handles the datetime64[ns] vs date comparison issue
                        deadline_filter = filtered_df["Deadline"].apply(lambda x: 
                            pd.Timestamp(x.date()) >= start_date_pd and pd.Timestamp(x.date()) <= end_date_pd 
                            if not pd.isna(x) else False)
                        
                        date_filter = deadline_filter
                        
                        # Keep rows where there's no deadline or the deadline is in range
                        # Convert boolean Series to numpy array to avoid type issues
                        date_mask = ~has_deadline.values | (has_deadline.values & date_filter.values)
                        filtered_df = filtered_df[date_mask]
                    except Exception as e:
                        st.sidebar.error(f"Error applying date filter: {str(e)}")
                        st.sidebar.info("Some grants may not have deadline information.")
            
            # Sort options - dynamically adjust based on available columns
            available_sort_options = []
            
            # Add deadline-based sorting if available
            if "Deadline" in filtered_df.columns:
                available_sort_options.extend(["Deadline (Closest)", "Deadline (Furthest)"])
            
            # Add award amount sorting if available
            if "Award Amount" in filtered_df.columns:
                available_sort_options.extend(["Award Amount (High to Low)", "Award Amount (Low to High)"])
                
            # Add a default option if no columns are available for sorting
            if not available_sort_options:
                available_sort_options = ["No sorting available"]
            
            sort_by = st.sidebar.selectbox("Sort By", available_sort_options)
            
            try:
                if sort_by == "Deadline (Closest)" and "Deadline" in filtered_df.columns:
                    filtered_df = filtered_df.sort_values("Deadline")
                elif sort_by == "Deadline (Furthest)" and "Deadline" in filtered_df.columns:
                    filtered_df = filtered_df.sort_values("Deadline", ascending=False)
                elif sort_by == "Award Amount (High to Low)" and "Award Amount" in filtered_df.columns:
                    filtered_df = filtered_df.sort_values("Award Amount", ascending=False)
                elif sort_by == "Award Amount (Low to High)" and "Award Amount" in filtered_df.columns:
                    filtered_df = filtered_df.sort_values("Award Amount")
            except Exception as e:
                st.sidebar.error(f"Error sorting data: {str(e)}")
        except KeyError as e:
            st.sidebar.error(f"Error: Missing required column - {str(e)}")
            st.sidebar.info("The data may not have been properly loaded. Please try refreshing.")
            # Ensure filtered_df is an empty DataFrame in case of error
            filtered_df = pd.DataFrame()

# Advanced search for grants
st.sidebar.header("Advanced Search")
search_query = st.sidebar.text_input("Search by keyword in title or description:")
search_funder = st.sidebar.text_input("Search by funder name:")

# Main content area - now using conditional rendering based on current_view
if st.session_state.grants_data is None:
    # Try to load from database first
    db_grants = load_grants()
    
    # If no grants in database, show the fetch button
    if db_grants is None:
        # Display in the Grant Listings view
        if st.session_state.current_view == "Grant Listings":
            st.info("Click 'Refresh Grant Data' to fetch the latest grant opportunities.")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Fetch Grant Data"):
                    fetch_all_grants()
            with col2:
                st.info("This will fetch grant data from external sources and save to database.")
else:
    # Apply advanced search filters if provided
    search_filtered_df = filtered_df.copy()
    
    if search_query:
        # Filter by search query in title or description
        search_filtered_df = search_filtered_df[
            search_filtered_df["Title"].str.contains(search_query, case=False, na=False) |
            search_filtered_df["Description"].str.contains(search_query, case=False, na=False)
        ]
    
    if search_funder:
        # Filter by funder name
        search_filtered_df = search_filtered_df[
            search_filtered_df["Funder"].str.contains(search_funder, case=False, na=False)
        ]
    
    # Grant Listings View
    if st.session_state.current_view == "Grant Listings":
        st.header(f"Grant Opportunities ({len(search_filtered_df)} results)")
        
        # Export options
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Export to CSV"):
                csv_data = search_filtered_df.to_csv(index=False)
                b64 = base64.b64encode(csv_data.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="pursuit_grants.csv">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            if st.button("Share Results"):
                share_option = st.radio("Share via:", ["Email", "Slack"])
                recipient = st.text_input("Recipient (Email or Slack channel):")
                
                if st.button("Send"):
                    if share_option == "Email" and recipient:
                        # Generate CSV
                        csv_buffer = io.StringIO()
                        search_filtered_df.to_csv(csv_buffer, index=False)
                        csv_content = csv_buffer.getvalue()
                        
                        # Send email
                        success = send_email(
                            recipient=recipient,
                            subject="Pursuit Grant Opportunities",
                            body=f"Please find attached the latest grant opportunities for Pursuit.\n\nGenerated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            attachment=csv_content,
                            attachment_name="pursuit_grants.csv"
                        )
                        
                        if success:
                            st.success(f"Email sent to {recipient}!")
                        else:
                            st.error("Failed to send email. Please try again.")
                    
                    elif share_option == "Slack" and recipient:
                        # Generate CSV
                        csv_buffer = io.StringIO()
                        search_filtered_df.to_csv(csv_buffer, index=False)
                        csv_content = csv_buffer.getvalue()
                        
                        # Send to Slack
                        success = send_slack(
                            channel=recipient,
                            message=f"Latest grant opportunities for Pursuit (Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                            file_content=csv_content,
                            file_name="pursuit_grants.csv"
                        )
                        
                        if success:
                            st.success(f"Sent to Slack channel {recipient}!")
                        else:
                            st.error("Failed to send to Slack. Please try again.")
        
        # Display grants in expandable sections
        for i, row in search_filtered_df.iterrows():
            deadline_str = row['Deadline'].strftime('%Y-%m-%d') if not pd.isna(row['Deadline']) else "No deadline"
            
            # Determine grant status for styling
            status_class = ""
            status_text = ""
            
            if not pd.isna(row['Deadline']):
                today = datetime.datetime.now().date()
                deadline_date = row['Deadline'].date()
                two_weeks_later = today + datetime.timedelta(days=14)
                
                if deadline_date < today:
                    status_class = "status-closed"
                    status_text = "CLOSED"
                elif deadline_date <= two_weeks_later:
                    status_class = "status-closing-soon"
                    status_text = "CLOSING SOON"
                else:
                    status_class = "status-open"
                    status_text = "OPEN"
            else:
                status_class = "status-open"
                status_text = "OPEN"
            
            # Create expander title with status indicator
            expander_title = f"{row['Title']} - {row['Funder']}"
            
            with st.expander(expander_title):
                # Status and deadline info at the top
                st.markdown(f"<div><span class='{status_class}'>{status_text}</span> - Deadline: {deadline_str}</div>", unsafe_allow_html=True)
                
                # Responsive columns for desktop and stacked for mobile
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("### Grant Details")
                    if not pd.isna(row['Description']):
                        st.markdown(f"**Description:** {row['Description']}")
                    if not pd.isna(row['Eligibility']):
                        st.markdown(f"**Eligibility:** {row['Eligibility']}")
                    
                    award_text = f"**Award Amount:** ${row['Award Amount']:,.2f}" if not pd.isna(row['Award Amount']) else "**Award Amount:** Not specified"
                    st.markdown(award_text)
                    
                    # Add link button if available
                    if not pd.isna(row['Link']) and row['Link'] != '':
                        st.markdown(f"[Apply Now ↗]({row['Link']})")
                
                with col2:
                    st.markdown("### Tags")
                    tags_md = []
                    if not pd.isna(row['Geography']):
                        tags_md.append(f"- **Geography:** {row['Geography']}")
                    if not pd.isna(row['Topic']):
                        tags_md.append(f"- **Topic:** {row['Topic']}")
                    if not pd.isna(row['Audience']):
                        tags_md.append(f"- **Audience:** {row['Audience']}")
                    if not pd.isna(row['Funder Type']):
                        tags_md.append(f"- **Funder Type:** {row['Funder Type']}")
                    
                    st.markdown("\n".join(tags_md))
    
    # Dashboard View
    elif st.session_state.current_view == "Dashboard":
        st.header("Grant Opportunities Dashboard")
        
        # Advanced dashboard search 
        st.subheader("Search Dashboard")
        dashboard_col1, dashboard_col2, dashboard_col3 = st.columns(3)
        
        with dashboard_col1:
            dashboard_search = st.text_input("Search by keyword:", key="dashboard_search")
        with dashboard_col2:
            funder_search = st.text_input("Search by funder name:", key="funder_search")
        with dashboard_col3:
            show_only_open = st.checkbox("Show only open applications", value=True)
        
        # Apply dashboard search filters
        dashboard_filtered_df = search_filtered_df.copy()
        
        if dashboard_search:
            dashboard_filtered_df = dashboard_filtered_df[
                dashboard_filtered_df["Title"].str.contains(dashboard_search, case=False, na=False) |
                dashboard_filtered_df["Description"].str.contains(dashboard_search, case=False, na=False)
            ]
        
        if funder_search:
            dashboard_filtered_df = dashboard_filtered_df[
                dashboard_filtered_df["Funder"].str.contains(funder_search, case=False, na=False)
            ]
        
        if show_only_open:
            today = datetime.datetime.now().date()
            today_pd = pd.to_datetime(today)
            
            # Convert dates safely for comparison
            open_filter = dashboard_filtered_df["Deadline"].apply(lambda x: 
                pd.Timestamp(x.date()) >= today_pd if not pd.isna(x) else True)
            
            dashboard_filtered_df = dashboard_filtered_df[open_filter]
        
        # Only show dashboard if we have data
        if dashboard_filtered_df.empty:
            st.info("No grants match the current filters. Adjust your filters to see the dashboard.")
        else:
            # Summary metrics at the top
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Total grants count
                st.metric("Total Grants", len(dashboard_filtered_df))
            
            with col2:
                # Average award amount
                avg_award = dashboard_filtered_df["Award Amount"].dropna().mean()
                if pd.isna(avg_award):
                    st.metric("Avg. Award Amount", "N/A")
                else:
                    st.metric("Avg. Award Amount", f"${avg_award:,.2f}")
            
            with col3:
                # Grants closing soon (next 30 days)
                today = datetime.datetime.now().date()
                thirty_days = today + datetime.timedelta(days=30)
                today_pd = pd.to_datetime(today)
                thirty_days_pd = pd.to_datetime(thirty_days)
                
                # Convert dates safely for comparison
                closing_soon_filter = dashboard_filtered_df["Deadline"].apply(lambda x: 
                    pd.Timestamp(x.date()) >= today_pd and pd.Timestamp(x.date()) <= thirty_days_pd
                    if not pd.isna(x) else False)
                
                closing_soon = dashboard_filtered_df[closing_soon_filter]
                st.metric("Closing in 30 Days", len(closing_soon))
            
            with col4:
                # Open grants
                today_pd = pd.to_datetime(today)
                
                # Convert dates safely for comparison
                open_filter = dashboard_filtered_df["Deadline"].apply(lambda x: 
                    pd.Timestamp(x.date()) >= today_pd if not pd.isna(x) else True)
                    
                open_grants = dashboard_filtered_df[open_filter]
                st.metric("Open Grants", len(open_grants))
            
            # Grants by Funder Type section
            st.subheader("Grants by Funder Type")
            
            # Create two columns for the funder type summary
            funder_col1, funder_col2 = st.columns([3, 2])
            
            with funder_col1:
                try:
                    # Group by funder type and count grants
                    if "Funder Type" in dashboard_filtered_df.columns:
                        funder_type_counts = dashboard_filtered_df.groupby("Funder Type").size().reset_index(name="Count")
                        
                        # Create a bar chart of funder types
                        if not funder_type_counts.empty:
                            st.bar_chart(funder_type_counts.set_index("Funder Type"))
                        else:
                            st.info("No funder type data available.")
                    else:
                        st.warning("Missing 'Funder Type' column. Cannot display chart.")
                except Exception as e:
                    st.error(f"Error creating chart: {str(e)}")
            
            with funder_col2:
                try:
                    # Check if required columns exist
                    if "Funder Type" in dashboard_filtered_df.columns and "Award Amount" in dashboard_filtered_df.columns:
                        # Table of grants by funder type with average award
                        funder_summary = dashboard_filtered_df.groupby("Funder Type").agg({
                            "Award Amount": ["mean", "max", "count"]
                        }).reset_index()
                        
                        # Flatten the multi-index columns
                        funder_summary.columns = ["Funder Type", "Avg. Award", "Max Award", "Count"]
                        
                        # Format the award amounts
                        funder_summary["Avg. Award"] = funder_summary["Avg. Award"].apply(
                            lambda x: f"${x:,.2f}" if not pd.isna(x) else "N/A"
                        )
                        funder_summary["Max Award"] = funder_summary["Max Award"].apply(
                            lambda x: f"${x:,.2f}" if not pd.isna(x) else "N/A"
                        )
                        
                        st.dataframe(funder_summary, use_container_width=True)
                    else:
                        missing_cols = []
                        if "Funder Type" not in dashboard_filtered_df.columns:
                            missing_cols.append("Funder Type")
                        if "Award Amount" not in dashboard_filtered_df.columns:
                            missing_cols.append("Award Amount")
                        st.warning(f"Missing required columns: {', '.join(missing_cols)}. Cannot display summary table.")
                except Exception as e:
                    st.error(f"Error creating summary table: {str(e)}")
            
            # Create sections for best grants by funder type
            st.subheader("Best Grants by Funder Type")
            
            # Get unique funder types
            funder_types = dashboard_filtered_df["Funder Type"].unique()
            
            # For each funder type, show the top grants by award amount
            for funder_type in funder_types:
                with st.expander(f"Best {funder_type} Grants"):
                    # Filter for this funder type and sort by award amount
                    funder_grants = dashboard_filtered_df[
                        dashboard_filtered_df["Funder Type"] == funder_type
                    ].sort_values("Award Amount", ascending=False).head(3)
                    
                    # Display top grants for this funder
                    if not funder_grants.empty:
                        for i, row in funder_grants.iterrows():
                            today = datetime.datetime.now().date()
                            status = "🟢 Open" if pd.isna(row['Deadline']) or row['Deadline'].date() >= today else "🔴 Closed"
                            
                            st.markdown(f"**{row['Title']}** - {status}")
                            st.markdown(f"*Funder: {row['Funder']}*")
                            
                            # Display deadline if available
                            deadline_str = row['Deadline'].strftime('%Y-%m-%d') if not pd.isna(row['Deadline']) else "No deadline"
                            st.markdown(f"*Deadline: {deadline_str}*")
                            
                            # Display award amount if available
                            award_str = f"${row['Award Amount']:,.2f}" if not pd.isna(row['Award Amount']) else "Not specified"
                            st.markdown(f"*Award Amount: {award_str}*")
                            
                            # Add link to application
                            st.markdown(f"[Apply Now]({row['Link']})")
                            st.markdown("---")
                    else:
                        st.info(f"No grants data available for {funder_type}.")
            
            # Top grants by award amount
            st.subheader("Top Grants by Award Amount")
            
            # Filter out grants with no award amount and get top 5
            top_grants = dashboard_filtered_df.dropna(subset=["Award Amount"]).sort_values("Award Amount", ascending=False).head(5)
            
            if not top_grants.empty:
                for i, row in top_grants.iterrows():
                    st.markdown(f"**{row['Title']}** - {row['Funder']} - **${row['Award Amount']:,.2f}**")
                    deadline_str = row['Deadline'].strftime('%Y-%m-%d') if not pd.isna(row['Deadline']) else "No deadline"
                    st.markdown(f"*Deadline: {deadline_str}*")
                    st.markdown(f"*[View Details]({row['Link']})*")
                    st.markdown("---")
            else:
                st.info("No grants with specified award amounts available.")
            
            # Grants by deadline
            st.subheader("Upcoming Grant Deadlines")
            
            # Filter out grants with no deadline and sort by closest deadline
            upcoming_deadlines = dashboard_filtered_df.dropna(subset=["Deadline"]).sort_values("Deadline")
            
            # Only show grants with future deadlines
            today = datetime.datetime.now().date()
            today_pd = pd.to_datetime(today)
            
            # Convert dates safely for comparison
            future_filter = upcoming_deadlines["Deadline"].apply(lambda x: 
                pd.Timestamp(x.date()) >= today_pd if not pd.isna(x) else False)
                
            future_deadlines = upcoming_deadlines[future_filter].head(5)
            
            if not future_deadlines.empty:
                for i, row in future_deadlines.iterrows():
                    days_until = (row['Deadline'].date() - datetime.datetime.now().date()).days
                    
                    st.markdown(f"**{row['Title']}** - 🟢 Open")
                    st.markdown(f"*Deadline: {row['Deadline'].strftime('%Y-%m-%d')} ({days_until} days remaining)*")
                    award_str = f"${row['Award Amount']:,.2f}" if not pd.isna(row['Award Amount']) else "Not specified"
                    st.markdown(f"*Award Amount: {award_str}*")
                    st.markdown(f"*[View Details]({row['Link']})*")
                    st.markdown("---")
            else:
                st.info("No grants with upcoming deadlines available.")
            
            # Count grants by status
            today = datetime.datetime.now().date()
            today_pd = pd.to_datetime(today)
            
            # Convert dates safely for comparison for open grants
            open_filter = dashboard_filtered_df["Deadline"].apply(lambda x: 
                pd.Timestamp(x.date()) >= today_pd if not pd.isna(x) else True)
            open_grants = len(dashboard_filtered_df[open_filter])
            
            # Convert dates safely for comparison for closed grants
            closed_filter = dashboard_filtered_df["Deadline"].apply(lambda x: 
                pd.Timestamp(x.date()) < today_pd if not pd.isna(x) else False)
            closed_grants = len(dashboard_filtered_df[closed_filter])
            no_deadline = len(dashboard_filtered_df[dashboard_filtered_df["Deadline"].isna()])
            
            # Create status summary data
            status_data = pd.DataFrame({
                "Status": ["Open", "Closed", "No Deadline"],
                "Count": [open_grants, closed_grants, no_deadline]
            })
            
            # Display status chart
            st.bar_chart(status_data.set_index("Status"))
            
            # Create charts for geography and topic distributions
            col1, col2 = st.columns(2)
            
            with col1:
                # Grants by geography
                st.subheader("Grants by Geography")
                geography_counts = dashboard_filtered_df["Geography"].value_counts().reset_index()
                geography_counts.columns = ["Geography", "Count"]
                
                # Display bar chart for geography
                st.bar_chart(geography_counts.set_index("Geography"))
                
            with col2:
                # Grants by topic
                st.subheader("Grants by Topic")
                topic_counts = dashboard_filtered_df["Topic"].value_counts().reset_index()
                topic_counts.columns = ["Topic", "Count"]
                
                # Display bar chart for topics
                st.bar_chart(topic_counts.set_index("Topic"))
            
            # Top grants by award amount
            st.subheader("Top Grants by Award Amount")
            
            # Filter out grants with no award amount and get top 5
            top_grants = dashboard_filtered_df.dropna(subset=["Award Amount"]).sort_values("Award Amount", ascending=False).head(5)
            
            if not top_grants.empty:
                for i, row in top_grants.iterrows():
                    st.markdown(f"**{row['Title']}** - {row['Funder']} - **${row['Award Amount']:,.2f}**")
                    deadline_str = row['Deadline'].strftime('%Y-%m-%d') if not pd.isna(row['Deadline']) else "No deadline"
                    st.markdown(f"*Deadline: {deadline_str}*")
                    st.markdown(f"*[View Details]({row['Link']})*")
                    st.markdown("---")
            else:
                st.info("No grants with specified award amounts available.")
            
            # Grants by deadline
            st.subheader("Upcoming Grant Deadlines")
            
            # Filter out grants with no deadline and sort by closest deadline
            upcoming_deadlines = dashboard_filtered_df.dropna(subset=["Deadline"]).sort_values("Deadline").head(5)
            
            if not upcoming_deadlines.empty:
                for i, row in upcoming_deadlines.iterrows():
                    days_until = (row['Deadline'].date() - datetime.datetime.now().date()).days
                    status = "🟢 Open" if days_until >= 0 else "🔴 Closed"
                    
                    st.markdown(f"**{row['Title']}** - {status}")
                    st.markdown(f"*Deadline: {row['Deadline'].strftime('%Y-%m-%d')} ({days_until} days remaining)*")
                    award_str = f"${row['Award Amount']:,.2f}" if not pd.isna(row['Award Amount']) else "Not specified"
                    st.markdown(f"*Award Amount: {award_str}*")
                    st.markdown(f"*[View Details]({row['Link']})*")
                    st.markdown("---")
            else:
                st.info("No grants with specified deadlines available.")

# Footer
st.markdown("---")
st.markdown("""
<div style="display: flex; align-items: center; max-width: 1200px; margin: 20px auto; padding: 0 20px;">
    <div style="margin-right: 20px;">
        <img src="data:image/png;base64,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" width="60">
    </div>
    <div>
        <div style="color: #4B46E9; font-weight: bold; font-size: 1.1rem;">Pursuit Grant Scanner</div>
        <div style="font-size: 0.8em;">© 2025 Pursuit - Evolve or Die | Rethink Priors | Days, Not Weeks | Build In Public</div>
    </div>
</div>
""", unsafe_allow_html=True)
