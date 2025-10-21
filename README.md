# ÖBB Procurement Intelligence System

## Project Overview
Automated web scraping and business intelligence system for analyzing ÖBB (Austrian Federal Railways) procurement data across 22 subsidiaries with specialized focus on consulting competitor analysis. The system features incremental scraping capabilities with intelligent tracking and a comprehensive Streamlit dashboard branded with Horvath & Partners styling.

## Project Structure
```
ScraperÖBB/
├── multi_subsidiary/           # Production system
│   ├── scraper/                # Web scraping modules
│   │   ├── final_multi_subsidiary_scraper.py       # Full baseline scraper
│   │   └── incremental_multi_subsidiary_scraper.py # Incremental update scraper
│   ├── dashboard/              # Streamlit analytics dashboard
│   │   ├── procurement_dashboard.py                # Main dashboard application
│   │   ├── horvath-partners.jpg                    # Logo image (JPEG)
│   │   └── horvath-partners.png                    # Logo image (PNG)
│   ├── data/                   # Generated data files
│   │   ├── *_data.csv          # 22 subsidiary CSV files
│   │   └── scraper_tracking.json # Incremental scraping state
│   └── README.md               # Multi-subsidiary documentation
├── venv/                       # Python virtual environment
├── requirements.txt            # Python dependencies
├── STREAMLIT_README.md         # Dashboard deployment guide
└── README.md                   # This file
```

## Quick Start

### 1. Initial Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Run the Scraper

#### Full Baseline Scrape (First Time or Refresh)
Scrapes all data from scratch for all 22 subsidiaries:
```bash
cd multi_subsidiary/scraper
python final_multi_subsidiary_scraper.py
```

#### Incremental Update Scrape (Regular Updates)
Only scrapes new pages since last run using intelligent tracking:
```bash
cd multi_subsidiary/scraper
python incremental_multi_subsidiary_scraper.py --mode incremental
```

Force full refresh with incremental scraper:
```bash
python incremental_multi_subsidiary_scraper.py --mode full
```

### 3. Launch the Dashboard
```bash
cd multi_subsidiary/dashboard
streamlit run procurement_dashboard.py
```

The dashboard will be available at `http://localhost:8501`

## System Components

### 🔄 Scrapers

#### Final Multi-Subsidiary Scraper (`final_multi_subsidiary_scraper.py`)
- **Purpose**: Baseline data collection from all 22 ÖBB subsidiaries
- **Features**:
  - Complete data extraction from all pages
  - Robust pagination handling with empty page detection
  - Batch writing (1000 rows) for memory efficiency
  - Individual CSV files per subsidiary with subsidiary metadata
  - Comprehensive logging and error handling
- **Output**: Individual CSV files for each subsidiary in `multi_subsidiary/data/`
- **Use Case**: Initial data collection or complete refresh

#### Incremental Multi-Subsidiary Scraper (`incremental_multi_subsidiary_scraper.py`)
- **Purpose**: Efficient updates by scraping only new data
- **Features**:
  - Page-level tracking via `scraper_tracking.json`
  - Resumes from last scraped page per subsidiary
  - Appends new data to existing CSV files
  - Two modes: `incremental` (default) and `full`
  - Automatic detection of first-time subsidiaries
  - Comprehensive metadata tracking (last scrape date, records added)
- **Output**: Updates existing CSV files and tracking metadata
- **Use Case**: Regular updates without re-scraping historical data

### 📊 Ausschreibungs-Dashboard (`procurement_dashboard.py`)

A comprehensive Streamlit application with Horvath & Partners branding featuring:

#### Pages:
1. **Dashboard Info & Disclaimer**: Project information, data sources, methodology
2. **Market Overview**: Aggregate metrics across selected subsidiaries with consulting highlights
3. **Market Share Analysis**: Contract count and value distribution
4. **Competitive Intelligence**: Consulting-specific competitive landscape
5. **Category Analysis**: CPV category breakdown with consulting insights
6. **Timeline Analysis**: Temporal trends with consulting overlay
7. **Company Deep Dive**: Detailed individual company performance

#### Key Features:
- **Multi-subsidiary filtering**: Select specific subsidiaries for analysis
- **Consulting intelligence**: Automatic identification of 37+ consulting firms
- **Interactive visualizations**: Plotly charts with McKinsey color palette
- **Advanced filtering**: Contract value ranges, company type (consulting/non-consulting)
- **Responsive design**: Professional layout with Horvath & Partners logo on all pages
- **Data integrity**: Robust file loading with fallback paths for deployment

### 📂 Data Files

#### Subsidiary Data Files (`*_data.csv`)
22 CSV files, one per subsidiary, with standardized schema:
- `subsidiary_name`: Name of the ÖBB subsidiary
- `subsidiary_id`: Unique identifier for the subsidiary
- `Bezeichnung`: Contract description
- `Lieferant`: Supplier/vendor name
- `Kategorie (CPV Hauptteil)`: CPV category classification
- `Bieter`: Number of bidders
- `Summe`: Contract value (formatted string)
- `Aktualisiert`: Last update date (DD.MM.YYYY)

