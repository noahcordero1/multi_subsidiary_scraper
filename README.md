# ÖBB Procurement Intelligence System

## Project Overview
Automated web scraping and business intelligence system for analyzing ÖBB (Austrian Federal Railways) procurement data with focus on consulting competitor analysis.

## Project Structure
```
ScraperÖBB/
├── single_subsidiary/           # Single subsidiary PoC
│   ├── scraper/                # Basic scraper
│   ├── dashboard/              # PoC dashboard
│   ├── data/                   # Generated data
│   └── README.md
├── multi_subsidiary/           # Full-scale system
│   ├── scraper/                # Multi-subsidiary scraper
│   ├── dashboard/              # Comprehensive dashboard
│   ├── data/                   # Generated data
│   └── README.md
├── shared/
│   ├── requirements/           # Dependencies
│   └── utils/                  # Shared utilities
├── venv/                       # Python virtual environment
└── README.md                   # This file
```

## Quick Start

### For Proof of Concept (Tomorrow's Presentation)
```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run single subsidiary scraper
cd single_subsidiary/scraper
python basic_scraper.py

# 3. Launch dashboard
cd ../dashboard
streamlit run procurement_dashboard.py
```

### For Full-Scale Analysis
```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run multi-subsidiary scraper
cd multi_subsidiary/scraper
python multi_subsidiary_scraper.py

# 3. Launch dashboard
cd ../dashboard
streamlit run procurement_dashboard.py
```

## Components

### 🎯 Single Subsidiary (PoC Ready)
- **Data Source**: ÖBB Business Competence Center
- **Volume**: ~2,100+ contracts
- **Output**: Excel format
- **Dashboard**: McKinsey-styled consulting intelligence
- **Use Case**: Proof of concept presentations

### 🚀 Multi-Subsidiary (Full Scale)
- **Data Source**: All 22 ÖBB subsidiaries
- **Volume**: ~7,600+ contracts
- **Output**: CSV format
- **Dashboard**: Comprehensive subsidiary analysis
- **Use Case**: Complete market intelligence

## Features
- ✅ Automated web scraping with pagination
- ✅ Professional McKinsey-styled dashboards
- ✅ Consulting competitor intelligence
- ✅ Interactive data visualization
- ✅ Export capabilities
- ✅ Scalable architecture

## Technology Stack
- **Scraping**: Selenium, BeautifulSoup
- **Data Processing**: Pandas, NumPy
- **Visualization**: Streamlit, Plotly
- **Export**: Excel, CSV formats