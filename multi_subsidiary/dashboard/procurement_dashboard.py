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

# McKinsey Color Palette
MCKINSEY_COLORS = {
    'primary': '#003f5c',      # Dark Blue
    'secondary': '#2f4b7c',    # Medium Blue
    'accent1': '#665191',      # Purple
    'accent2': '#a05195',      # Pink-Purple
    'accent3': '#d45087',      # Pink
    'accent4': '#f95d6a',      # Red-Pink
    'accent5': '#ff7c43',      # Orange
    'accent6': '#ffa600',      # Yellow-Orange
    'light_blue': '#7fb3d3',   # Light Blue
    'gray': '#696969',         # Gray
    'light_gray': '#d3d3d3'    # Light Gray
}

# Define consulting companies for filtering
CONSULTING_COMPANIES = [
    'Accenture', 'Deloitte', 'PwC', 'KPMG', 'McKinsey', 'BCG', 'Bain',
    'Capgemini', 'IBM', 'EY', 'Roland Berger', 'Oliver Wyman', 'A.T. Kearney',
    'Booz Allen Hamilton', 'L.E.K.', 'Strategy&', 'Monitor Deloitte',
    'Nagarro', 'TCS', 'Infosys', 'Wipro', 'Cognizant', 'HCL', 'Tech Mahindra',
    'CGI', 'Atos', 'NTT Data', 'DXC Technology', 'Slalom', 'BearingPoint',
    'Sopra Steria', 'T-Systems', 'Fujitsu', 'NEC', 'Unisys'
]

