# 🏦 NeoTrust Bank - Customer Churn Prediction & Retention Revenue Calculator

> **Identifying ₹2.29 Crore in Annual Revenue Risk across 6,001 Neo-Banking Customers**

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Power BI](https://img.shields.io/badge/PowerBI-Dashboard-yellow)
![ML](https://img.shields.io/badge/RandomForest-94%25%20Accuracy-green)
![SQL](https://img.shields.io/badge/SQL-SQLite-lightgrey)

## 📌 Business Problem

Indian neo-banks like Open Financial Technologies and Jupiter Money posted 
combined net losses exceeding ₹1,300 Crore in FY24-25, despite strong 
revenue growth. The core issue is not customer acquisition — it is retention.

Customer Acquisition Cost (CAC) for Indian neo-banks averages ₹1,200 per 
customer. When a customer churns, that investment is lost entirely. A 
₹40,000 retention campaign targeting the right customers can protect 
₹20,00,000+ in annual revenue.

**This project answers one business question:**
> *"Which customers are about to leave and how much does it cost us if they do?"*

## 🏗️ Project Architecture

```
Raw Data (3 CSV Files)
        ↓
ingestion_db.py → SQLite Database (churn.db)
        ↓
etl_pipeline.py → Cleaned Master Table (clean_master.csv)
        ↓
02_eda.ipynb → Top 5 Churn Drivers Identified
        ↓
03_ml_model.ipynb → Random Forest Model (94% Accuracy)
        ↓
04_revenue_calculator.ipynb → ₹2.29 Crore Revenue at Risk
        ↓
05_sql_analysis.ipynb → Business SQL Insights
        ↓
Power BI Dashboard → 3-Page Interactive Dashboard
```

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python (pandas, numpy) | Data cleaning & ETL |
| SQLite + SQLAlchemy | Database ingestion & storage |
| scikit-learn | ML model training |
| matplotlib, seaborn | EDA visualizations |
| SQL | Business insight queries |
| Power BI | Interactive dashboard |
| GitHub | Version control & portfolio |

## 📂 Dataset

| File | Rows | Description |
|---|---|---|
| customer_master.csv | 6,180 | Customer demographics, KYC status, acquisition channel |
| transaction_log.csv | 1,49,596 | Raw transaction records per customer |
| support_tickets.csv | 7,167 | Customer support and complaint history |

**Data was intentionally designed with real-world messiness:**
- Inconsistent date formats across source systems
- Currency values stored as strings (₹38,589 format)
- Duplicate customer IDs from re-KYC migrations
- Missing KYC and employment data from incomplete onboarding
- Mismatched customer IDs across files (data entry typos)

**Churn Definition:**
> A customer with zero transactions in the 90 days prior to 30 September 2024
> is classified as churned. This mirrors how real BFSI analysts define 
> attrition from behavioral signals rather than explicit account closure data.

## 🔍 Key Findings

### Top 5 Churn Drivers

| Rank | Driver | Insight |
|---|---|---|
| 1 | Transaction Recency | 67% of model's predictive power — inactive customers almost certain to churn |
| 2 | Credit Saturation | Customers with 5+ lending relationships churn at 48% vs 35% for low-saturation customers |
| 3 | KYC Incompleteness | Unknown/Incomplete KYC customers churn at 41% vs 37% for verified customers |
| 4 | Acquisition Channel | Paid Social customers churn at 40% — highest among all channels |
| 5 | Support Complaints | Churned customers raise 33% more high risk tickets before leaving |

### Model Performance

| Model | Accuracy | ROC-AUC |
|---|---|---|
| Logistic Regression | 81% | 0.8984 |
| Random Forest | 94% | 0.9868 |

## 💰 Revenue Impact

| Metric | Value |
|---|---|
| Total Customers Analysed | 6,001 |
| Churned Customers Identified | 2,251 |
| Churn Rate | 37.51% |
| Total Revenue at Risk | ₹2,29,60,200 |
| High Risk Customers (70%+ probability) | 2,228 |
| Retention Campaign Cost (Top 200) | ₹40,000 |
| Net Revenue Protected | ₹20,00,000 |
| ROI on

## 💡 Business Recommendations

1. **Immediate Action — Transaction Monitoring**
   Flag any customer with zero transactions for 30+ days for retention 
   outreach. This single rule captures the majority of churn risk.

2. **Credit Saturation Alert**
   Customers with 5+ active lending relationships should trigger an 
   automatic financial health check offer. These customers are 
   financially overextended and at 48% churn risk.

3. **KYC Completion Campaign**
   1,174 customers have incomplete or unknown KYC status and churn at 
   41%. A guided KYC completion nudge could reduce churn in this 
   segment by 15-20%.

4. **Acquisition Channel Reallocation**
   Paid Social drives the highest churn at 40%. Reallocating 20% of 
   Paid Social budget to Referral programs would improve customer 
   quality and reduce long term churn.

5. **High Risk Ticket Monitoring**
   Account Closure Requests and Hidden Charge complaints are the 
   strongest pre-churn signals. A real-time alert

## 📁 Project Structure

```
Customer_churn_prediction_Neo-Banking/
│
├── raw_data/
│   ├── customer_master.csv
│   ├── transaction_log.csv
│   └── support_tickets.csv
│
├── reference/
│   └── _internal_ground_truth_DO_NOT_USE_AS_FEATURE.csv
│
├── charts/
│   ├── churn_by_channel.png
│   ├── churn_by_kyc.png
│   ├── churn_by_lending.png
│   ├── churn_by_employment.png
│   ├── churn_by_transactions.png
│   ├── churn_by_tickets.png
│   ├── feature_importance.png
│   └── revenue_impact.png
│
├── logs/
│   ├── ingestion_db.log
│   └── etl_pipeline.log
│
├── ingestion_db.py
├── etl_pipeline.py
├── generate_raw_data.py
├── 02_eda.ipynb
├── 03_ml_model.ipynb
├── 04_revenue_calculator.ipynb
├── 05_sql_analysis.ipynb
├── clean_master.csv
├── churn.db
├── NeoTrust_Bank_Customer_Churn_Prediction_Dashboard.pbix
└── README.md
```

## ▶️ How to Run

### Prerequisites
- Python 3.x
- Power BI Desktop
- Jupyter Notebook or VS Code

### Installation
```bash
pip install pandas numpy matplotlib seaborn scikit-learn sqlalchemy
```

### Steps

**Step 1 — Generate Raw Data**
```bash
python generate_raw_data.py
```

**Step 2 — Ingest into Database**
```bash
python ingestion_db.py
```

**Step 3 — Run ETL Pipeline**
```bash
python etl_pipeline.py
```

**Step 4 — Run Notebooks in Order**
```
02_eda.ipynb                → Exploratory Data Analysis
03_ml_model.ipynb           → Churn Prediction Model
04_revenue_calculator.ipynb → Revenue Impact Analysis
05_sql_analysis.ipynb       → SQL Business Insights
```

**Step 5 — Open Power BI Dashboard**
```
NeoTrust_Bank_Customer_Churn_Prediction_Dashboard.pbix
```

## 👤 Author

**Mohd Hussain Khan**

Data Scientist | 🏆 Rank 1 in Academia

### Connect with me
📧 [mohdhussainkhan.ds@gmail.com]
💼 [www.linkedin.com/in/mohdhussain-khan]
🐙 [https://github.com/insightzbyhussain]

---

*This project was built to demonstrate end-to-end data analytics capabilities 
targeting BFSI domain roles at leading financial institutions.*
