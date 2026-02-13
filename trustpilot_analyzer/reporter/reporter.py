import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from harvester.harvester import fetch_next_data
from analyst.analyst import (
    extract_aggregate_star_distribution,
    extract_main_page_star_distribution,
    extract_reviews_over_time,
    extract_source_distribution,
    extract_detailed_monthly_distribution,
    calculate_recent_reviews_count,
    analyze_reply_behavior
)
from config import PREDEFINED_DOMAINS

#RATING_COLOR_MAP = {
#    "1": "#E53935",  # Adjusted Red: Less neon, more professional
#    "2": "#FB8C00",  # Deep Orange: Bridges red and yellow perfectly
#    "3": "#FDD835",  # Sunflower Yellow: Readable against white, unlike pure yellow
#    "4": "#7CB342",  # Light Green: Vibrant but not washed out
#    "5": "#2E7D32"   # Dark Green: Forest green, matches the intensity of the red
#}

#RATING_COLOR_MAP = {
#    "1": "#D7191C",  # Deep Red
#    "2": "#FDAE61",  # Soft Orange
#    "3": "#FFFFBF",  # Cream Yellow (Neutral midpoint)
#    "4": "#A6D96A",  # Soft Green
#    "5": "#1A9641"   # Deep Green
#}

RATING_COLOR_MAP = {
    "1": "#FF4757",  # Watermelon Red
    "2": "#FFA502",  # Bright Tangerine
    "3": "#ECCC68",  # Honey Yellow (Warm)
    "4": "#7BED9F",  # Lime Green
    "5": "#2ED573"   # Emerald Green
}

def extract_business_info(data):
    """Extracts business unit info from the main data object."""
    if not data:
        return None
    try:
        return data['props']['pageProps']['businessUnit']
    except (KeyError, TypeError):
        return None

st.set_page_config(page_title="Trustpilot Analyzer", layout="wide")

