# Single Subsidiary ÖBB Procurement Scraper

## Overview
This component scrapes procurement data from a single ÖBB subsidiary (Business Competence Center) for proof of concept demonstrations.

## Structure
```
single_subsidiary/
├── scraper/
│   └── basic_scraper.py          # Single subsidiary scraper
├── dashboard/
│   └── procurement_dashboard.py  # Streamlit dashboard
├── data/                         # Generated data files
└── README.md                     # This file
```

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/noahcordero/Downloads/ScraperÖBB
source venv/bin/activate
pip install -r shared/requirements/requirements.txt
```

### 2. Run the Scraper
```bash
cd single_subsidiary/scraper
python basic_scraper.py
```
This will generate `../data/single_subsidiary_data.xlsx` with ~2,100+ contracts.

### 3. Launch the Dashboard
```bash
cd single_subsidiary/dashboard
streamlit run procurement_dashboard.py
```

## Features
- **Scraper**: Extracts all procurement contracts from ÖBB Business Competence Center
- **Dashboard**: McKinsey-styled analytics with consulting competitor focus
- **Data**: Excel format for easy sharing and analysis

## Use Case
Perfect for proof of concept presentations showing:
- Procurement data extraction capabilities
- Competitive intelligence insights
- Professional consulting-focused analytics