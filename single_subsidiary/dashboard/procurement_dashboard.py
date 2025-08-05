#!/usr/bin/env python3
"""
ÖBB Procurement Consulting Intelligence Dashboard
A specialized Streamlit dashboard for analyzing consulting competitors in procurement data

Requirements:
pip install streamlit plotly pandas numpy openpyxl seaborn matplotlib

Run with: streamlit run procurement_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import re
from collections import Counter

# Custom Color Palette
CUSTOM_COLORS = {
    'primary': 'rgb(5,65,90)',        # Dark Blue
    'secondary': 'rgb(0,140,200)',     # Bright Blue
    'gray1': 'rgb(140,140,140)',       # Medium Gray
    'gray2': 'rgb(180,180,180)',       # Light Gray
    'gray3': 'rgb(150,150,150)',       # Gray
    'gray4': 'rgb(120,120,120)',       # Dark Gray
    'light_gray': 'rgb(230,230,230)',  # Very Light Gray
    'black': 'rgb(0,0,0)',             # Black
    'white': 'rgb(255,255,255)'        # White
}

# Define consulting companies for filtering
CONSULTING_COMPANIES = [
    'Accenture', 'Deloitte', 'PwC', 'KPMG', 'McKinsey', 'BCG', 'Bain',
    'Capgemini', 'IBM', 'EY', 'Roland Berger', 'Oliver Wyman', 'A.T. Kearney',
    'Booz Allen Hamilton', 'L.E.K.', 'Strategy&', 'Monitor Deloitte',
    'Nagarro', 'TCS', 'Infosys', 'Wipro', 'Cognizant', 'HCL', 'Tech Mahindra',
    'CGI', 'Atos', 'NTT Data', 'DXC Technology', 'Slalom', 'BearingPoint',
    'Sopra Steria', 'T-Systems', 'Fujitsu', 'NEC', 'Unisys', 'Horvath & Partner'
]

# Page configuration
st.set_page_config(
    page_title="ÖBB Single Subsidiary Procurement Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with McKinsey styling
st.markdown(f"""
<style>
.main-header {{
    font-size: 3rem;
    font-weight: bold;
    color: {CUSTOM_COLORS['primary']};
    text-align: center;
    margin-bottom: 2rem;
}}
.metric-card {{
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    border-left: 4px solid {CUSTOM_COLORS['primary']};
}}
.consulting-highlight {{
    background-color: {CUSTOM_COLORS['secondary']};
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
}}
.section-header {{
    color: {CUSTOM_COLORS['primary']};
    border-bottom: 2px solid {CUSTOM_COLORS['gray2']};
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}}
</style>
""", unsafe_allow_html=True)

def validate_csv_format(uploaded_df):
    """Validate that uploaded CSV has the correct format"""
    required_columns = [
        'Bezeichnung', 'Lieferant', 'Kategorie (CPV Hauptteil)', 
        'Bieter', 'Summe', 'Aktualisiert'
    ]
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in uploaded_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Check for minimum data requirements
    if len(uploaded_df) == 0:
        raise ValueError("CSV file is empty")
    
    # Check data types and format (basic validation)
    if uploaded_df['Summe'].dtype == 'object':
        # Check if Summe column has reasonable monetary values
        sample_values = uploaded_df['Summe'].dropna().head(10)
        if not any(str(val).replace('.','').replace(',','').replace(' ','').isdigit() for val in sample_values):
            raise ValueError("'Summe' column doesn't appear to contain valid monetary values")
    
    return True

def process_dataframe(df):
    """Process DataFrame with all cleaning and consulting identification"""
    # Clean and preprocess data
    df['Aktualisiert'] = pd.to_datetime(df['Aktualisiert'], format='%d.%m.%Y', errors='coerce')
    
    # Clean contract values
    df['Summe_Clean'] = df['Summe'].str.replace('.', '').str.replace(',', '.').str.extract(r'(\d+\.?\d*)')[0]
    df['Summe_Clean'] = pd.to_numeric(df['Summe_Clean'], errors='coerce')
    
    # Extract CPV category numbers
    df['CPV_Code'] = df['Kategorie (CPV Hauptteil)'].str.extract(r'(\d+)')[0]
    df['CPV_Category'] = df['Kategorie (CPV Hauptteil)'].str.replace(r'^\d+\s*', '', regex=True)
    
    # Company cleaning
    df['Lieferant_Clean'] = df['Lieferant'].str.strip()
    
    # Identify consulting companies
    df['Is_Consulting'] = df['Lieferant_Clean'].apply(
        lambda x: any(consulting in str(x) for consulting in CONSULTING_COMPANIES) if pd.notna(x) else False
    )
    
    # Extract consulting companies found in data
    consulting_matches = []
    for company in df['Lieferant_Clean'].dropna():
        for consulting in CONSULTING_COMPANIES:
            if consulting.lower() in company.lower():
                consulting_matches.append(company)
                break
    
    df['Consulting_Company'] = df['Lieferant_Clean'].apply(
        lambda x: x if x in consulting_matches else None
    )
    
    return df

@st.cache_data
def load_data():
    """Load and preprocess the procurement data"""
    import os
    
    # Try different possible paths for the data file
    possible_paths = [
        '../data/single_subsidiary_data.csv',  # Local development
        'single_subsidiary/data/single_subsidiary_data.csv',  # Streamlit Cloud
        'data/single_subsidiary_data.csv',  # Alternative path
        os.path.join(os.path.dirname(__file__), '../data/single_subsidiary_data.csv')  # Relative to script
    ]
    
    for path in possible_paths:
        try:
            if os.path.exists(path):
                df = pd.read_csv(path)
                return process_dataframe(df)
        except:
            continue
    
    # If no file found, show error
    st.error("❌ Data file 'single_subsidiary_data.csv' not found. Please run the single subsidiary scraper first or upload your own data using the sidebar.")
    return pd.DataFrame()

def get_custom_colors(n):
    """Get custom color palette for n items"""
    colors = [
        CUSTOM_COLORS['primary'], CUSTOM_COLORS['secondary'], CUSTOM_COLORS['gray1'],
        CUSTOM_COLORS['gray2'], CUSTOM_COLORS['gray3'], CUSTOM_COLORS['gray4'],
        CUSTOM_COLORS['light_gray'], CUSTOM_COLORS['black']
    ]
    return colors[:n] if n <= len(colors) else colors * (n // len(colors) + 1)

def create_market_overview(df):
    """Create balanced market overview with consulting insights"""
    if df.empty:
        return
    
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">📊 Market Overview</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Executive Summary KPIs
    st.markdown('<div class="section-header">🎯 Executive Summary</div>', unsafe_allow_html=True)
    
    # Calculate key metrics
    consulting_df = df[df['Is_Consulting'] == True]
    total_contracts = len(df)
    total_value = df['Summe_Clean'].sum()
    consulting_value = consulting_df['Summe_Clean'].sum()
    consulting_share = (consulting_value / total_value) * 100 if total_value > 0 else 0
    avg_competition = df['Bieter'].mean()
    
    # Executive KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {CUSTOM_COLORS['secondary']} 0%, {CUSTOM_COLORS['gray2']} 100%); 
                    padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; font-size: 2.5rem;">€{total_value/1000000:.1f}M</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">Total Market Size</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {CUSTOM_COLORS['secondary']} 0%, {CUSTOM_COLORS['gray2']} 100%); 
                    padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; font-size: 2.5rem;">{consulting_share:.1f}%</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">Consulting Market Share</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {CUSTOM_COLORS['secondary']} 0%, {CUSTOM_COLORS['gray2']} 100%); 
                    padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; font-size: 2.5rem;">{avg_competition:.1f}</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">Avg Competition</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Market concentration
        top5_value = df.groupby('Lieferant_Clean')['Summe_Clean'].sum().sort_values(ascending=False).head(5).sum()
        concentration = (top5_value / total_value) * 100 if total_value > 0 else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {CUSTOM_COLORS['secondary']} 0%, {CUSTOM_COLORS['gray2']} 100%); 
                    padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; font-size: 2.5rem;">{concentration:.0f}%</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">Top 5 Market Share</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Market composition analysis
    st.markdown('<div class="section-header">Market Composition</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top companies overall with consulting highlighted
        top_companies = df['Lieferant_Clean'].value_counts().head(15)
        
        # Create color map - consulting companies get McKinsey accent colors, others get gray
        colors = []
        for company in top_companies.index:
            if df[df['Lieferant_Clean'] == company]['Is_Consulting'].iloc[0]:
                colors.append(CUSTOM_COLORS['secondary'])  # Consulting companies in bright blue
            else:
                colors.append(CUSTOM_COLORS['gray1'])  # Non-consulting in gray
        
        fig_companies = px.bar(
            x=top_companies.values,
            y=top_companies.index,
            orientation='h',
            title="Top 15 Companies by Contract Count (Consulting Highlighted)",
            color_discrete_sequence=colors
        )
        fig_companies.update_layout(
            showlegend=False,
            height=500,
            title_font_color=CUSTOM_COLORS['primary']
        )
        st.plotly_chart(fig_companies, use_container_width=True)
    
    with col2:
        # Market share by value with consulting split
        consulting_value = consulting_df['Summe_Clean'].sum()
        non_consulting_value = total_value - consulting_value
        
        split_data = pd.DataFrame({
            'Type': ['Consulting', 'Non-Consulting'],
            'Value': [consulting_value, non_consulting_value]
        })
        
        fig_split = px.pie(
            split_data, 
            values='Value', 
            names='Type',
            title="Market Value: Consulting vs Non-Consulting",
            color_discrete_sequence=[CUSTOM_COLORS['secondary'], CUSTOM_COLORS['gray2']]
        )
        fig_split.update_layout(
            title_font_color=CUSTOM_COLORS['primary'],
            height=500
        )
        st.plotly_chart(fig_split, use_container_width=True)
    
    # Key consulting insights box
    if not consulting_df.empty:
        st.markdown('<div class="section-header">🎯 Consulting Market Insights</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            consulting_companies = consulting_df['Lieferant_Clean'].nunique()
            st.metric("Consulting Firms Active", f"{consulting_companies}")
        
        with col2:
            avg_consulting_value = consulting_df['Summe_Clean'].mean()
            avg_overall_value = df['Summe_Clean'].mean()
            premium = ((avg_consulting_value/avg_overall_value - 1) * 100) if avg_overall_value > 0 else 0
            st.metric("Consulting Premium", f"{premium:+.1f}%", "vs market average")
        
        with col3:
            consulting_share_value = (consulting_value / total_value) * 100
            st.metric("Consulting Market Share", f"{consulting_share_value:.1f}%")

def create_company_analysis(df):
    """Create detailed company analysis section"""
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">🏢 Company Analysis</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Company selection
    companies = sorted(df['Lieferant_Clean'].dropna().unique())
    selected_companies = st.multiselect(
        "Select companies to analyze:",
        companies,
        default=companies[:10] if len(companies) > 10 else companies[:5],
        key="company_selector"
    )
    
    if not selected_companies:
        st.warning("Please select at least one company to analyze.")
        return
    
    # Filter data for selected companies
    company_df = df[df['Lieferant_Clean'].isin(selected_companies)]
    
    # Company metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Contract count by company
        contract_counts = company_df.groupby('Lieferant_Clean').size().sort_values(ascending=False)
        fig_contracts = px.bar(
            x=contract_counts.values,
            y=contract_counts.index,
            orientation='h',
            title="Number of Contracts by Company",
            labels={'x': 'Number of Contracts', 'y': 'Company'}
        )
        fig_contracts.update_layout(height=400)
        st.plotly_chart(fig_contracts, use_container_width=True)
    
    with col2:
        # Total value by company
        value_by_company = company_df.groupby('Lieferant_Clean')['Summe_Clean'].sum().sort_values(ascending=False)
        fig_value = px.bar(
            x=value_by_company.values,
            y=value_by_company.index,
            orientation='h',
            title="Total Contract Value by Company",
            labels={'x': 'Total Value (€)', 'y': 'Company'}
        )
        fig_value.update_layout(height=400)
        st.plotly_chart(fig_value, use_container_width=True)
    
    # Detailed company table
    st.subheader("📋 Company Performance Summary")
    company_summary = company_df.groupby('Lieferant_Clean').agg({
        'Summe_Clean': ['count', 'sum', 'mean', 'max'],
        'Bieter': 'mean',
        'Aktualisiert': ['min', 'max']
    }).round(2)
    
    company_summary.columns = ['Contracts', 'Total Value (€)', 'Avg Value (€)', 'Max Value (€)', 
                             'Avg Competitors', 'First Contract', 'Last Contract']
    company_summary = company_summary.sort_values('Total Value (€)', ascending=False)
    
    st.dataframe(company_summary, use_container_width=True)

def create_market_share_analysis(df):
    """Create market share analysis with McKinsey colors and consulting highlights"""
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">📈 Market Share Analysis</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Market share by contract count
        top_companies_count = df['Lieferant_Clean'].value_counts().head(12)
        colors = get_custom_colors(len(top_companies_count))
        
        fig_pie_count = px.pie(
            values=top_companies_count.values,
            names=top_companies_count.index,
            title="Market Share by Contract Count (Top 12)",
            color_discrete_sequence=colors
        )
        fig_pie_count.update_layout(title_font_color=CUSTOM_COLORS['primary'])
        st.plotly_chart(fig_pie_count, use_container_width=True)
    
    with col2:
        # Market share by value
        top_companies_value = df.groupby('Lieferant_Clean')['Summe_Clean'].sum().sort_values(ascending=False).head(12)
        colors = get_custom_colors(len(top_companies_value))
        
        fig_pie_value = px.pie(
            values=top_companies_value.values,
            names=top_companies_value.index,
            title="Market Share by Value (Top 12)",
            color_discrete_sequence=colors
        )
        fig_pie_value.update_layout(title_font_color=CUSTOM_COLORS['primary'])
        st.plotly_chart(fig_pie_value, use_container_width=True)
    
    # Contract value filter for market share analysis
    st.subheader("🔧 Filter by Contract Value")
    
    # Preset value range options
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("All Contracts", key="market_all", type="secondary"):
            st.session_state.market_filter = "all"
    with col2:
        if st.button("Small (€0-50K)", key="market_small", type="secondary"):
            st.session_state.market_filter = "small"
    with col3:
        if st.button("Medium (€50K-500K)", key="market_medium", type="secondary"):
            st.session_state.market_filter = "medium"
    with col4:
        if st.button("Large (€500K-2M)", key="market_large", type="secondary"):
            st.session_state.market_filter = "large"
    with col5:
        if st.button("XL (€2M+)", key="market_xl", type="secondary"):
            st.session_state.market_filter = "xl"
    
    # Initialize filter if not set
    if 'market_filter' not in st.session_state:
        st.session_state.market_filter = "all"
    
    # Show current selection
    filter_labels = {
        "all": "All Contracts",
        "small": "Small (€0-50K)", 
        "medium": "Medium (€50K-500K)",
        "large": "Large (€500K-2M)",
        "xl": "XL (€2M+)"
    }
    st.info(f"**Current filter:** {filter_labels[st.session_state.market_filter]}")
    
    # Apply filter based on selection and add adaptive slider
    if st.session_state.market_filter == "small":
        range_min, range_max = 0, 50000
        min_value, max_value = st.slider(
            "Fine-tune Small contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=1000,
            key="market_small_slider",
            format="€%d"
        )
    elif st.session_state.market_filter == "medium":
        range_min, range_max = 50000, 500000
        min_value, max_value = st.slider(
            "Fine-tune Medium contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=5000,
            key="market_medium_slider",
            format="€%d"
        )
    elif st.session_state.market_filter == "large":
        range_min, range_max = 500000, 2000000
        min_value, max_value = st.slider(
            "Fine-tune Large contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=25000,
            key="market_large_slider",
            format="€%d"
        )
    elif st.session_state.market_filter == "xl":
        range_min = 2000000
        range_max = int(df['Summe_Clean'].max())
        min_value, max_value = st.slider(
            "Fine-tune XL contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=100000,
            key="market_xl_slider",
            format="€%d"
        )
    else:
        min_value, max_value = 0, float('inf')
    
    # Apply filter and show filtered results if different
    if st.session_state.market_filter != "all":
        df_filtered = df[(df['Summe_Clean'] >= min_value) & (df['Summe_Clean'] <= max_value)]
        if not df_filtered.empty:
            st.info(f"Showing results for {len(df_filtered):,} contracts (filtered from {len(df):,})")
            
            col1_f, col2_f = st.columns(2)
            
            with col1_f:
                top_companies_count_f = df_filtered['Lieferant_Clean'].value_counts().head(12)
                colors = get_custom_colors(len(top_companies_count_f))
                
                fig_pie_count_f = px.pie(
                    values=top_companies_count_f.values,
                    names=top_companies_count_f.index,
                    title="Filtered: Market Share by Contract Count",
                    color_discrete_sequence=colors
                )
                fig_pie_count_f.update_layout(title_font_color=CUSTOM_COLORS['primary'])
                st.plotly_chart(fig_pie_count_f, use_container_width=True)
            
            with col2_f:
                top_companies_value_f = df_filtered.groupby('Lieferant_Clean')['Summe_Clean'].sum().sort_values(ascending=False).head(12)
                colors = get_custom_colors(len(top_companies_value_f))
                
                fig_pie_value_f = px.pie(
                    values=top_companies_value_f.values,
                    names=top_companies_value_f.index,
                    title="Filtered: Market Share by Value",
                    color_discrete_sequence=colors
                )
                fig_pie_value_f.update_layout(title_font_color=CUSTOM_COLORS['primary'])
                st.plotly_chart(fig_pie_value_f, use_container_width=True)
        else:
            st.warning("No data available for the selected value range.")
    
    # Market concentration metrics
    st.markdown('<div class="section-header">🎯 Market Concentration</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    total_contracts = len(df)
    total_value = df['Summe_Clean'].sum()
    consulting_df = df[df['Is_Consulting'] == True]
    
    with col1:
        # Top 5 companies concentration
        top5_contracts = df['Lieferant_Clean'].value_counts().head(5).sum()
        concentration_contracts = (top5_contracts / total_contracts) * 100
        st.metric("Top 5 Companies", f"{concentration_contracts:.1f}%", "of contracts")
    
    with col2:
        top5_value = df.groupby('Lieferant_Clean')['Summe_Clean'].sum().sort_values(ascending=False).head(5).sum()
        concentration_value = (top5_value / total_value) * 100
        st.metric("Top 5 Companies", f"{concentration_value:.1f}%", "of value")
    
    with col3:
        # Consulting concentration
        if not consulting_df.empty:
            consulting_share = (len(consulting_df) / total_contracts) * 100
            st.metric("Consulting Share", f"{consulting_share:.1f}%", "of market")
        else:
            st.metric("Consulting Share", "0.0%", "of market")

def create_category_analysis(df):
    """Create category analysis with consulting insights"""
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">🏷️ Category Analysis</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Analysis controls
    st.subheader("🔧 Analysis Controls")
    top_n = st.selectbox(
        "Number of top categories to display:",
        [5, 8, 10, 15, 20],
        index=2,  # Default to 10
        key="category_top_n"
    )
    
    # Top categories with McKinsey colors
    col1, col2 = st.columns(2)
    
    with col1:
        category_counts = df['CPV_Category'].value_counts().head(top_n)
        colors = get_custom_colors(len(category_counts))
        
        fig_cat = px.bar(
            x=category_counts.values,
            y=category_counts.index,
            orientation='h',
            title=f"Top {top_n} Categories by Contract Count",
            color_discrete_sequence=colors
        )
        fig_cat.update_layout(
            height=500,
            showlegend=False,
            title_font_color=CUSTOM_COLORS['primary']
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        category_values = df.groupby('CPV_Category')['Summe_Clean'].sum().sort_values(ascending=False).head(top_n)
        colors = get_custom_colors(len(category_values))
        
        fig_cat_val = px.bar(
            x=category_values.values,
            y=category_values.index,
            orientation='h',
            title=f"Top {top_n} Categories by Value",
            color_discrete_sequence=colors
        )
        fig_cat_val.update_layout(
            height=500,
            showlegend=False,
            title_font_color=CUSTOM_COLORS['primary']
        )
        st.plotly_chart(fig_cat_val, use_container_width=True)
    
    # Consulting category analysis
    consulting_df = df[df['Is_Consulting'] == True]
    if not consulting_df.empty:
        st.markdown('<div class="section-header">🎯 Consulting Category Breakdown</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            consulting_categories = consulting_df['CPV_Category'].value_counts().head(8)
            colors = get_custom_colors(len(consulting_categories))
            
            fig_consulting_cat = px.bar(
                x=consulting_categories.values,
                y=consulting_categories.index,
                orientation='h',
                title="Top Categories for Consulting Firms",
                color_discrete_sequence=colors
            )
            fig_consulting_cat.update_layout(
                height=400,
                showlegend=False,
                title_font_color=CUSTOM_COLORS['primary']
            )
            st.plotly_chart(fig_consulting_cat, use_container_width=True)
        
        with col2:
            # Consulting vs non-consulting by top categories
            top_categories = df['CPV_Category'].value_counts().head(6).index
            category_comparison = []
            
            for cat in top_categories:
                cat_df = df[df['CPV_Category'] == cat]
                consulting_count = len(cat_df[cat_df['Is_Consulting'] == True])
                total_count = len(cat_df)
                category_comparison.append({
                    'Category': cat[:30] + '...' if len(cat) > 30 else cat,
                    'Consulting': consulting_count,
                    'Non-Consulting': total_count - consulting_count
                })
            
            comparison_df = pd.DataFrame(category_comparison)
            
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(
                name='Consulting',
                x=comparison_df['Category'],
                y=comparison_df['Consulting'],
                marker_color=CUSTOM_COLORS['secondary']
            ))
            fig_comparison.add_trace(go.Bar(
                name='Non-Consulting',
                x=comparison_df['Category'],
                y=comparison_df['Non-Consulting'],
                marker_color=CUSTOM_COLORS['gray2']
            ))
            
            fig_comparison.update_layout(
                title="Consulting vs Non-Consulting by Category",
                barmode='stack',
                height=400,
                title_font_color=CUSTOM_COLORS['primary']
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Category selection for detailed analysis
    st.markdown('<div class="section-header">🔍 Category Deep Dive</div>', unsafe_allow_html=True)
    selected_category = st.selectbox(
        "Select a category to analyze:",
        df['CPV_Category'].value_counts().index[:20]
    )
    
    if selected_category:
        category_df = df[df['CPV_Category'] == selected_category]
        category_consulting = category_df[category_df['Is_Consulting'] == True]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Contracts", len(category_df))
        with col2:
            st.metric("Total Value", f"€{category_df['Summe_Clean'].sum():,.0f}")
        with col3:
            consulting_in_cat = len(category_consulting)
            consulting_pct = (consulting_in_cat / len(category_df)) * 100 if len(category_df) > 0 else 0
            st.metric("Consulting Contracts", f"{consulting_in_cat}", f"{consulting_pct:.1f}%")
        with col4:
            st.metric("Unique Suppliers", category_df['Lieferant_Clean'].nunique())
        
        # Top performers in category with consulting highlight
        category_leaders = category_df.groupby('Lieferant_Clean').agg({
            'Summe_Clean': ['count', 'sum'],
            'Is_Consulting': 'first'
        }).round(2)
        category_leaders.columns = ['Contracts', 'Total Value', 'Is_Consulting']
        category_leaders = category_leaders.sort_values('Total Value', ascending=False).head(10)
        
        st.subheader(f"Top Performers in {selected_category}")
        
        # Style the dataframe to highlight consulting companies
        def highlight_consulting(val, is_consulting):
            if is_consulting:
                return 'background-color: #f95d6a; color: white'
            return ''
        
        # Create a copy for styling without the Is_Consulting column
        display_df = category_leaders.drop('Is_Consulting', axis=1).copy()
        
        # Apply styling based on the original consulting flags
        styled_df = display_df.style.apply(
            lambda row: [highlight_consulting(val, category_leaders.loc[row.name, 'Is_Consulting']) 
                        for val in row], axis=1
        )
        st.dataframe(styled_df, use_container_width=True)
        st.caption("🎯 Consulting companies highlighted in red")



def create_company_deep_dive(df):
    """Create detailed company analysis with McKinsey styling"""
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">🔬 Company Deep Dive</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Company selector
    companies = sorted(df['Lieferant_Clean'].dropna().unique())
    selected_company = st.selectbox("Select a company for detailed analysis:", companies)
    
    if not selected_company:
        return
    
    company_data = df[df['Lieferant_Clean'] == selected_company]
    is_consulting = company_data['Is_Consulting'].iloc[0] if len(company_data) > 0 else False
    
    # Company overview with consulting indicator
    if is_consulting:
        st.markdown(f'<div class="consulting-highlight">🎯 {selected_company} - CONSULTING FIRM</div>', unsafe_allow_html=True)
        st.write("")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Contracts", len(company_data))
    with col2:
        total_value = company_data['Summe_Clean'].sum()
        st.metric("Total Value", f"€{total_value:,.0f}")
    with col3:
        avg_value = company_data['Summe_Clean'].mean()
        market_avg = df['Summe_Clean'].mean()
        premium = ((avg_value/market_avg - 1) * 100) if market_avg > 0 else 0
        st.metric("Average Value", f"€{avg_value:,.0f}", f"{premium:+.1f}% vs market")
    with col4:
        market_share = (len(company_data) / len(df)) * 100
        st.metric("Market Share", f"{market_share:.1f}%")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Company performance over time
        if not company_data[company_data['Aktualisiert'].notna()].empty:
            company_time = company_data[company_data['Aktualisiert'].notna()].copy()
            company_time.loc[:, 'YearMonth'] = company_time['Aktualisiert'].dt.to_period('M')
            monthly_performance = company_time.groupby('YearMonth').agg({
                'Summe_Clean': ['count', 'sum']
            })
            monthly_performance.columns = ['Contracts', 'Value']
            
            fig_performance = make_subplots(specs=[[{"secondary_y": True}]])
            fig_performance.add_trace(
                go.Scatter(
                    x=monthly_performance.index.astype(str), 
                    y=monthly_performance['Contracts'], 
                    name="Contracts",
                    line=dict(color=CUSTOM_COLORS['primary'])
                ),
                secondary_y=False,
            )
            fig_performance.add_trace(
                go.Scatter(
                    x=monthly_performance.index.astype(str), 
                    y=monthly_performance['Value'], 
                    name="Value",
                    line=dict(color=CUSTOM_COLORS['secondary'])
                ),
                secondary_y=True,
            )
            fig_performance.update_yaxes(title_text="Number of Contracts", secondary_y=False)
            fig_performance.update_yaxes(title_text="Contract Value (€)", secondary_y=True)
            fig_performance.update_layout(
                title=f"{selected_company} - Performance Over Time",
                title_font_color=CUSTOM_COLORS['primary']
            )
            
            st.plotly_chart(fig_performance, use_container_width=True)
    
    with col2:
        # Company's categories
        company_categories = company_data['CPV_Category'].value_counts().head(8)
        colors = get_custom_colors(len(company_categories))
        
        fig_cat = px.bar(
            x=company_categories.values,
            y=company_categories.index,
            orientation='h',
            title=f"{selected_company} - Top Categories",
            color_discrete_sequence=colors
        )
        fig_cat.update_layout(
            showlegend=False,
            title_font_color=CUSTOM_COLORS['primary']
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    # Competition analysis
    st.markdown('<div class="section-header">Competition Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        avg_competition = company_data['Bieter'].mean()
        market_avg_competition = df['Bieter'].mean()
        st.metric("Avg Competition Faced", f"{avg_competition:.1f}", 
                 f"{avg_competition - market_avg_competition:+.1f} vs market")
    
    with col2:
        # Win rate approximation (assuming they won all contracts they appear in)
        total_bids_estimated = company_data['Bieter'].sum()  # Rough estimate
        win_rate = (len(company_data) / total_bids_estimated) * 100 if total_bids_estimated > 0 else 0
        st.metric("Estimated Win Rate", f"{win_rate:.1f}%")
    
    # Recent contracts
    st.markdown('<div class="section-header">Recent Contracts</div>', unsafe_allow_html=True)
    recent_contracts = company_data.nlargest(10, 'Aktualisiert')[
        ['Bezeichnung', 'Summe', 'Kategorie (CPV Hauptteil)', 'Bieter', 'Aktualisiert']
    ]
    st.dataframe(recent_contracts, use_container_width=True)

def create_consulting_competitive_analysis(df):
    """Create consulting-specific competitive analysis"""
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">🎯 Consulting Competitive Landscape</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    consulting_df = df[df['Is_Consulting'] == True]
    
    if consulting_df.empty:
        st.warning("No consulting companies found in the data.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Contract value distribution for consulting firms
        consulting_summary = consulting_df.groupby('Lieferant_Clean').agg({
            'Summe_Clean': ['count', 'sum', 'mean'],
            'Bieter': 'mean'
        }).round(2)
        
        consulting_summary.columns = ['Contracts', 'Total Value (€)', 'Avg Value (€)', 'Avg Competition']
        consulting_summary = consulting_summary.sort_values('Total Value (€)', ascending=False)
        
        # Value by company chart
        top_consulting_value = consulting_summary.head(10)['Total Value (€)']
        colors = get_custom_colors(len(top_consulting_value))
        
        fig_value = px.bar(
            x=top_consulting_value.values,
            y=top_consulting_value.index,
            orientation='h',
            title="Total Contract Value by Consulting Firm",
            color_discrete_sequence=colors
        )
        fig_value.update_layout(
            showlegend=False,
            height=500,
            title_font_color=CUSTOM_COLORS['primary']
        )
        st.plotly_chart(fig_value, use_container_width=True)
    
    with col2:
        # Market positioning analysis - more intuitive visualization
        # Create competitiveness score: higher contract value + lower competition = better position
        consulting_summary_viz = consulting_summary.reset_index()
        
        # Normalize values for better comparison (0-100 scale)
        max_value = consulting_summary_viz['Avg Value (€)'].max()
        max_competition = consulting_summary_viz['Avg Competition'].max()
        
        consulting_summary_viz['Value Score'] = (consulting_summary_viz['Avg Value (€)'] / max_value) * 100
        consulting_summary_viz['Competition Score'] = 100 - ((consulting_summary_viz['Avg Competition'] / max_competition) * 100)
        
        # Create quadrant analysis chart
        fig_position = px.scatter(
            consulting_summary_viz,
            x='Competition Score',
            y='Value Score', 
            size='Contracts',
            hover_name='Lieferant_Clean',
            hover_data={
                'Avg Value (€)': ':,.0f',
                'Avg Competition': ':.1f',
                'Contracts': True,
                'Competition Score': False,
                'Value Score': False
            },
            title="Market Positioning Analysis",
            color='Total Value (€)',
            color_continuous_scale=['lightcoral', 'gold', 'lightgreen'],
            labels={
                'Competition Score': 'Lower Competition →',
                'Value Score': 'Higher Contract Value →'
            }
        )
        
        # Add quadrant lines
        fig_position.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
        fig_position.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add quadrant labels
        fig_position.add_annotation(x=25, y=75, text="High Value<br>High Competition", 
                                   showarrow=False, font=dict(size=10, color="gray"))
        fig_position.add_annotation(x=75, y=75, text="Sweet Spot<br>High Value, Low Competition", 
                                   showarrow=False, font=dict(size=10, color="darkgreen"))
        fig_position.add_annotation(x=25, y=25, text="Challenging<br>Low Value, High Competition", 
                                   showarrow=False, font=dict(size=10, color="darkred"))
        fig_position.add_annotation(x=75, y=25, text="Low Value<br>Low Competition", 
                                   showarrow=False, font=dict(size=10, color="gray"))
        
        fig_position.update_layout(
            height=500,
            title_font_color=CUSTOM_COLORS['primary'],
            xaxis=dict(range=[0, 100]),
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig_position, use_container_width=True)
    
    # Contract value filter for consulting analysis
    st.subheader("🔧 Filter by Contract Value")
    
    # Preset value range options
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("All Contracts", key="consulting_all", type="secondary"):
            st.session_state.consulting_filter = "all"
    with col2:
        if st.button("Small (€0-50K)", key="consulting_small", type="secondary"):
            st.session_state.consulting_filter = "small"
    with col3:
        if st.button("Medium (€50K-500K)", key="consulting_medium", type="secondary"):
            st.session_state.consulting_filter = "medium"
    with col4:
        if st.button("Large (€500K-2M)", key="consulting_large", type="secondary"):
            st.session_state.consulting_filter = "large"
    with col5:
        if st.button("XL (€2M+)", key="consulting_xl", type="secondary"):
            st.session_state.consulting_filter = "xl"
    
    # Initialize filter if not set
    if 'consulting_filter' not in st.session_state:
        st.session_state.consulting_filter = "all"
    
    # Show current selection
    filter_labels = {
        "all": "All Contracts",
        "small": "Small (€0-50K)", 
        "medium": "Medium (€50K-500K)",
        "large": "Large (€500K-2M)",
        "xl": "XL (€2M+)"
    }
    st.info(f"**Current filter:** {filter_labels[st.session_state.consulting_filter]}")
    
    # Apply filter based on selection and add adaptive slider
    if st.session_state.consulting_filter == "small":
        range_min, range_max = 0, 50000
        min_value, max_value = st.slider(
            "Fine-tune Small contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=1000,
            key="consulting_small_slider",
            format="€%d"
        )
    elif st.session_state.consulting_filter == "medium":
        range_min, range_max = 50000, 500000
        min_value, max_value = st.slider(
            "Fine-tune Medium contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=5000,
            key="consulting_medium_slider",
            format="€%d"
        )
    elif st.session_state.consulting_filter == "large":
        range_min, range_max = 500000, 2000000
        min_value, max_value = st.slider(
            "Fine-tune Large contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=25000,
            key="consulting_large_slider",
            format="€%d"
        )
    elif st.session_state.consulting_filter == "xl":
        range_min = 2000000
        range_max = int(consulting_df['Summe_Clean'].max())
        min_value, max_value = st.slider(
            "Fine-tune XL contracts range:",
            min_value=range_min,
            max_value=range_max,
            value=(range_min, range_max),
            step=100000,
            key="consulting_xl_slider",
            format="€%d"
        )
    else:
        min_value, max_value = 0, float('inf')
    
    # Apply filter and show filtered results if different
    if st.session_state.consulting_filter != "all":
        consulting_filtered = consulting_df[(consulting_df['Summe_Clean'] >= min_value) & (consulting_df['Summe_Clean'] <= max_value)]
        if not consulting_filtered.empty:
            st.info(f"Showing results for {len(consulting_filtered):,} consulting contracts (filtered from {len(consulting_df):,})")
            
            # Recalculate summary for filtered data
            consulting_summary_filtered = consulting_filtered.groupby('Lieferant_Clean').agg({
                'Summe_Clean': ['count', 'sum', 'mean'],
                'Bieter': 'mean'
            }).round(2)
            
            consulting_summary_filtered.columns = ['Contracts', 'Total Value (€)', 'Avg Value (€)', 'Avg Competition']
            consulting_summary_filtered = consulting_summary_filtered.sort_values('Total Value (€)', ascending=False)
            
            col1_f, col2_f = st.columns(2)
            
            with col1_f:
                top_consulting_value_f = consulting_summary_filtered.head(10)['Total Value (€)']
                colors = get_custom_colors(len(top_consulting_value_f))
                
                fig_value_f = px.bar(
                    x=top_consulting_value_f.values,
                    y=top_consulting_value_f.index,
                    orientation='h',
                    title="Filtered: Total Contract Value by Consulting Firm",
                    color_discrete_sequence=colors
                )
                fig_value_f.update_layout(
                    showlegend=False,
                    height=500,
                    title_font_color=CUSTOM_COLORS['primary']
                )
                st.plotly_chart(fig_value_f, use_container_width=True)
            
            with col2_f:
                # Market positioning analysis for filtered data - more intuitive visualization
                consulting_summary_viz_f = consulting_summary_filtered.reset_index()
                
                # Normalize values for better comparison (0-100 scale)
                max_value_f = consulting_summary_viz_f['Avg Value (€)'].max()
                max_competition_f = consulting_summary_viz_f['Avg Competition'].max()
                
                consulting_summary_viz_f['Value Score'] = (consulting_summary_viz_f['Avg Value (€)'] / max_value_f) * 100
                consulting_summary_viz_f['Competition Score'] = 100 - ((consulting_summary_viz_f['Avg Competition'] / max_competition_f) * 100)
                
                # Create quadrant analysis chart
                fig_position_f = px.scatter(
                    consulting_summary_viz_f,
                    x='Competition Score',
                    y='Value Score', 
                    size='Contracts',
                    hover_name='Lieferant_Clean',
                    hover_data={
                        'Avg Value (€)': ':,.0f',
                        'Avg Competition': ':.1f',
                        'Contracts': True,
                        'Competition Score': False,
                        'Value Score': False
                    },
                    title="Filtered: Market Positioning Analysis",
                    color='Total Value (€)',
                    color_continuous_scale=['lightcoral', 'gold', 'lightgreen'],
                    labels={
                        'Competition Score': 'Lower Competition →',
                        'Value Score': 'Higher Contract Value →'
                    }
                )
                
                # Add quadrant lines
                fig_position_f.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
                fig_position_f.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
                
                # Add quadrant labels
                fig_position_f.add_annotation(x=25, y=75, text="High Value<br>High Competition", 
                                           showarrow=False, font=dict(size=10, color="gray"))
                fig_position_f.add_annotation(x=75, y=75, text="Sweet Spot<br>High Value, Low Competition", 
                                           showarrow=False, font=dict(size=10, color="darkgreen"))
                fig_position_f.add_annotation(x=25, y=25, text="Challenging<br>Low Value, High Competition", 
                                           showarrow=False, font=dict(size=10, color="darkred"))
                fig_position_f.add_annotation(x=75, y=25, text="Low Value<br>Low Competition", 
                                           showarrow=False, font=dict(size=10, color="gray"))
                
                fig_position_f.update_layout(
                    height=500,
                    title_font_color=CUSTOM_COLORS['primary'],
                    xaxis=dict(range=[0, 100]),
                    yaxis=dict(range=[0, 100])
                )
                st.plotly_chart(fig_position_f, use_container_width=True)
            
            st.subheader("📋 Filtered Consulting Firm Performance")
            st.dataframe(consulting_summary_filtered, use_container_width=True)
        else:
            st.warning("No consulting companies found in the selected value range.")
    else:
        # Detailed consulting table
        st.subheader("📋 Consulting Firm Performance")
        st.dataframe(consulting_summary, use_container_width=True)

def create_consulting_categories(df):
    """Create consulting category analysis"""
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">📊 Consulting Service Categories</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    consulting_df = df[df['Is_Consulting'] == True]
    
    if consulting_df.empty:
        st.warning("No consulting companies found in the data.")
        return
    
    # Top categories for consulting
    consulting_categories = consulting_df['CPV_Category'].value_counts().head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        colors = get_custom_colors(len(consulting_categories))
        fig_cat = px.bar(
            x=consulting_categories.values,
            y=consulting_categories.index,
            orientation='h',
            title="Top Service Categories for Consulting",
            color_discrete_sequence=colors
        )
        fig_cat.update_layout(
            showlegend=False,
            height=500,
            title_font_color=CUSTOM_COLORS['primary']
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        # Category value analysis
        category_values = consulting_df.groupby('CPV_Category')['Summe_Clean'].sum().sort_values(ascending=False).head(10)
        colors = get_custom_colors(len(category_values))
        
        fig_cat_val = px.bar(
            x=category_values.values,
            y=category_values.index,
            orientation='h',
            title="Highest Value Categories for Consulting",
            color_discrete_sequence=colors
        )
        fig_cat_val.update_layout(
            showlegend=False,
            height=500,
            title_font_color=CUSTOM_COLORS['primary']
        )
        st.plotly_chart(fig_cat_val, use_container_width=True)

def create_timeline_analysis(df):
    """Create timeline analysis with consulting overlay"""
    # Add Horvath & Partners logo to top right
    col1, col2 = st.columns([3, 1])
    with col2:
        st.image("horvath-partners.jpg", width=400)
    
    st.markdown('<div class="main-header">📅 Market Timeline Analysis</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter out invalid dates
    df_time = df[df['Aktualisiert'].notna()].copy()
    
    if df_time.empty:
        st.warning("No valid date data available for timeline analysis.")
        return
    
    # Date range selector
    min_date = df_time['Aktualisiert'].min().date()
    max_date = df_time['Aktualisiert'].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", min_date)
    with col2:
        end_date = st.date_input("End Date", max_date)
    
    # Filter by date range
    mask = (df_time['Aktualisiert'].dt.date >= start_date) & (df_time['Aktualisiert'].dt.date <= end_date)
    df_filtered = df_time[mask]
    
    if df_filtered.empty:
        st.warning("No data available for the selected date range.")
        return
    
    # Monthly trends with consulting overlay
    df_filtered.loc[:, 'YearMonth'] = df_filtered['Aktualisiert'].dt.to_period('M')
    
    # Overall monthly trends
    monthly_all = df_filtered.groupby('YearMonth').agg({
        'Summe_Clean': ['count', 'sum']
    })
    monthly_all.columns = ['Total_Contracts', 'Total_Value']
    
    # Consulting monthly trends
    consulting_monthly = df_filtered[df_filtered['Is_Consulting'] == True].groupby('YearMonth').agg({
        'Summe_Clean': ['count', 'sum']
    })
    consulting_monthly.columns = ['Consulting_Contracts', 'Consulting_Value']
    
    # Combine data
    monthly_combined = monthly_all.join(consulting_monthly, how='left').fillna(0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Contract count trends
        fig_contracts = go.Figure()
        fig_contracts.add_trace(go.Scatter(
            x=monthly_combined.index.astype(str),
            y=monthly_combined['Total_Contracts'],
            name='Total Market',
            line=dict(color=CUSTOM_COLORS['primary'], width=3)
        ))
        fig_contracts.add_trace(go.Scatter(
            x=monthly_combined.index.astype(str),
            y=monthly_combined['Consulting_Contracts'],
            name='Consulting',
            line=dict(color=CUSTOM_COLORS['secondary'], width=2)
        ))
        fig_contracts.update_layout(
            title="Monthly Contract Trends",
            title_font_color=CUSTOM_COLORS['primary'],
            height=400
        )
        st.plotly_chart(fig_contracts, use_container_width=True)
    
    with col2:
        # Value trends
        fig_values = go.Figure()
        fig_values.add_trace(go.Scatter(
            x=monthly_combined.index.astype(str),
            y=monthly_combined['Total_Value'],
            name='Total Market',
            line=dict(color=CUSTOM_COLORS['primary'], width=3)
        ))
        fig_values.add_trace(go.Scatter(
            x=monthly_combined.index.astype(str),
            y=monthly_combined['Consulting_Value'],
            name='Consulting',
            line=dict(color=CUSTOM_COLORS['secondary'], width=2)
        ))
        fig_values.update_layout(
            title="Monthly Value Trends",
            title_font_color=CUSTOM_COLORS['primary'],
            height=400
        )
        st.plotly_chart(fig_values, use_container_width=True)

def main():
    """Main dashboard function with balanced market and consulting view"""
    # Load original data
    original_df = load_data()
    
    if original_df.empty:
        st.stop()
    
    # Initialize session state for data management
    if 'using_uploaded_data' not in st.session_state:
        st.session_state.using_uploaded_data = False
        st.session_state.uploaded_df = None
    
    # Data selection will happen after all session state management
    
    # Sidebar navigation - balanced approach
    # Add Horvath & Partners logo to sidebar - centered
    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:
        st.image("horvath-partners.png", width=200)
    st.sidebar.markdown('<h1 style="text-align: center;">📊 Dashboard</h1>', unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # Navigation at the top
    page = st.sidebar.selectbox(
        "Choose Analysis:",
        [
            "Market Overview",
            "Market Share Analysis",
            "Competitive Intelligence", 
            "Category Analysis",
            "Timeline Analysis",
            "Company Deep Dive"
        ]
    )
    
    # Use uploaded data if available, otherwise use original (after all session state management)
    df = st.session_state.uploaded_df if (st.session_state.using_uploaded_data and st.session_state.uploaded_df is not None) else original_df
    
    # Data filters - right after navigation
    st.sidebar.header("🔧 Filters")
    
    # Company type filter
    company_filter = st.sidebar.selectbox(
        "Company Focus:",
        ["All Companies", "Consulting Only", "Non-Consulting Only"],
        index=0
    )
    
    # Apply company type filter
    if company_filter == "Consulting Only":
        df_base_filtered = df[df['Is_Consulting'] == True]
    elif company_filter == "Non-Consulting Only":
        df_base_filtered = df[df['Is_Consulting'] == False]
    else:
        df_base_filtered = df
    
    st.sidebar.markdown("---")
    
    # Upload CSV section - compact
    with st.sidebar.expander("📁 Upload New Data"):
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            help="Upload CSV with same format as original data"
        )
    
    # Handle file upload
    if uploaded_file is not None:
        try:
            # Read uploaded file
            uploaded_df = pd.read_csv(uploaded_file)
            
            # Validate format
            validate_csv_format(uploaded_df)
            
            # Process the uploaded data
            processed_df = process_dataframe(uploaded_df)
            
            # Store in session state
            st.session_state.uploaded_df = processed_df
            st.session_state.using_uploaded_data = True
            
            # Success message
            st.sidebar.success(f"✅ Successfully loaded {len(processed_df):,} contracts from uploaded file!")
            
            # Show data info
            st.sidebar.info(f"📊 **Current Data:** Uploaded CSV\n\n📋 {len(processed_df):,} contracts\n🏢 {processed_df['Lieferant_Clean'].nunique():,} suppliers")
            
            # Force rerun to update the data selection
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ Upload failed: {str(e)}")
            # Keep using original data
            st.session_state.using_uploaded_data = False
    
    # Reset to original data button
    if st.session_state.using_uploaded_data:
        if st.sidebar.button("🔄 Reset to Original Data", key="reset_data_btn"):
            # Clear all session state related to uploaded data
            st.session_state.using_uploaded_data = False
            st.session_state.uploaded_df = None
            
            # Clear any cached data and filter states
            keys_to_delete = []
            for key in st.session_state.keys():
                if key.startswith(('market_', 'consulting_', 'category_')):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del st.session_state[key]
            
            # Clear any streamlit cache
            st.cache_data.clear()
            
            # Force refresh the page
            st.rerun()
    
    # Data source indicator with additional controls
    if st.session_state.using_uploaded_data:
        st.sidebar.markdown("🔵 **Using uploaded data**")
        
        # Add warning and additional reset option
        st.sidebar.warning("⚠️ You are currently viewing uploaded data. All analyses reflect the uploaded dataset.")
        
        # Alternative reset method with expander
        with st.sidebar.expander("🔄 Data Management"):
            st.write("**Current Status:** Using uploaded CSV file")
            st.write(f"**Contracts:** {len(df):,}")
            st.write(f"**Suppliers:** {df['Lieferant_Clean'].nunique():,}")
            
            if st.button("↩️ Switch Back to Original Data", key="reset_data_expanded"):
                # Clear everything and reset
                keys_to_delete = []
                for key in st.session_state.keys():
                    if key.startswith(('market_', 'consulting_', 'category_')):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del st.session_state[key]
                
                st.session_state.using_uploaded_data = False
                st.session_state.uploaded_df = None
                
                # Clear any streamlit cache
                st.cache_data.clear()
                
                st.rerun()
    else:
        st.sidebar.markdown("🟢 **Using original data**")
        
        # Show original data info
        with st.sidebar.expander("📊 Original Data Info"):
            st.write(f"**Source:** Single subsidiary scraper")
            st.write(f"**Contracts:** {len(original_df):,}")
            st.write(f"**Suppliers:** {original_df['Lieferant_Clean'].nunique():,}")
            st.write(f"**Last Updated:** Based on scraper run")
    
    
    # Display selected page
    if page == "Market Overview":
        create_market_overview(df)  # Always use full dataset for overview
    elif page == "Market Share Analysis":
        create_market_share_analysis(df_base_filtered)
    elif page == "Competitive Intelligence":
        create_consulting_competitive_analysis(df_base_filtered)
    elif page == "Category Analysis":
        create_category_analysis(df_base_filtered)
    elif page == "Timeline Analysis":
        create_timeline_analysis(df_base_filtered)
    elif page == "Company Deep Dive":
        create_company_deep_dive(df_base_filtered)
    
    
    # Compact download section at bottom
    st.sidebar.markdown("---")
    with st.sidebar.expander("💾 Download Data"):
        # Prepare filtered data based on current company filter
        if company_filter == "Consulting Only":
            download_df = df[df['Is_Consulting'] == True]
            download_label = "consulting_contracts"
        elif company_filter == "Non-Consulting Only":
            download_df = df[df['Is_Consulting'] == False]
            download_label = "non_consulting_contracts"
        else:
            download_df = df
            download_label = "all_contracts"
        
        # Convert DataFrame to CSV
        csv_data = download_df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label=f"📥 {download_label.replace('_', ' ').title()}",
            data=csv_data,
            file_name=f"obb_procurement_{download_label}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help=f"Download {len(download_df):,} contracts as CSV file"
        )
        
        # Also provide option to download consulting companies only
        if company_filter != "Consulting Only":
            consulting_df = df[df['Is_Consulting'] == True]
            if not consulting_df.empty:
                consulting_csv = consulting_df.to_csv(index=False)
                st.download_button(
                    label="📥 Consulting Only",
                    data=consulting_csv,
                    file_name=f"obb_procurement_consulting_only_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help=f"Download {len(consulting_df):,} consulting contracts as CSV file"
                )
    
    # Footer with balanced stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("📊 **Dashboard Statistics**")
    consulting_count = len(df[df['Is_Consulting'] == True])
    total_count = len(df)
    st.sidebar.markdown(f"Total contracts: {total_count:,}")
    st.sidebar.markdown(f"Consulting: {consulting_count:,} ({consulting_count/total_count*100:.1f}%)")
    st.sidebar.markdown(f"Non-consulting: {total_count-consulting_count:,}")
    st.sidebar.markdown(f"Total suppliers: {df['Lieferant_Clean'].nunique():,}")

if __name__ == "__main__":
    main()