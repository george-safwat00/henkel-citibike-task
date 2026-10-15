# NYC Citi Bike 2019 Data Analysis & BI Dashboard

## Project Overview
This project delivers an end-to-end data engineering and business intelligence solution for the 2019 NYC Citi Bike dataset (~20.5 million trips). It transforms raw, messy CSV files into actionable strategic insights through a robust, modular Python ETL pipeline, rigorous data profiling, and a corporate-branded Power BI dashboard. 

The solution is built with a focus on scalability, reproducibility, and clean data modeling (Star Schema), adhering to modern Medallion Architecture principles.

---

## Key Highlights
* **Modular ETL Pipeline:** Built with a clean `src/` package structure, featuring idempotent downloads, memory-efficient Polars streaming (`sink_parquet`), and production-grade dual-output logging (Console + JSON).
* **Medallion Architecture:** Clear separation of Bronze (raw ingestion), Silver (cleaning & feature engineering), and Gold (optimized Star Schema Parquet files) layers.
* **Advanced Data Modeling:** Transformed flat data into a normalized Star Schema with role-playing dimensions (handling both Start/End stations and Start/Stop times via inactive relationships).
* **Corporate Branding:** Power BI dashboard fully customized with the official **Henkel** color palette and typography for a professional, enterprise-ready presentation.
* **Comprehensive Analysis:** Answers 6 core business questions using a hybrid approach: heavy computation in Python (Polars/Matplotlib) and interactive time-series/spatial analysis in Power BI (DAX).

---

## Project Folder Architecture

This repository is strictly organized to separate data, code, documentation, and deliverables. Here is where to find everything:

```text
henkel-citibike-task/
│
├── docs/                           #  FINAL DOCUMENTATION
│   ├── Project Summary.docx        # Detailed Word document covering methodology, findings, and architecture.
│   └── Project Summary.pdf         # PDF version (Recommended for viewing to preserve formatting).
│
├── data/                           #  DATA STORAGE (Medallion Architecture)
│   ├── processed/                  #  GOLD LAYER: Clean, Zstd-compressed Parquet files (Fact & Dimension tables).
│   └── raw/                        #  BRONZE LAYER: Downloaded .zip files and extracted monthly .csv files.
│
├── html_export/                    #  NOTEBOOK EXPORTS
│   ├── 01_data_profiling.html      # HTML exports of all notebooks for easy viewing without Jupyter.
│   └── [business_questions].html   
│
├── notebooks/                      #  JUPYTER NOTEBOOKS
│   ├── 01_data_profiling.ipynb     # Exploratory Data Analysis and Data Quality checks.
│   └── business_questions/         # Python-based answers to Q1 (Demographics), Q3 (Frequent Trips), Q6 (Speed).
│
├── powerbi/                        # POWER BI DELIVERABLES
│   ├── CitiBike_Analysis_Report.pbip      # Power BI Project file (optimized for version control).
│   ├── CitiBike_Analysis_Report.pdf       # Exported PDF of the dashboard (Recommended for viewing).
│   └── Henkel_Corporate_Theme.json        # Custom JSON theme file applied to the report.
│
├── scripts/ (or root)              # UTILITY SCRIPTS
│   └── dump_project.py             # Script used to generate the project structure tree for documentation.
│
├── src/                            # CORE PYTHON ETL PIPELINE (Modular Package)
│   ├── extract/                    # Logic for downloading and safely unzipping data.
│   ├── load/                       # Logic for consolidating raw CSVs into a single Bronze Parquet file.
│   ├── transform/                  # Logic for cleaning, feature engineering (Haversine), and building the Star Schema.
│   ├── logger/                     # Custom logging manager (JSON file output + human-readable console).
│   ├── utils/                      # Helper functions (e.g., `haversine.py`) and custom exceptions.
│   └── main.py                     # Main entry point to execute the full pipeline.
│
├── README.md                       # This file.
└── requirements.txt                # Python dependencies.
```
--
## Project Folder Architecture
* **Python Environment**: Ensure you have Python 3.10+ installed.
* **Virtual Environment**: It is highly recommended to use a virtual environment.
``` text
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
```
* **Install Dependencies**:
```text
   pip install -r requirements.txt
```
* **Install the Local Package**: (Ensures src modules are recognized globally within the project)
```text
   pip install -e .
```

## How to Run the Project
1. Execute the ETL Pipeline
To download, extract, and transform the data from scratch, run the main pipeline script from the project root:
```text
python -m src.main
```
**Note**: The pipeline is idempotent. If the raw files or processed Parquet files already exist, it will safely skip those steps.

2. View the Analysis Notebooks
You can run the notebooks interactively: jupyter notebook
Navigate to the notebooks/ directory to explore the Data Profiling and Business Question analyses. Alternatively, open the pre-exported .html files in the html_export/ folder directly in your web browser.

3. View the Power BI Dashboard
Recommended: Open powerbi/CitiBike_Analysis_Report.pdf in any PDF reader to see the final, interactive-like layout and insights.
Interactive: Open powerbi/CitiBike_Analysis_Report.pbix in Power BI Desktop to interact with the slicers, explore the Star Schema data model, and review the DAX measures.

## Final Deliverables Checklist
* **Python Code**: Modular, documented ETL pipeline (src/).
* **Jupyter Notebooks**: .ipynb and exported .html formats for Profiling and Q1, Q3, Q6.
* **Power BI Report**: .pbip, and exported .pdf formats answering Q2, Q4, Q5.
* **Summary Document**: docs/Project Summary.pdf covering methodology, data quality, architecture, and strategic recommendations.



