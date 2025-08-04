# Multi-Subsidiary ÖBB Procurement Scraper

## Overview
This component scrapes procurement data from all 22 ÖBB subsidiaries for comprehensive market analysis.

## Structure
```
multi_subsidiary/
├── scraper/
│   └── multi_subsidiary_scraper.py  # Multi-subsidiary scraper
├── dashboard/
│   └── procurement_dashboard.py     # Streamlit dashboard
├── data/                            # Generated data files
└── README.md                        # This file
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
cd multi_subsidiary/scraper
python multi_subsidiary_scraper.py
```
This will generate `../data/multi_subsidiary_data.csv` with ~7,600+ contracts.

### 3. Launch the Dashboard
```bash
cd multi_subsidiary/dashboard
streamlit run procurement_dashboard.py
```

## Features
- **Scraper**: Extracts contracts from all 22 ÖBB subsidiaries
- **Dashboard**: Comprehensive analytics with subsidiary breakdowns
- **Data**: CSV format for efficient processing of large datasets
- **Batching**: Handles large datasets with intermediate saves

## Use Case
Full-scale competitive intelligence covering:
- Complete ÖBB procurement landscape
- Cross-subsidiary analysis
- Comprehensive market insights