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
    /* Pursuit purple color for buttons and accents */
    .stButton>button {
        background-color: #4B46E9;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #3f3ac1;
    }
    
    /* Container formatting */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Heading colors */
    h1, h2, h3 {
        color: #4B46E9;
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
    }
    
    /* Grant cards styling */
    div[data-testid="stExpander"] {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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

# Page title with Pursuit logo
col1, col2 = st.columns([1, 5])

with col1:
    # Display Pursuit logo with custom size
    st.image("attached_assets/Pursuit Logo Purple.png", width=120)

with col2:
    st.title("Pursuit Grant Scanner")
    st.markdown("""
    This tool scans and displays active grant opportunities that Pursuit may be eligible for, 
    filtered by criteria that match our mission: workforce development, tech training, 
    economic mobility, and geographic focus.
    """)

# Navigation - Add tabs for different views
tab1, tab2 = st.tabs(["Grant Listings", "Dashboard"])

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
            
            if len(date_range) == 2:
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
                filtered_df = filtered_df[~has_deadline | (has_deadline & date_filter)]
            
            # Sort options
            sort_options = ["Deadline (Closest)", "Deadline (Furthest)", "Award Amount (High to Low)", "Award Amount (Low to High)"]
            sort_by = st.sidebar.selectbox("Sort By", sort_options)
            
            if sort_by == "Deadline (Closest)":
                filtered_df = filtered_df.sort_values("Deadline")
            elif sort_by == "Deadline (Furthest)":
                filtered_df = filtered_df.sort_values("Deadline", ascending=False)
            elif sort_by == "Award Amount (High to Low)":
                filtered_df = filtered_df.sort_values("Award Amount", ascending=False)
            elif sort_by == "Award Amount (Low to High)":
                filtered_df = filtered_df.sort_values("Award Amount")
        except KeyError as e:
            st.sidebar.error(f"Error: Missing required column - {str(e)}")
            st.sidebar.info("The data may not have been properly loaded. Please try refreshing.")
            # Ensure filtered_df is an empty DataFrame in case of error
            filtered_df = pd.DataFrame()

# Advanced search for grants
st.sidebar.header("Advanced Search")
search_query = st.sidebar.text_input("Search by keyword in title or description:")
search_funder = st.sidebar.text_input("Search by funder name:")

# Main content area - handled within tabs
if st.session_state.grants_data is None:
    # Try to load from database first
    db_grants = load_grants()
    
    # If no grants in database, show the fetch button
    if db_grants is None:
        with tab1:  # Display in the Grant Listings tab
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
    
    # Tab 1: Grant Listings
    with tab1:
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
    
    # Tab 2: Dashboard
    with tab2:
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
                # Group by funder type and count grants
                funder_type_counts = dashboard_filtered_df.groupby("Funder Type").size().reset_index(name="Count")
                
                # Create a bar chart of funder types
                if not funder_type_counts.empty:
                    st.bar_chart(funder_type_counts.set_index("Funder Type"))
                else:
                    st.info("No funder type data available.")
            
            with funder_col2:
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
footer_col1, footer_col2 = st.columns([1, 5])

with footer_col1:
    st.image("attached_assets/Pursuit Logo Purple.png", width=60)
    
with footer_col2:
    st.markdown("""
    <div style="color: #4B46E9; font-weight: bold;">Pursuit Grant Scanner</div>
    <div style="font-size: 0.8em;">© 2025 Pursuit - Made with 💜 to help find grant opportunities</div>
    """, unsafe_allow_html=True)
