import streamlit as st
import pandas as pd
import datetime
import io
import base64
from grants_gov_api import fetch_grants_gov_opportunities
from ny_grants_gateway_scraper import fetch_ny_grants_gateway_opportunities
from grant_processor import process_grants, tag_grants
from utils import send_email, send_slack
from funder_data import FUNDER_CATEGORIES

# Set page configuration
st.set_page_config(
    page_title="Pursuit Grant Scanner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page title and description
st.title("Pursuit Grant Scanner")
st.markdown("""
This tool scans and displays active grant opportunities that Pursuit may be eligible for, 
filtered by criteria that match our mission: workforce development, tech training, 
economic mobility, and geographic focus.
""")

# Initialize session state for storing the grants data
if 'grants_data' not in st.session_state:
    st.session_state.grants_data = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None


# Function to fetch all grant opportunities
def fetch_all_grants():
    with st.spinner("Fetching grant opportunities..."):
        # Fetch government grants
        govt_grants = fetch_grants_gov_opportunities()
        ny_grants = fetch_ny_grants_gateway_opportunities()
        
        # Combine all grants
        all_grants = pd.concat([govt_grants, ny_grants], ignore_index=True)
        
        # Process and tag the grants
        processed_grants = process_grants(all_grants)
        tagged_grants = tag_grants(processed_grants)
        
        st.session_state.grants_data = tagged_grants
        st.session_state.last_refresh = datetime.datetime.now()
        
        return tagged_grants


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

# Only show filters if we have data
if st.session_state.grants_data is not None:
    df = st.session_state.grants_data
    
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
    
    # Date range filter for deadlines
    min_date = df["Deadline"].min() if not pd.isna(df["Deadline"].min()) else datetime.datetime.now()
    max_date = df["Deadline"].max() if not pd.isna(df["Deadline"].max()) else (datetime.datetime.now() + datetime.timedelta(days=365))
    
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
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["Deadline"].dt.date >= start_date) & 
            (filtered_df["Deadline"].dt.date <= end_date)
        ]
    
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

# Main content area
if st.session_state.grants_data is None:
    st.info("Click 'Refresh Grant Data' to fetch the latest grant opportunities.")
    if st.button("Fetch Grant Data"):
        fetch_all_grants()
else:
    # Display the filtered grants
    st.header(f"Grant Opportunities ({len(filtered_df)} results)")
    
    # Export options
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Export to CSV"):
            csv_data = filtered_df.to_csv(index=False)
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
                    filtered_df.to_csv(csv_buffer, index=False)
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
                    filtered_df.to_csv(csv_buffer, index=False)
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
    for i, row in filtered_df.iterrows():
        with st.expander(f"{row['Title']} - {row['Funder']} - Deadline: {row['Deadline'].strftime('%Y-%m-%d')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Description:** {row['Description']}")
                st.markdown(f"**Eligibility:** {row['Eligibility']}")
                st.markdown(f"**Award Amount:** ${row['Award Amount']:,.2f}" if not pd.isna(row['Award Amount']) else "**Award Amount:** Not specified")
            
            with col2:
                st.markdown("**Tags:**")
                st.markdown(f"- **Geography:** {row['Geography']}")
                st.markdown(f"- **Topic:** {row['Topic']}")
                st.markdown(f"- **Audience:** {row['Audience']}")
                st.markdown(f"- **Funder Type:** {row['Funder Type']}")
            
            st.markdown(f"**Application Link:** [{row['Link']}]({row['Link']})")

# Footer
st.markdown("---")
st.markdown("© 2023 Pursuit Grant Scanner - Made with Streamlit")