#### Tracking File (`scraper_tracking.json`)
Maintains incremental scraping state:
- `tracking_info`: Scraper version and last update timestamp
- `subsidiaries`: Per-subsidiary tracking with:
  - `last_scraped_page`: Last successfully scraped page number
  - `last_scrape_date`: ISO timestamp of last scrape
  - `total_new_records_this_run`: Records added in most recent run

## Data Coverage

### 22 ÖBB Subsidiaries
The system covers all major ÖBB entities:
- ÖBB-Business Competence Center (3 variants)
- ÖBB-Infrastruktur AG (4 variants)
- ÖBB-Personenverkehr AG (5 variants)
- ÖBB-Technische Services Gesellschaft (2 variants)
- ÖBB-Immobilienmanagement (2 variants)
- ÖBB Holding AG (2 variants)
- ÖBB-Produktion
- ÖBB-Postbus
- ÖBB-Werbung
- ÖBB Rail Tours Austria

**Total procurement records**: ~15,621 (as of last incremental scrape)

## Technology Stack

### Scraping
- **Selenium**: Dynamic web page automation with Chrome WebDriver
- **BeautifulSoup**: HTML parsing and data extraction
- **webdriver-manager**: Automatic ChromeDriver management

### Data Processing
- **Pandas**: Data manipulation and CSV operations
- **NumPy**: Numerical operations
- **JSON**: Tracking data persistence

### Visualization & Dashboard
- **Streamlit**: Interactive web application framework
- **Plotly**: Dynamic, interactive charts and visualizations
- **McKinsey Color Palette**: Professional business intelligence styling

### Development
- **Python 3.12**: Core language
- **Virtual Environment**: Dependency isolation
- **Git**: Version control

## Consulting Company Intelligence

The dashboard automatically identifies and tracks 37+ consulting companies:
- **Strategy Consulting**: McKinsey, BCG, Bain, Roland Berger, Oliver Wyman, A.T. Kearney, L.E.K., Strategy&
- **Big 4**: Deloitte, PwC, KPMG, EY
- **Technology Consulting**: Accenture, Capgemini, IBM, Nagarro, TCS, Infosys, Wipro, Cognizant, HCL, Tech Mahindra
- **IT Services**: CGI, Atos, NTT Data, DXC Technology, Slalom, Sopra Steria, T-Systems, Fujitsu, NEC, Unisys
- **Specialized**: Horvath & Partners, BearingPoint

## Features

### Scraping System
- ✅ Intelligent pagination with automatic empty page detection
- ✅ Incremental updates to avoid re-scraping historical data
- ✅ Page-level tracking per subsidiary
- ✅ Robust error handling and recovery
- ✅ Batch writing for memory efficiency
- ✅ Comprehensive logging with timestamps
- ✅ Headless browser operation for production

### Dashboard
- ✅ Multi-subsidiary selection and filtering
- ✅ Consulting vs. non-consulting segmentation
- ✅ Contract value range filtering with presets
- ✅ Interactive Plotly visualizations
- ✅ McKinsey-styled professional design
- ✅ Horvath & Partners branding
- ✅ Real-time metric calculations
- ✅ Export and data download capabilities
- ✅ Responsive layout for various screen sizes
- ✅ Deployment-ready for Streamlit Cloud

## Deployment

### Local Development
See "Quick Start" section above.

### Streamlit Cloud Deployment
1. Push repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repository
4. Set main file path: `multi_subsidiary/dashboard/procurement_dashboard.py`
5. Configure secrets if needed
6. Deploy

See `STREAMLIT_README.md` for detailed deployment instructions.

## Maintenance

### Regular Updates
Run incremental scraper weekly or as needed:
```bash
cd multi_subsidiary/scraper
python incremental_multi_subsidiary_scraper.py
```

### Full Refresh
For complete data refresh or if tracking is corrupted:
```bash
python incremental_multi_subsidiary_scraper.py --mode full
```

### Tracking Reset
To reset incremental tracking and start fresh:
```bash
rm ../data/scraper_tracking.json
python incremental_multi_subsidiary_scraper.py
```

## Data Source
All data is sourced from **OffeneVergaben.at**, Austria's official public procurement transparency platform, ensuring compliance with Austrian procurement transparency regulations.

## Project Evolution
- **Baseline Implementation**: `final_multi_subsidiary_scraper.py` - Complete data extraction
- **Incremental Enhancement**: `incremental_multi_subsidiary_scraper.py` - Efficient updates
- **Dashboard Refinement**: Enhanced with Horvath & Partners branding, multi-subsidiary filtering, and comprehensive consulting intelligence