# Custom CSS for Scandi/Modern look
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* Global Font and Colors */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #334155;
    }

    /* Main Background */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Content Container */
    .block-container {
        max-width: 1000px;
        padding-top: 3rem;
        padding-bottom: 5rem;
    }

    /* Headings */
    h1 {
        color: #0F172A;
        font-weight: 700;
        letter-spacing: -0.025em;
    }
    h2 {
        color: #1E293B;
        font-weight: 600;
        font-size: 1.5rem !important;
        letter-spacing: -0.015em;
        margin-top: 0.5rem;
    }
    h3 {
        color: #334155;
        font-weight: 500;
        font-size: 1.1rem !important;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    div[data-testid="stMetric"] label {
        color: #64748B;
        font-size: 0.875rem;
        font-weight: 500;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0F172A;
        font-size: 1.5rem;
        font-weight: 600;
    }

    /* Containers (Sections) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01), 0 2px 4px -1px rgba(0, 0, 0, 0.01);
        padding: 2rem;
        margin-bottom: 1rem;
    }

    /* Filters (Multiselect) */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #F1F5F9 !important;
        border: 1px solid #E2E8F0;
    }
    .stMultiSelect span[data-baseweb="tag"] span {
        color: #334155 !important;
    }
    div[data-baseweb="select"] > div {
        border-color: #CBD5E1 !important;
        border-radius: 6px;
    }
    
    /* Buttons */
    div.stButton > button {
        background-color: #0F172A;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    div.stButton > button:hover {
        background-color: #334155;
        color: white;
        border: none;
    }
    div.stButton > button:focus {
        background-color: #334155;
        color: white;
        border: none;
    }

    /* Plotly Charts - Clean up */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }

    /* --- Checkbox Styling --- */
    /* This targets the visual box of the checkbox when checked.
       The increased specificity helps override Streamlit's defaults. */
    .stApp div[data-testid="stCheckbox"] input:checked + div {
        background-color: #0F172A !important;
        border-color: #0F172A !important;
    }
    /* This ensures the text label and its container have no background. */
    div[data-testid="stCheckbox"] label > div:last-of-type,
    div[data-testid="stCheckbox"] label > div:last-of-type p {
        background: transparent !important;
        color: #334155 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Trustpilot Review Analyzer")

# Create Tabs
tab1, tab2 = st.tabs(["Single Domain Analysis", "Domain Comparison"])

# --- TAB 1: Single Domain Analysis ---
with tab1:
    # Initialize session state
    if "analyzed" not in st.session_state:
        st.session_state["analyzed"] = False
    if "review_data" not in st.session_state:
        st.session_state["review_data"] = None
    if "transparency_data" not in st.session_state:
        st.session_state["transparency_data"] = None
    if "domain" not in st.session_state:
        st.session_state["domain"] = ""

    if "domain_input_val" not in st.session_state:
        st.session_state["domain_input_val"] = "store.manutd.com"

    def update_domain_from_dropdown():
        if st.session_state.domain_dropdown:
            st.session_state.domain_input_val = st.session_state.domain_dropdown

    st.selectbox(
        "Select from predefined domains:",
        [""] + PREDEFINED_DOMAINS,
        key="domain_dropdown",
        on_change=update_domain_from_dropdown
    )

    domain_input = st.text_input("Enter domain:", key="domain_input_val")

    if st.button("Analyze Domain"):
        if domain_input:
            review_url = f"https://www.trustpilot.com/review/{domain_input}"
            transparency_url = f"{review_url}/transparency"

            with st.spinner(f"Scraping data for {domain_input}..."):
                review_data = fetch_next_data(review_url)
                transparency_data = fetch_next_data(transparency_url)
            
            if not review_data or not transparency_data:
                st.error(f"Failed to fetch all necessary data for '{domain_input}'. Please check the domain and try again.")
            else:
                st.session_state["review_data"] = review_data
                st.session_state["transparency_data"] = transparency_data
                st.session_state["domain"] = domain_input
                st.session_state["analyzed"] = True
                st.success(f"Successfully scraped data for **{domain_input}**.")
        else:
            st.warning("Please enter a domain to analyze.")

    if st.session_state["analyzed"]:
        domain = st.session_state["domain"]
        review_data = st.session_state["review_data"]
        transparency_data = st.session_state["transparency_data"]

        # --- Section 1: Overall Performance ---
        with st.container(border=True):
            st.header("Overall Performance")
            business_info = extract_business_info(review_data)
            if business_info:
                st.subheader(business_info.get('displayName', 'Unknown Brand'))
                
                # Metrics in 3 columns
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("TrustScore", f"{business_info.get('trustScore', 'N/A')} / 5")
                m_col2.metric("Total Reviews", f"{business_info.get('numberOfReviews', 'N/A')}")
                recent_count = calculate_recent_reviews_count(review_data)
                m_col3.metric("New Reviews (7 days)", recent_count)
                
                # Main Page Star Distribution
                main_star_dist_df = extract_main_page_star_distribution(review_data)
                if not main_star_dist_df.empty:
                    main_star_dist_df['rating'] = main_star_dist_df['rating'].astype(str)
                    main_star_dist_df['text'] = main_star_dist_df['percentage'].apply(lambda x: f"{x:.1f}%")
                    fig = px.bar(
                        main_star_dist_df,
                        x='percentage',
                        y='rating',
                        orientation='h',
                        title="Distribution of Star Ratings (All Time)",
                        labels={'rating': 'Star Rating', 'percentage': 'Percentage of Reviews (%)'},
                        color='rating',
                        color_discrete_map=RATING_COLOR_MAP,
                            category_orders={'rating': ["5", "4", "3", "2", "1"]},
                            text='text',
                            template="plotly_white"
                    )
                    fig.update_traces(textposition='outside')
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    
                    # Center the chart with ~60% width
                    _, col_chart, _ = st.columns([1, 3, 1])
                    with col_chart:
                        st.plotly_chart(fig, use_container_width=True)

        # --- Section 2: Lookback (Past 12 Months) ---
        with st.container(border=True):
            st.header("Lookback (Past 12 Months)")

            # 1. Get the detailed data which supports filtering
            detailed_reviews_df = extract_detailed_monthly_distribution(transparency_data)

            if not detailed_reviews_df.empty:
                # --- Filters ---
                col_filter1, col_filter2 = st.columns(2)
                
                # Get unique sorted options
                all_sources = sorted(detailed_reviews_df['source'].unique().tolist())
                all_ratings = sorted(detailed_reviews_df['rating'].unique().tolist())
                
                with col_filter1:
                    with st.popover("Filter by Source", use_container_width=True):
                        with st.form(f"{domain}_source_form", border=False):
                            selected_sources = []
                            for source in all_sources:
                                if st.checkbox(source, value=True, key=f"{domain}_source_{source}"):
                                    selected_sources.append(source)
                            st.form_submit_button("Apply")
                
                with col_filter2:
                    with st.popover("Filter by Rating", use_container_width=True):
                        with st.form(f"{domain}_rating_form", border=False):
                            selected_ratings = []
                            for rating in all_ratings:
                                if st.checkbox(str(rating), value=True, key=f"{domain}_rating_{rating}"):
                                    selected_ratings.append(rating)
                            st.form_submit_button("Apply")

                # Filter the DataFrame
                filtered_df = detailed_reviews_df.copy()
                if selected_sources:
                    filtered_df = filtered_df[filtered_df['source'].isin(selected_sources)]
                if selected_ratings:
                    filtered_df = filtered_df[filtered_df['rating'].isin(selected_ratings)]

                if filtered_df.empty:
                    st.warning("No reviews match the selected filters.")
                else:
                    # --- Visualizations based on filtered_df ---
                    col_dist, col_time = st.columns(2)

                    with col_dist:
                        # 1. Star Distribution (Aggregated from filtered data)
                        star_counts = filtered_df.groupby('rating')['count'].sum().reset_index()
                        total_filtered = star_counts['count'].sum()
                        star_counts['percentage'] = (star_counts['count'] / total_filtered) * 100
                        star_counts['rating'] = star_counts['rating'].astype(str) # For categorical color mapping
                        star_counts['text'] = star_counts['percentage'].apply(lambda x: f"{x:.1f}%")

                        fig = px.bar(
                            star_counts,
                            x='percentage',
                            y='rating',
                            orientation='h',
                            title="Distribution of Star Ratings (Filtered)",
                            labels={'rating': 'Star Rating', 'percentage': 'Percentage of Reviews (%)'},
                            color='rating',
                            color_discrete_map=RATING_COLOR_MAP,
                            category_orders={'rating': ["5", "4", "3", "2", "1"]},
                                text='text',
                            template="plotly_white"
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True)

                    with col_time:
                        # 2. Reviews Over Time (Aggregated from filtered data)
                        time_counts = filtered_df.groupby('date')['count'].sum().reset_index().sort_values('date')
                        
                        fig = px.line(
                            time_counts,
                            x='date',
                            y='count',
                            title="Reviews Over Time (Filtered)",
                            labels={'date': '', 'count': 'Number of Reviews'},
                                markers=True,
                                template="plotly_white"
                        )
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True)

                    # 3. New Reviews by Star Rating (Monthly)
                    monthly_rating_df = filtered_df.groupby(['date', 'rating'])['count'].sum().reset_index()
                    monthly_rating_df['rating'] = monthly_rating_df['rating'].astype(str)
                    monthly_rating_df = monthly_rating_df.sort_values(['date', 'rating'])
                    
                    fig_rating = px.bar(
                        monthly_rating_df,
                        x='date',
                        y='count',
                        color='rating',
                        title="New Reviews by Star Rating per Month",
                        labels={'date': '', 'count': 'Number of Reviews', 'rating': 'Stars'},
                        color_discrete_map=RATING_COLOR_MAP,
                            category_orders={'rating': ["1", "2", "3", "4", "5"]},
                            template="plotly_white"
                    )
                    fig_rating.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_rating, use_container_width=True)

                    # 4. Source Charts
                    col_source1, col_source2 = st.columns(2)
                    
                    with col_source1:
                        # Line chart by source
                        monthly_source_df = filtered_df.groupby(['date', 'source'])['count'].sum().reset_index().sort_values('date')
                        fig_source = px.line(
                            monthly_source_df,
                            x='date',
                            y='count',
                            color='source',
                            title="Reviews by Source per Month",
                            labels={'date': '', 'count': 'Number of Reviews', 'source': 'Source'},
                                markers=True,
                                template="plotly_white"
                        )
                        fig_source.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_source, use_container_width=True)
                    
                    with col_source2:
                        # Pie chart by source
                        source_counts = filtered_df.groupby('source')['count'].sum().reset_index()
                        fig_pie = px.pie(
                            source_counts,
                            values='count',
                            names='source',
                            title="Review Sources Distribution",
                                template="plotly_white"
                        )
                        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No detailed review data available for the past 12 months.")

        # --- Section 3: Company Activity ---
        with st.container(border=True):
            st.header("Company Activity")
            reply_stats = analyze_reply_behavior(transparency_data)
            if reply_stats:
                col_act1, col_act2, col_act3, col_act4 = st.columns(4)
                col_act1.metric("Typical Reply Time", reply_stats.get('label', 'N/A'))
                
                avg_days = reply_stats.get('averageDaysToReply')
                col_act2.metric("Avg. Days to Reply", f"{avg_days:.1f}" if avg_days is not None else "N/A")
                
                col_act3.metric("Reply Rate (Negative, 1 & 2 Stars)", f"{reply_stats.get('replyPercentage', 0):.1f}%")
                
                replied = reply_stats.get('negativeReviewsWithRepliesCount', 0)
                total = reply_stats.get('totalNegativeReviewsCount', 0)
                col_act4.metric("Replied / Total (Negative, 1 & 2 Stars)", f"{replied} / {total}")
            else:
                st.warning("Could not find 'Company Activity' data. The following data keys were available:")
                # For debugging, let's see what keys are available
                if transparency_data and 'props' in transparency_data and 'pageProps' in transparency_data['props']:
                    st.json(list(transparency_data['props']['pageProps'].keys()))

        # --- Footer ---
        st.markdown("---")
        st.markdown(f"**Source:** [https://www.trustpilot.com/review/{domain}](https://www.trustpilot.com/review/{domain})", unsafe_allow_html=True)