# Page configuration
st.set_page_config(
    page_title="ÖBB Multi-Subsidiary Procurement Intelligence",
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
    color: {MCKINSEY_COLORS['primary']};
    text-align: center;
    margin-bottom: 2rem;
}}
.metric-card {{
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    border-left: 4px solid {MCKINSEY_COLORS['primary']};
}}
.consulting-highlight {{
    background-color: {MCKINSEY_COLORS['accent4']};
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
}}
.section-header {{
    color: {MCKINSEY_COLORS['primary']};
    border-bottom: 2px solid {MCKINSEY_COLORS['light_blue']};
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and preprocess the procurement data"""
    try:
        df = pd.read_csv('../data/multi_subsidiary_data.csv')
        
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
    except FileNotFoundError:
        st.error("❌ Data file 'single_subsidiary_data.xlsx' not found. Please run the single subsidiary scraper first.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return pd.DataFrame()

def get_mckinsey_colors(n):
    """Get McKinsey color palette for n items"""
    colors = [
        MCKINSEY_COLORS['primary'], MCKINSEY_COLORS['secondary'], MCKINSEY_COLORS['accent1'],
        MCKINSEY_COLORS['accent2'], MCKINSEY_COLORS['accent3'], MCKINSEY_COLORS['accent4'],
        MCKINSEY_COLORS['accent5'], MCKINSEY_COLORS['accent6'], MCKINSEY_COLORS['light_blue'],
        MCKINSEY_COLORS['gray']
    ]
    return colors[:n] if n <= len(colors) else colors * (n // len(colors) + 1)

def create_market_overview(df):
    """Create balanced market overview with consulting insights"""
    if df.empty:
        return
    
    st.markdown('<div class="main-header">📊 ÖBB Procurement Market Intelligence</div>', unsafe_allow_html=True)
    
    # Overall market metrics
    consulting_df = df[df['Is_Consulting'] == True]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_contracts = len(df)
        st.metric("Total Contracts", f"{total_contracts:,}")
    
    with col2:
        total_value = df['Summe_Clean'].sum()
        st.metric("Total Market Value", f"€{total_value:,.0f}")
    
    with col3:
        unique_suppliers = df['Lieferant_Clean'].nunique()
        consulting_share = len(consulting_df) / len(df) * 100 if len(df) > 0 else 0
        st.metric("Total Suppliers", f"{unique_suppliers:,}", 
                 f"{consulting_share:.1f}% consulting")
    
    with col4:
        avg_contract_value = df['Summe_Clean'].mean()
        st.metric("Avg Contract Value", f"€{avg_contract_value:,.0f}")
    
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
                colors.append(MCKINSEY_COLORS['accent4'])  # Consulting companies in red-pink
            else:
                colors.append(MCKINSEY_COLORS['light_gray'])  # Non-consulting in gray
        
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
            title_font_color=MCKINSEY_COLORS['primary']
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
            color_discrete_sequence=[MCKINSEY_COLORS['accent4'], MCKINSEY_COLORS['light_blue']]
        )
        fig_split.update_layout(
            title_font_color=MCKINSEY_COLORS['primary'],
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
            st.metric("Consulting Market Share", f"{consulting_share_value:.1f}%", "by value")

def create_company_analysis(df):
    """Create detailed company analysis section"""
    st.header("🏢 Company Analysis")
    
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
    st.markdown('<div class="section-header">📈 Market Share Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Market share by contract count
        top_companies_count = df['Lieferant_Clean'].value_counts().head(12)
        colors = get_mckinsey_colors(len(top_companies_count))
        
        fig_pie_count = px.pie(
            values=top_companies_count.values,
            names=top_companies_count.index,
            title="Market Share by Contract Count (Top 12)",
            color_discrete_sequence=colors
        )
        fig_pie_count.update_layout(title_font_color=MCKINSEY_COLORS['primary'])
        st.plotly_chart(fig_pie_count, use_container_width=True)
    
    with col2:
        # Market share by value
        top_companies_value = df.groupby('Lieferant_Clean')['Summe_Clean'].sum().sort_values(ascending=False).head(12)
        colors = get_mckinsey_colors(len(top_companies_value))
        
        fig_pie_value = px.pie(
            values=top_companies_value.values,
            names=top_companies_value.index,
            title="Market Share by Value (Top 12)",
            color_discrete_sequence=colors
        )
        fig_pie_value.update_layout(title_font_color=MCKINSEY_COLORS['primary'])
        st.plotly_chart(fig_pie_value, use_container_width=True)
    
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
    st.markdown('<div class="section-header">🏷️ Category Analysis</div>', unsafe_allow_html=True)
    
    # Top categories with McKinsey colors
    col1, col2 = st.columns(2)
    
    with col1:
        category_counts = df['CPV_Category'].value_counts().head(10)
        colors = get_mckinsey_colors(len(category_counts))
        
        fig_cat = px.bar(
            x=category_counts.values,
            y=category_counts.index,
            orientation='h',
            title="Top 10 Categories by Contract Count",
            color_discrete_sequence=colors
        )
        fig_cat.update_layout(
            height=500,
            showlegend=False,
            title_font_color=MCKINSEY_COLORS['primary']
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        category_values = df.groupby('CPV_Category')['Summe_Clean'].sum().sort_values(ascending=False).head(10)
        colors = get_mckinsey_colors(len(category_values))
        
        fig_cat_val = px.bar(
            x=category_values.values,
            y=category_values.index,
            orientation='h',
            title="Top 10 Categories by Value",
            color_discrete_sequence=colors
        )
        fig_cat_val.update_layout(
            height=500,
            showlegend=False,
            title_font_color=MCKINSEY_COLORS['primary']
        )
        st.plotly_chart(fig_cat_val, use_container_width=True)
    
    # Consulting category analysis
    consulting_df = df[df['Is_Consulting'] == True]
    if not consulting_df.empty:
        st.markdown('<div class="section-header">🎯 Consulting Category Breakdown</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            consulting_categories = consulting_df['CPV_Category'].value_counts().head(8)
            colors = get_mckinsey_colors(len(consulting_categories))
            
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
                title_font_color=MCKINSEY_COLORS['primary']
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
                marker_color=MCKINSEY_COLORS['accent4']
            ))
            fig_comparison.add_trace(go.Bar(
                name='Non-Consulting',
                x=comparison_df['Category'],
                y=comparison_df['Non-Consulting'],
                marker_color=MCKINSEY_COLORS['light_blue']
            ))
            
            fig_comparison.update_layout(
                title="Consulting vs Non-Consulting by Category",
                barmode='stack',
                height=400,
                title_font_color=MCKINSEY_COLORS['primary']
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
        def highlight_consulting(row):
            if row['Is_Consulting']:
                return ['background-color: #f95d6a; color: white'] * len(row)
            return [''] * len(row)
        
        styled_df = category_leaders.drop('Is_Consulting', axis=1).style.apply(
            lambda row: highlight_consulting(category_leaders.loc[row.name]), axis=1
        )
        st.dataframe(styled_df, use_container_width=True)
        st.caption("🎯 Consulting companies highlighted in red")



def create_company_deep_dive(df):
    """Create detailed company analysis with McKinsey styling"""
    st.markdown('<div class="section-header">🔬 Company Deep Dive</div>', unsafe_allow_html=True)
    
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
                    line=dict(color=MCKINSEY_COLORS['primary'])
                ),
                secondary_y=False,
            )
            fig_performance.add_trace(
                go.Scatter(
                    x=monthly_performance.index.astype(str), 
                    y=monthly_performance['Value'], 
                    name="Value",
                    line=dict(color=MCKINSEY_COLORS['accent4'])
                ),
                secondary_y=True,
            )
            fig_performance.update_yaxes(title_text="Number of Contracts", secondary_y=False)
            fig_performance.update_yaxes(title_text="Contract Value (€)", secondary_y=True)
            fig_performance.update_layout(
                title=f"{selected_company} - Performance Over Time",
                title_font_color=MCKINSEY_COLORS['primary']
            )
            
            st.plotly_chart(fig_performance, use_container_width=True)
    
    with col2:
        # Company's categories
        company_categories = company_data['CPV_Category'].value_counts().head(8)
        colors = get_mckinsey_colors(len(company_categories))
        
        fig_cat = px.bar(
            x=company_categories.values,
            y=company_categories.index,
            orientation='h',
            title=f"{selected_company} - Top Categories",
            color_discrete_sequence=colors
        )
        fig_cat.update_layout(
            showlegend=False,
            title_font_color=MCKINSEY_COLORS['primary']
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
    st.markdown('<div class="section-header">🎯 Consulting Competitive Landscape</div>', unsafe_allow_html=True)
    
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
        colors = get_mckinsey_colors(len(top_consulting_value))
        
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
            title_font_color=MCKINSEY_COLORS['primary']
        )
        st.plotly_chart(fig_value, use_container_width=True)
    
    with col2:
        # Competition intensity analysis for consulting
        fig_competition = px.scatter(
            consulting_summary.reset_index(),
            x='Avg Competition',
            y='Avg Value (€)',
            size='Contracts',
            hover_name='Lieferant_Clean',
            title="Competition vs. Contract Value",
            color_discrete_sequence=[MCKINSEY_COLORS['accent3']]
        )
        fig_competition.update_layout(
            height=500,
            title_font_color=MCKINSEY_COLORS['primary']
        )
        st.plotly_chart(fig_competition, use_container_width=True)
    
    # Detailed consulting table
    st.subheader("📋 Consulting Firm Performance")
    st.dataframe(consulting_summary, use_container_width=True)

def create_consulting_categories(df):
    """Create consulting category analysis"""
    st.markdown('<div class="section-header">📊 Consulting Service Categories</div>', unsafe_allow_html=True)
    
    consulting_df = df[df['Is_Consulting'] == True]
    
    if consulting_df.empty:
        st.warning("No consulting companies found in the data.")
        return
    
    # Top categories for consulting
    consulting_categories = consulting_df['CPV_Category'].value_counts().head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        colors = get_mckinsey_colors(len(consulting_categories))
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
            title_font_color=MCKINSEY_COLORS['primary']
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        # Category value analysis
        category_values = consulting_df.groupby('CPV_Category')['Summe_Clean'].sum().sort_values(ascending=False).head(10)
        colors = get_mckinsey_colors(len(category_values))
        
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
            title_font_color=MCKINSEY_COLORS['primary']
        )
        st.plotly_chart(fig_cat_val, use_container_width=True)

def create_timeline_analysis(df):
    """Create timeline analysis with consulting overlay"""
    st.markdown('<div class="section-header">📅 Market Timeline Analysis</div>', unsafe_allow_html=True)
    
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
            line=dict(color=MCKINSEY_COLORS['primary'], width=3)
        ))
        fig_contracts.add_trace(go.Scatter(
            x=monthly_combined.index.astype(str),
            y=monthly_combined['Consulting_Contracts'],
            name='Consulting',
            line=dict(color=MCKINSEY_COLORS['accent4'], width=2)
        ))
        fig_contracts.update_layout(
            title="Monthly Contract Trends",
            title_font_color=MCKINSEY_COLORS['primary'],
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
            line=dict(color=MCKINSEY_COLORS['primary'], width=3)
        ))
        fig_values.add_trace(go.Scatter(
            x=monthly_combined.index.astype(str),
            y=monthly_combined['Consulting_Value'],
            name='Consulting',
            line=dict(color=MCKINSEY_COLORS['accent4'], width=2)
        ))
        fig_values.update_layout(
            title="Monthly Value Trends",
            title_font_color=MCKINSEY_COLORS['primary'],
            height=400
        )
        st.plotly_chart(fig_values, use_container_width=True)

def main():
    """Main dashboard function with balanced market and consulting view"""
    # Load data
    df = load_data()
    
    if df.empty:
        st.stop()
    
    # Sidebar navigation - balanced approach
    st.sidebar.title("📊 Market Intelligence")
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
    
    # Data filters
    st.sidebar.header("🔧 Filters")
    
    # Company type filter
    company_filter = st.sidebar.selectbox(
        "Company Focus:",
        ["All Companies", "Consulting Only", "Non-Consulting Only"],
        index=0
    )
    
    # Value range filter
    min_value, max_value = st.sidebar.slider(
        "Contract Value Range (€)",
        min_value=0,
        max_value=int(df['Summe_Clean'].max()),
        value=(0, int(df['Summe_Clean'].max())),
        step=1000
    )
    
    # Apply filters
    df_filtered = df[
        (df['Summe_Clean'] >= min_value) & 
        (df['Summe_Clean'] <= max_value)
    ]
    
    if company_filter == "Consulting Only":
        df_filtered = df_filtered[df_filtered['Is_Consulting'] == True]
    elif company_filter == "Non-Consulting Only":
        df_filtered = df_filtered[df_filtered['Is_Consulting'] == False]
    
    # Display selected page
    if page == "Market Overview":
        create_market_overview(df)  # Always use full dataset for overview
    elif page == "Market Share Analysis":
        create_market_share_analysis(df_filtered)
    elif page == "Competitive Intelligence":
        create_consulting_competitive_analysis(df_filtered)
    elif page == "Category Analysis":
        create_category_analysis(df_filtered)
    elif page == "Timeline Analysis":
        create_timeline_analysis(df_filtered)
    elif page == "Company Deep Dive":
        create_company_deep_dive(df_filtered)
    
    # Footer with balanced stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("📊 **Market Intelligence**")
    consulting_count = len(df[df['Is_Consulting'] == True])
    total_count = len(df)
    st.sidebar.markdown(f"Total contracts: {total_count:,}")
    st.sidebar.markdown(f"Consulting: {consulting_count:,} ({consulting_count/total_count*100:.1f}%)")
    st.sidebar.markdown(f"Non-consulting: {total_count-consulting_count:,}")
    st.sidebar.markdown(f"Total suppliers: {df['Lieferant_Clean'].nunique():,}")

if __name__ == "__main__":
    main()