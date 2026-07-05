pip install pandas numpy faker

"""
Raw Data Generator — NeoTrust Bank Customer Churn Project
============================================================
Simulates 3 separate, UNJOINED raw data exports as they would realistically
come out of a neo-bank's systems:
    1. customer_master.csv   -> from CRM / onboarding system
    2. transaction_log.csv   -> from core banking transaction engine
    3. support_tickets.csv   -> from customer support / CRM ticketing tool

Deliberate realism flaws are injected (NOT random noise — each flaw mirrors
something that actually happens in real BFSI data exports):
    - Duplicate customer_id rows (re-KYC / system migration duplicates)
    - Inconsistent date formats across files (different source systems)
    - Missing values in KYC fields (incomplete onboarding)
    - Inconsistent casing / whitespace in categorical fields
    - Currency values stored as strings with ₹ symbols and commas in some rows
    - A few customer_id mismatches between files (data entry typos)
    - Outlier transaction amounts (fat-finger entries)
    - The "credit saturation" signal (active_lending_relationships) is
      correlated with churn, mirroring the RBI Financial Stability Report
      finding that borrowers with 5+ lender relationships show higher
      attrition/impairment.

Run: python generate_raw_data.py
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

N_CUSTOMERS = 6000
import os
OUT_DIR = "raw_data"
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# 1. CUSTOMER MASTER (from CRM / onboarding)
# ----------------------------------------------------------------------

cities = ["Mumbai", "Bandra West", "BKC", "Pune", "Bengaluru", "Delhi",
          "Hyderabad", "Chennai", "Ahmedabad", "Kolkata", "mumbai", "PUNE"]
acquisition_channels = ["Referral", "Paid Social", "Google Ads", "Organic",
                         "Affiliate", "In-App Promo", "referral", "PAID SOCIAL"]
products = ["Savings Account", "Salary Account", "Personal Loan",
            "Credit Card", "BNPL", "Fixed Deposit"]
employment_types = ["Salaried", "Self-Employed", "Student", "Gig Worker", np.nan]

customer_ids = [f"CUST{100000+i}" for i in range(N_CUSTOMERS)]

def random_signup_date():
    start = datetime(2022, 1, 1)
    end = datetime(2025, 12, 31)
    delta = end - start
    rand_days = random.randint(0, delta.days)
    d = start + timedelta(days=rand_days)
    # inconsistent date formats across rows (simulating different export batches)
    fmt = random.choice(["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%m/%d/%Y"])
    return d.strftime(fmt)

rows = []
for cid in customer_ids:
    age = int(np.clip(np.random.normal(31, 8), 18, 65))
    tenure_days = random.randint(15, 1400)
    channel = random.choice(acquisition_channels)
    city = random.choice(cities)
    employment = random.choice(employment_types)

    # active lending relationships -> credit saturation signal (RBI FSR insight)
    # most customers have 0-2, a tail has 5+ (these will show higher churn)
    lending_rel = np.random.choice(
        [0, 1, 2, 3, 4, 5, 6, 7],
        p=[0.30, 0.25, 0.18, 0.12, 0.07, 0.04, 0.02, 0.02]
    )

    # KYC completeness — some missing (realistic onboarding drop-off)
    kyc_status = random.choices(
        ["Verified", "Pending", "Incomplete", np.nan],
        weights=[0.78, 0.10, 0.08, 0.04]
    )[0]

    # monthly income stored messily — some as plain numbers, some as strings w/ symbols
    income_val = int(np.clip(np.random.normal(55000, 25000), 12000, 300000))
    if random.random() < 0.25:
        income_str = f"₹{income_val:,}"
    elif random.random() < 0.10:
        income_str = ""  # missing
    else:
        income_str = str(income_val)

    primary_product = random.choice(products)

    rows.append({
        "customer_id": cid,
        "signup_date": random_signup_date(),
        "age": age if random.random() > 0.02 else np.nan,
        "city": city,
        "acquisition_channel": channel,
        "employment_type": employment,
        "monthly_income": income_str,
        "active_lending_relationships": lending_rel,
        "kyc_status": kyc_status,
        "primary_product": primary_product,
        "account_status": None,  # filled in after churn logic below
    })

cust_df = pd.DataFrame(rows)

# Inject duplicate customer rows (re-KYC / migration duplicates) - ~3%
dupe_sample = cust_df.sample(frac=0.03, random_state=1).copy()
cust_df = pd.concat([cust_df, dupe_sample], ignore_index=True)

# Inject a few whitespace/casing issues into customer_id (data entry errors) - ~1%
typo_idx = cust_df.sample(frac=0.01, random_state=2).index
cust_df.loc[typo_idx, "customer_id"] = cust_df.loc[typo_idx, "customer_id"].apply(
    lambda x: f" {x.lower()} " if random.random() > 0.5 else x + "_old"
)

# ----------------------------------------------------------------------
# 2. CHURN GROUND TRUTH (latent, used to drive transaction/support behavior)
# ----------------------------------------------------------------------
# Higher churn probability if: short tenure, high lending_rel (saturation),
# Incomplete/missing KYC, acquired via Paid Social (low quality leads per
# our research), low engagement (will reflect in transaction_log).

base_cust = cust_df.drop_duplicates(subset="customer_id").copy()
base_cust["customer_id_clean"] = base_cust["customer_id"].astype(str).str.strip().str.replace("_old", "", regex=False).str.upper()

def churn_prob(row):
    p = 0.12
    if row["active_lending_relationships"] >= 5:
        p += 0.30  # credit saturation -> high attrition (RBI FSR finding)
    elif row["active_lending_relationships"] >= 3:
        p += 0.12
    if row["kyc_status"] in ["Incomplete", "Pending"] or pd.isna(row["kyc_status"]):
        p += 0.15
    if row["acquisition_channel"] in ["Paid Social", "paid social", "PAID SOCIAL"]:
        p += 0.10
    if row["employment_type"] in ["Student", "Gig Worker"] or pd.isna(row["employment_type"]):
        p += 0.08
    return min(p, 0.85)

base_cust["churn_probability_latent"] = base_cust.apply(churn_prob, axis=1)
base_cust["will_churn"] = base_cust["churn_probability_latent"].apply(
    lambda p: 1 if random.random() < p else 0
)

churn_map = dict(zip(base_cust["customer_id_clean"], base_cust["will_churn"]))

# ----------------------------------------------------------------------
# 3. TRANSACTION LOG (from core banking engine) — separate raw file
# ----------------------------------------------------------------------
txn_rows = []
txn_id_counter = 500000

for _, c in base_cust.iterrows():
    cid_clean = c["customer_id_clean"]
    will_churn = c["will_churn"]
    n_txns = np.random.randint(2, 60)
    if will_churn:
        n_txns = max(1, int(n_txns * random.uniform(0.2, 0.5)))  # churners transact less

    for _ in range(n_txns):
        txn_id_counter += 1
        amt = round(np.clip(np.random.exponential(2500), 50, 150000), 2)
        # outlier fat-finger entries (~0.5%)
        if random.random() < 0.005:
            amt = amt * 100

        txn_type = random.choice(["UPI", "NEFT", "Card Swipe", "BNPL Repayment",
                                   "ATM Withdrawal", "upi", "Card swipe"])

        # inconsistent date format again, sometimes with timestamp
        d = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 700))
        fmt = random.choice(["%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"])
        txn_date = d.strftime(fmt)

        # occasionally store amount as string with commas/currency symbol
        amt_val = amt
        if random.random() < 0.15:
            amt_val = f"Rs. {amt:,.2f}"

        # inject a few mismatched customer_ids (typos from source system) ~0.5%
        out_cid = cid_clean
        if random.random() < 0.005:
            out_cid = cid_clean.replace("CUST", "CSUT")

        txn_rows.append({
            "transaction_id": f"TXN{txn_id_counter}",
            "customer_id": out_cid,
            "transaction_date": txn_date,
            "transaction_type": txn_type,
            "amount": amt_val,
        })

txn_df = pd.DataFrame(txn_rows)

# ----------------------------------------------------------------------
# 4. SUPPORT TICKETS (from CRM ticketing tool) — separate raw file
# ----------------------------------------------------------------------
ticket_rows = []
ticket_id_counter = 9000

issue_types = ["App Login Issue", "Failed Transaction", "KYC Query",
               "Card Block Request", "Loan Inquiry", "Complaint - Hidden Charges",
               "Complaint - Poor Service", "Account Closure Request",
               "app login issue", "Failed transaction "]

for _, c in base_cust.iterrows():
    cid_clean = c["customer_id_clean"]
    will_churn = c["will_churn"]

    # churners raise more complaints/closure requests before leaving
    n_tickets = np.random.poisson(0.8 if not will_churn else 2.3)

    for _ in range(n_tickets):
        ticket_id_counter += 1
        issue = random.choice(issue_types)
        if will_churn and random.random() < 0.35:
            issue = random.choice(["Account Closure Request",
                                    "Complaint - Hidden Charges",
                                    "Complaint - Poor Service"])

        d = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 700))
        fmt = random.choice(["%Y-%m-%d", "%d-%m-%Y", "%d %b %Y"])
        ticket_date = d.strftime(fmt)

        resolved = random.choices(["Resolved", "Unresolved", "Pending", None],
                                   weights=[0.65, 0.15, 0.12, 0.08])[0]

        ticket_rows.append({
            "ticket_id": f"TKT{ticket_id_counter}",
            "customer_id": cid_clean if random.random() > 0.003 else cid_clean + " ",
            "ticket_date": ticket_date,
            "issue_type": issue,
            "resolution_status": resolved,
        })

ticket_df = pd.DataFrame(ticket_rows)

# ----------------------------------------------------------------------
# Save raw files — note: account_status / churn label is INTENTIONALLY
# NOT included directly in customer_master. It will be derived during
# the EDA/labeling phase from behavioral signals, just like a real
# BFSI analyst would have to define "churn" themselves.
# ----------------------------------------------------------------------
cust_df_out = cust_df.drop(columns=["account_status"])
cust_df_out.to_csv(f"{OUT_DIR}/customer_master.csv", index=False)
txn_df.to_csv(f"{OUT_DIR}/transaction_log.csv", index=False)
ticket_df.to_csv(f"{OUT_DIR}/support_tickets.csv", index=False)

# Save the latent ground truth SEPARATELY (for your own validation later,
# NOT to be used as a feature/cheat — treat it as "if this were real,
# we wouldn't have this; we'll derive churn from inactivity instead")
base_cust[["customer_id_clean", "will_churn", "churn_probability_latent"]].to_csv(
    f"{OUT_DIR}/_internal_ground_truth_DO_NOT_USE_AS_FEATURE.csv", index=False
)

print("Raw files generated:")
print(f"  customer_master.csv   -> {len(cust_df_out):,} rows")
print(f"  transaction_log.csv   -> {len(txn_df):,} rows")
print(f"  support_tickets.csv   -> {len(ticket_df):,} rows")
print(f"  (internal ground truth saved separately for validation)")