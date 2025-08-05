# ÖBB Procurement Intelligence Dashboard

A comprehensive Streamlit dashboard for analyzing ÖBB (Austrian Federal Railways) procurement data with specialized focus on consulting company competitive intelligence.

## 🚀 Live Dashboard

Deploy this dashboard on Streamlit Cloud using the main file:
```
single_subsidiary/dashboard/procurement_dashboard.py
```

## 📊 Features

- **Executive Summary**: Key market metrics with professional KPI cards
- **Market Overview**: Comprehensive market analysis with consulting highlights
- **Market Share Analysis**: Contract count and value-based market share visualization
- **Competitive Intelligence**: Consulting firm positioning and competitive landscape
- **Category Analysis**: CPV category breakdown with consulting insights
- **Timeline Analysis**: Market trends over time
- **Company Deep Dive**: Detailed individual company analysis

## 🔧 Key Capabilities

- **Data Upload**: Upload custom CSV files with same format
- **Interactive Filtering**: Filter by company type (All/Consulting/Non-Consulting)
- **Value Range Filtering**: Analyze specific contract value ranges
- **Data Export**: Download filtered results as CSV
- **Real-time Analysis**: Dynamic charts and metrics

## 📁 File Structure

```
├── single_subsidiary/
│   ├── dashboard/
│   │   ├── procurement_dashboard.py  # Main Streamlit app
│   │   ├── horvath-partners.png      # Logo image
│   │   └── horvath-partners.jpg      # Logo image
│   └── data/
│       └── single_subsidiary_data.csv  # Sample data
├── requirements.txt                  # Python dependencies
└── README.md                        # This file
```

## 🛠️ Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/noahcordero1/obb-procurement-dashboard.git
   cd obb-procurement-dashboard
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard**:
   ```bash
   streamlit run single_subsidiary/dashboard/procurement_dashboard.py
   ```

## 📈 Data Format

The dashboard expects CSV files with these columns:
- `Bezeichnung`: Contract description
- `Lieferant`: Supplier name
- `Kategorie (CPV Hauptteil)`: CPV category
- `Bieter`: Number of bidders
- `Summe`: Contract value
- `Aktualisiert`: Last updated date (DD.MM.YYYY format)

## 🏢 Consulting Companies

The dashboard automatically identifies consulting companies including:
- Big 4: Deloitte, PwC, KPMG, EY
- Strategy firms: McKinsey, BCG, Bain, Roland Berger
- Tech consultancies: Accenture, IBM, Capgemini
- And many more...

## 🎨 Design Features

- Professional McKinsey-style color palette
- Executive summary with gradient KPI cards
- Responsive layout with collapsible sidebar sections
- Interactive charts with custom color schemes
- Clean, business-focused presentation

## 🚀 Deployment on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select this repository
4. Set main file path: `single_subsidiary/dashboard/procurement_dashboard.py`
5. Deploy!

## 📧 Contact

For questions or support regarding this dashboard, please refer to the repository issues section.