# --- TAB 2: Domain Comparison ---
with tab2:
    st.markdown("<h2 style='font-size: 1.8rem;'>Compare Multiple Domains</h2>", unsafe_allow_html=True)
    
    selected_domains = st.multiselect(
        "Select domains to compare:", 
        options=PREDEFINED_DOMAINS,
        default=PREDEFINED_DOMAINS[:2] if len(PREDEFINED_DOMAINS) >= 2 else PREDEFINED_DOMAINS
    )
    
    custom_domains_input = st.text_input("Add custom domains (comma-separated):")
    
    if st.button("Run Comparison"):
        custom_domains = [d.strip() for d in custom_domains_input.split(",") if d.strip()]
        all_domains = list(dict.fromkeys(selected_domains + custom_domains))
        
        if not all_domains:
            st.warning("Please select at least one domain.")
        else:
            comparison_metrics = []
            all_star_dists = []
            all_reviews_over_time = []
            all_source_dists = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, domain in enumerate(all_domains):
                status_text.text(f"Fetching data for {domain}...")
                review_url = f"https://www.trustpilot.com/review/{domain}"
                transparency_url = f"{review_url}/transparency"
                
                try:
                    review_data = fetch_next_data(review_url)
                    transparency_data = fetch_next_data(transparency_url)
                    
                    if review_data and transparency_data:
                        # 1. Metrics
                        info = extract_business_info(review_data)
                        recent_count = calculate_recent_reviews_count(review_data)
                        reply_stats = analyze_reply_behavior(transparency_data)
                        
                        domain_stats = {
                            "Domain": domain,
                            "TrustScore": info.get('trustScore'),
                            "Total Reviews": info.get('numberOfReviews'),
                            "New Reviews (7d)": recent_count,
                            "Reply Rate (%)": reply_stats.get('replyPercentage', 0) if reply_stats else 0,
                            "Avg Reply Time (Days)": reply_stats.get('averageDaysToReply') if reply_stats else None
                        }
                        comparison_metrics.append(domain_stats)
                        
                        # 2. Star Distribution (All Time)
                        star_dist = extract_main_page_star_distribution(review_data)
                        if not star_dist.empty:
                            star_dist['Domain'] = domain
                            all_star_dists.append(star_dist)
                            
                        # 3. Reviews Over Time
                        time_dist = extract_reviews_over_time(transparency_data)
                        if not time_dist.empty:
                            time_dist['Domain'] = domain
                            all_reviews_over_time.append(time_dist)
                            
                        # 4. Source Distribution
                        source_dist = extract_source_distribution(transparency_data)
                        if not source_dist.empty:
                            source_dist['Domain'] = domain
                            all_source_dists.append(source_dist)
                            
                except Exception as e:
                    st.error(f"Error processing {domain}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(all_domains))
            
            status_text.empty()
            progress_bar.empty()
            
            if comparison_metrics:
                # --- Metrics Table ---
                st.subheader("Key Metrics Comparison")
                metrics_df = pd.DataFrame(comparison_metrics)
                st.dataframe(metrics_df, use_container_width=True)
                
                # --- Visualizations ---
                
                # 1. TrustScore Comparison
                col1, col2 = st.columns(2)
                with col1:
                    fig_ts = px.bar(
                        metrics_df, 
                        x='Domain', 
                        y='TrustScore', 
                        title="TrustScore Comparison",
                        color='Domain',
                        template="plotly_white"
                    )
                    fig_ts.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_ts, use_container_width=True)
                
                with col2:
                    fig_new = px.bar(
                        metrics_df, 
                        x='Domain', 
                        y='New Reviews (7d)', 
                        title="New Reviews (Last 7 Days)",
                        color='Domain',
                        template="plotly_white"
                    )
                    fig_new.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_new, use_container_width=True)

                # 2. Star Distribution Comparison
                if all_star_dists:
                    st.subheader("Star Rating Distribution (All Time)")
                    combined_star_df = pd.concat(all_star_dists)
                    combined_star_df['rating'] = combined_star_df['rating'].astype(str)
                    
                    fig_star = px.bar(
                        combined_star_df,
                        x='percentage',
                        y='rating',
                        color='Domain',
                        barmode='group',
                        orientation='h',
                        title="Star Rating Distribution by Domain",
                        labels={'percentage': 'Percentage (%)', 'rating': 'Stars'},
                        category_orders={'rating': ["5", "4", "3", "2", "1"]},
                        template="plotly_white"
                    )
                    fig_star.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_star, use_container_width=True)

                # 3. Reviews Over Time Comparison
                if all_reviews_over_time:
                    st.subheader("Reviews Over Time (Past 12 Months)")
                    combined_time_df = pd.concat(all_reviews_over_time)
                    
                    fig_time = px.line(
                        combined_time_df,
                        x='date',
                        y='count',
                        color='Domain',
                        title="Review Volume Trends",
                        markers=True,
                        template="plotly_white"
                    )
                    fig_time.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_time, use_container_width=True)

                # 4. Additional Comparisons
                col3, col4 = st.columns(2)
                
                with col3:
                    st.subheader("Reply Rate Comparison")
                    fig_reply = px.bar(
                        metrics_df,
                        x='Domain',
                        y='Reply Rate (%)',
                        color='Domain',
                        title="Negative Review Reply Rate",
                        template="plotly_white"
                    )
                    fig_reply.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_reply, use_container_width=True)
                
                with col4:
                    if all_source_dists:
                        st.subheader("Review Sources Breakdown")
                        combined_source_df = pd.concat(all_source_dists)
                        
                        fig_source = px.bar(
                            combined_source_df,
                            x='Domain',
                            y='count',
                            color='source',
                            title="Review Sources by Domain",
                            barmode='stack',
                            template="plotly_white"
                        )
                        fig_source.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_source, use_container_width=True)
            else:
                st.error("No data could be fetched for the selected domains.")
